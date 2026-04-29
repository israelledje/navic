from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from devices.models import Device
from .models import GPSPosition, Trip, Stop, Geofence, GeofenceEvent, Report
from .serializers import (
    GPSPositionSerializer, TripSerializer, TripListSerializer,
    StopSerializer, GeofenceSerializer, GeofenceEventSerializer,
    ReportSerializer
)
from alerts.tasks import process_position_for_alerts

logger = logging.getLogger('tracking')


@api_view(['POST'])
@permission_classes([AllowAny])
def ingest_gps_data(request):
    """
    Endpoint pour recevoir les données GPS du service d'ingestion Go
    """
    
    # Validation de l'API Key pour la sécurité
    api_key = request.headers.get('X-API-Key')
    expected_key = settings.GPS_INGESTION_SERVICE.get('API_KEY')
    
    if api_key != expected_key:
        logger.warning(f"Tentative d'ingestion avec une API Key invalide de {request.META.get('REMOTE_ADDR')}")
        return Response(
            {'error': 'Non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        data = request.data
        
        # Validation des données essentielles
        imei = data.get('imei')
        if not imei:
            return Response(
                {'error': 'IMEI manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le device
        try:
            device = Device.objects.select_related('owner').get(imei=imei)
        except Device.DoesNotExist:
            logger.warning(f"Device avec IMEI {imei} non trouvé")
            return Response(
                {'error': f'Device avec IMEI {imei} non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que le device est actif
        if device.status != 'active':
            logger.warning(f"Device {device.name} n'est pas actif (status: {device.status})")
            return Response(
                {'error': 'Device non actif'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer la position GPS
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = timezone.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = timezone.now()
        else:
            timestamp = timezone.now()
        
        # 1. Mise à jour de l'état temps réel dans Redis
        last_pos_data = {
            'device_id': device.id,
            'imei': imei,
            'latitude': data.get('latitude', 0.0),
            'longitude': data.get('longitude', 0.0),
            'altitude': data.get('altitude'),
            'speed': data.get('speed', 0.0),
            'heading': data.get('heading'),
            'satellites': data.get('satellites'),
            'battery_level': data.get('battery'),
            'signal_strength': data.get('signal'),
            'ignition': data.get('other_data', {}).get('ignition'),
            'external_power': data.get('other_data', {}).get('external_power'),
            'odometer': data.get('other_data', {}).get('odometer'),
            'fuel_level': data.get('other_data', {}).get('fuel_level'),
            'io_data': data.get('other_data', {}),
            'timestamp': timestamp.isoformat(),
            'protocol': data.get('protocol'),
            'raw_data': data.get('raw_data'),
        }

        # Mettre à jour le cache temps réel
        cache.set(f"device_last_pos:{device.id}", last_pos_data, 86400)
        cache.set(f"device_online:{device.id}", True, 86400)
        
        # 2. Ajout au buffer pour insertion par lot (Batch Insert)
        # On utilise une liste Redis pour stocker les positions en attente
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        import json
        redis_conn.lpush("gps_position_buffer", json.dumps(last_pos_data))

        # 3. Mise à jour légère du Device en DB (si nécessaire)
        update_fields = []
        if not device.is_online:
            device.is_online = True
            update_fields.append('is_online')
        
        # On met à jour last_connection en DB moins souvent pour soulager PostgreSQL
        # (ex: toutes les minutes ou si changement de statut)
        last_db_update = cache.get(f"device_db_heartbeat:{device.id}")
        if not last_db_update or timezone.now().timestamp() - float(last_db_update) > 60:
            device.last_connection = timezone.now()
            device.last_position = last_pos_data
            update_fields.append('last_connection')
            update_fields.append('last_position')
            cache.set(f"device_db_heartbeat:{device.id}", timezone.now().timestamp(), 70)

        if update_fields:
            device.save(update_fields=update_fields)
        
        # 4. Gestion des trajets (Optimisée avec Redis)
        update_trip_for_position(device, last_pos_data)
        
        # 5. Diffusion temps réel (WebSocket)
        broadcast_position_update(device, last_pos_data)
        
        # 6. Alertes (Note: Comme la position n'est pas encore en DB, 
        # on passe l'objet de données au lieu de l'ID)
        # process_position_for_alerts(last_pos_data) 
        
        logger.debug(f"Position bufférisée pour {device.name}")
        
        return Response(
            {
                'success': True,
                'message': 'Données mise en attente pour insertion',
            },
            status=status.HTTP_202_ACCEPTED
        )
        
        # Diffuser la position en temps réel via WebSocket
        broadcast_position_update(device, position)
        
        # Traiter les alertes de manière asynchrone
        # Dans un vrai système, utilisez Celery ou Django Q
        process_position_for_alerts(position.id)
        
        logger.info(f"Position GPS enregistrée pour {device.name} (IMEI: {imei})")
        
        return Response(
            {
                'success': True,
                'message': 'Données GPS enregistrées',
                'position_id': position.id
            },
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.error(f"Erreur lors de l'ingestion GPS: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Erreur serveur lors de l\'ingestion'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def update_device_status(request):
    """
    Endpoint pour mettre à jour le statut de connexion d'un device (online/offline)
    Appelé par le service d'ingestion lors d'une déconnexion/reconnexion TCP.
    """
    api_key = request.headers.get('X-API-Key')
    if api_key != settings.GPS_INGESTION_SERVICE.get('API_KEY'):
        return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)

    imei = request.data.get('imei')
    is_online = request.data.get('is_online')

    if not imei:
        return Response({'error': 'IMEI manquant'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        device = Device.objects.get(imei=imei)
        
        # Mettre à jour le cache
        cache.set(f"device_online:{device.id}", bool(is_online), 86400)
        
        if device.is_online != bool(is_online):
            device.is_online = bool(is_online)
            device.save(update_fields=['is_online'])
            # Diffuser le changement de statut en temps réel
            broadcast_device_status(device)
        
        return Response({'status': 'ok', 'is_online': device.is_online})
    except Device.DoesNotExist:
        return Response({'error': 'Device non trouvé'}, status=status.HTTP_404_NOT_FOUND)


def update_trip_for_position(device, data):
    """
    Détecte les trajets, les arrêts et les marches au ralenti (Optimisé Redis).
    """
    try:
        # Essayer de récupérer les paramètres personnalisés du device
        settings = device.settings
        moving_threshold = settings.idling_speed_limit if settings.idling_speed_limit else 3
        stop_threshold_seconds = settings.idling_threshold * 60 if settings.idling_threshold else 300
    except:
        moving_threshold = 3 # km/h
        stop_threshold_seconds = 300 # 5 minutes
    
    speed = float(data.get('speed', 0))
    ignition = data.get('ignition', False)
    
    from django.utils.dateparse import parse_datetime
    timestamp = data.get('timestamp')
    if isinstance(timestamp, str):
        timestamp = parse_datetime(timestamp)
    if not timestamp:
        timestamp = timezone.now()
    
    trip_cache_key = f"active_trip_info:{device.id}"
    stop_cache_key = f"active_stop_info:{device.id}"
    
    trip_info = cache.get(trip_cache_key)
    stop_info = cache.get(stop_cache_key)
    
    if speed > moving_threshold:
        # --- VÉHICULE EN MOUVEMENT ---
        
        # 1. Fermer l'arrêt en cours s'il y en a un
        if stop_info:
            try:
                stop = Stop.objects.get(id=stop_info['id'])
                stop.end_time = timestamp
                start_time = timezone.datetime.fromtimestamp(stop_info['start'], tz=timezone.get_current_timezone())
                stop.duration_seconds = int((timestamp - start_time).total_seconds())
                stop.save(update_fields=['end_time', 'duration_seconds'])
                logger.info(f"Arrêt terminé pour {device.name} (durée: {stop.duration_seconds}s)")
            except Exception as e:
                logger.error(f"Erreur fermeture arrêt: {e}")
            cache.delete(stop_cache_key)
            
        # 2. Gérer le trajet
        if not trip_info:
            # Nouveau trajet
            trip = Trip.objects.create(
                device=device,
                start_time=timestamp,
                end_time=timestamp,
                is_completed=False
            )
            trip_info = {'id': trip.id, 'last_move': timestamp.timestamp(), 'last_db_update': timestamp.timestamp()}
            cache.set(trip_cache_key, trip_info, 86400)
            logger.info(f"Nouveau trajet détecté pour {device.name}")
        else:
            # Trajet en cours
            trip_info['last_move'] = timestamp.timestamp()
            last_db_update = trip_info.get('last_db_update', 0)
            
            # Mise à jour DB toutes les 2 minutes
            if timestamp.timestamp() - last_db_update > 120:
                Trip.objects.filter(id=trip_info['id']).update(end_time=timestamp)
                trip_info['last_db_update'] = timestamp.timestamp()
            
            cache.set(trip_cache_key, trip_info, 86400)
    else:
        # --- VÉHICULE À L'ARRÊT OU AU RALENTI ---
        
        if trip_info:
            # On vérifie si l'arrêt dépasse le seuil pour clôturer le trajet
            last_move = timezone.datetime.fromtimestamp(trip_info['last_move'], tz=timezone.get_current_timezone())
            idle_duration = (timestamp - last_move).total_seconds()
            
            if idle_duration > stop_threshold_seconds:
                # 1. Terminer le trajet
                Trip.objects.filter(id=trip_info['id']).update(
                    end_time=last_move,
                    is_completed=True
                )
                try:
                    t = Trip.objects.get(id=trip_info['id'])
                    t.calculate_duration()
                    t.save(update_fields=['duration_seconds'])
                    logger.info(f"Trajet terminé pour {device.name} (durée: {t.duration_seconds}s)")
                except: pass
                
                cache.delete(trip_cache_key)
                
                # 2. Démarrer un Arrêt rétroactif (qui a commencé lors du last_move)
                if not stop_info:
                    stop = Stop.objects.create(
                        device=device,
                        latitude=data.get('latitude', 0.0),
                        longitude=data.get('longitude', 0.0),
                        start_time=last_move,
                        end_time=timestamp,
                        ignition_off=not ignition  # Si ignition est True à 0km/h => Ralenti (Idling)
                    )
                    stop_info = {'id': stop.id, 'start': last_move.timestamp(), 'last_db_update': timestamp.timestamp()}
                    cache.set(stop_cache_key, stop_info, 86400)
                    state_str = "Ralenti (Idling)" if ignition else "Arrêt moteur coupé"
                    logger.info(f"Nouvel arrêt détecté ({state_str}) pour {device.name}")
        else:
            # Pas de trajet en cours, on met à jour ou crée l'arrêt
            if not stop_info:
                # Création initiale (ex: premier ping après redémarrage serveur)
                stop = Stop.objects.create(
                    device=device,
                    latitude=data.get('latitude', 0.0),
                    longitude=data.get('longitude', 0.0),
                    start_time=timestamp,
                    end_time=timestamp,
                    ignition_off=not ignition
                )
                stop_info = {'id': stop.id, 'start': timestamp.timestamp(), 'last_db_update': timestamp.timestamp()}
                cache.set(stop_cache_key, stop_info, 86400)
            else:
                # Mise à jour de l'arrêt existant
                last_db_update = stop_info.get('last_db_update', 0)
                if timestamp.timestamp() - last_db_update > 120:
                    start_time = timezone.datetime.fromtimestamp(stop_info['start'], tz=timezone.get_current_timezone())
                    duration = int((timestamp - start_time).total_seconds())
                    
                    update_dict = {'end_time': timestamp, 'duration_seconds': duration}
                    
                    # Si le moteur est coupé en plein milieu de l'arrêt, on met à jour le statut
                    if not ignition:
                        update_dict['ignition_off'] = True
                        
                    Stop.objects.filter(id=stop_info['id']).update(**update_dict)
                    stop_info['last_db_update'] = timestamp.timestamp()
                    cache.set(stop_cache_key, stop_info, 86400)


def broadcast_position_update(device, position_data):
    """
    Diffuse la mise à jour de position via WebSocket
    position_data est un dictionnaire (provenant de Redis ou Ingest).
    """
    
    channel_layer = get_channel_layer()
    
    # S'assurer que les données sont prêtes pour le frontend
    # Note: On renvoie l'objet entier qui contient déjà les bons noms de champs
    data_to_send = {
        'device_id': device.id,
        'device_name': device.name,
        'latitude': position_data.get('latitude'),
        'longitude': position_data.get('longitude'),
        'altitude': position_data.get('altitude'),
        'speed': position_data.get('speed'),
        'heading': position_data.get('heading'),
        'satellites': position_data.get('satellites'),
        'ignition': position_data.get('ignition'),
        'battery_level': position_data.get('battery_level'),
        'external_power': position_data.get('external_power'),
        'odometer': position_data.get('odometer'),
        'signal': position_data.get('signal_strength'),
        'timestamp': position_data.get('timestamp'),
        'is_online': True, # Puisqu'on reçoit des données
    }
    
    # Envoyer au groupe du device spécifique
    async_to_sync(channel_layer.group_send)(
        f'device_{device.id}',
        {
            'type': 'position_update',
            'data': data_to_send
        }
    )
    
    # Envoyer au groupe de l'utilisateur propriétaire
    async_to_sync(channel_layer.group_send)(
        f'user_{device.owner.id}',
        {
            'type': 'position_update',
            'data': data_to_send
        }
    )
    
    # Envoyer aux sous-comptes avec permissions
    from accounts.models import SubAccountPermission
    sub_permissions = SubAccountPermission.objects.filter(
        device=device
    ).select_related('sub_account')
    
    for perm in sub_permissions:
        if perm.has_permission('track'):
            async_to_sync(channel_layer.group_send)(
                f'user_{perm.sub_account.id}',
                {
                    'type': 'position_update',
                    'data': position_data
                }
            )


def broadcast_device_status(device):
    """Diffuse le changement de statut (online/offline) via WebSocket"""
    channel_layer = get_channel_layer()
    
    status_data = {
        'device_id': device.id,
        'imei': device.imei,
        'is_online': device.is_online,
        'last_connection': device.last_connection.isoformat() if device.last_connection else None
    }
    
    # Envoyer au groupe du device
    async_to_sync(channel_layer.group_send)(
        f'device_{device.id}',
        {
            'type': 'device_status',
            'data': status_data
        }
    )
    
    # Envoyer au groupe utilisateur propriétaire
    async_to_sync(channel_layer.group_send)(
        f'user_{device.owner.id}',
        {
            'type': 'device_status',
            'data': status_data
        }
    )
    
    # Envoyer aux sous-comptes
    from accounts.models import SubAccountPermission
    sub_permissions = SubAccountPermission.objects.filter(device=device).select_related('sub_account')
    for perm in sub_permissions:
        async_to_sync(channel_layer.group_send)(
            f'user_{perm.sub_account.id}',
            {
                'type': 'device_status',
                'data': status_data
            }
        )


# --- API ViewSets ---

class GPSPositionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consultation de l'historique des positions
    """
    serializer_class = GPSPositionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = GPSPosition.objects.all()
        else:
            # Filtrer par device appartenant à l'utilisateur OU dont il est le sous-compte autorisé
            queryset = GPSPosition.objects.filter(
                Q(device__owner=user) | 
                Q(device__sub_account_permissions__sub_account=user)
            ).distinct()
            
            # Limiter l'historique selon le package de facturation
            history_days = user.billing_package.history_days if user.billing_package else 30
            limit_date = timezone.now() - timezone.timedelta(days=history_days)
            queryset = queryset.filter(timestamp__gte=limit_date)
        
        device_id = self.request.query_params.get('device_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset

    @action(detail=False, methods=['get'])
    def path(self, request):
        """Retourne l'historique brut sans pagination pour le replay sur la carte"""
        queryset = self.get_queryset().order_by('timestamp')
        
        # Limiter à 5000 points maximum pour éviter de faire crasher le frontend
        # Si la période est longue, l'utilisateur doit filtrer par date
        data = queryset.values(
            'id', 'latitude', 'longitude', 'speed', 'timestamp', 'ignition', 'heading'
        )[:5000]
        
        return Response(list(data))

class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historique des trajets effectués
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = Trip.objects.all()
        else:
            queryset = Trip.objects.filter(
                Q(device__owner=user) | 
                Q(device__sub_account_permissions__sub_account=user)
            ).distinct()
            
            # Limiter l'historique selon le package de facturation
            history_days = user.billing_package.history_days if user.billing_package else 30
            limit_date = timezone.now() - timezone.timedelta(days=history_days)
            queryset = queryset.filter(start_time__gte=limit_date)
            
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer

class GeofenceViewSet(viewsets.ModelViewSet):
    """
    Gestion des zones géographiques (Géofences)
    """
    serializer_class = GeofenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Geofence.objects.all()
        return Geofence.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReportViewSet(viewsets.ModelViewSet):
    """
    Gestion et génération de rapports
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Report.objects.all()
        return Report.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
