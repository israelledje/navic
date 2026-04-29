"""
Tâches de traitement des alertes
Dans un environnement de production, ceci devrait être exécuté avec Celery
"""
import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger('tracking')


def process_position_for_alerts(position_id):
    """
    Traite une position GPS pour détecter et déclencher les alertes
    
    Args:
        position_id: ID de la position GPS à traiter
    """
    from tracking.models import GPSPosition
    from .models import AlertRule, Alert
    from .notifications import send_alert_notifications
    
    try:
        position = GPSPosition.objects.select_related('device', 'device__owner').get(id=position_id)
    except GPSPosition.DoesNotExist:
        logger.error(f"Position GPS {position_id} non trouvée")
        return
    
    device = position.device
    user = device.owner
    
    # Récupérer les règles d'alerte actives pour ce device
    alert_rules = AlertRule.objects.filter(
        user=user,
        is_active=True
    ).filter(
        models.Q(device=device) | models.Q(device__isnull=True)
    )
    
    for rule in alert_rules:
        # Vérifier si la règle peut être déclenchée (cooldown, horaires, etc.)
        if not rule.should_trigger():
            continue
        
        # Vérifier les conditions selon le type d'alerte
        should_trigger = check_alert_condition(rule, position, device)
        
        if should_trigger:
            # Créer l'alerte
            alert = create_alert(rule, position, device, user)
            
            # Mettre à jour le timestamp de dernière activation
            rule.last_triggered = timezone.now()
            rule.save(update_fields=['last_triggered'])
            
            # Envoyer les notifications
            send_alert_notifications(alert)
            
            # Diffuser l'alerte en temps réel
            broadcast_alert(alert)
    
    # Marquer la position comme traitée
    position.is_processed = True
    position.save(update_fields=['is_processed'])


def check_alert_condition(rule, position, device):
    """
    Vérifie si la condition d'une règle d'alerte est remplie
    
    Args:
        rule: Règle d'alerte
        position: Position GPS
        device: Device
    
    Returns:
        bool: True si la condition est remplie
    """
    from tracking.models import Geofence
    
    alert_type = rule.alert_type
    conditions = rule.conditions
    
    # Excès de vitesse
    if alert_type == 'speed':
        threshold = conditions.get('speed_threshold', 120)
        if position.speed > threshold:
            return True
    
    # Contact allumé
    elif alert_type == 'ignition_on':
        if position.ignition is True:
            # Vérifier si c'était éteint auparavant
            from tracking.models import GPSPosition
            prev_position = GPSPosition.objects.filter(
                device=device,
                timestamp__lt=position.timestamp
            ).order_by('-timestamp').first()
            
            if prev_position and prev_position.ignition is False:
                return True
    
    # Contact éteint
    elif alert_type == 'ignition_off':
        if position.ignition is False:
            from tracking.models import GPSPosition
            prev_position = GPSPosition.objects.filter(
                device=device,
                timestamp__lt=position.timestamp
            ).order_by('-timestamp').first()
            
            if prev_position and prev_position.ignition is True:
                return True
    
    # Batterie faible
    elif alert_type == 'low_battery':
        threshold = conditions.get('battery_threshold', 20)
        if position.battery_level and position.battery_level < threshold:
            return True
    
    # Entrée/Sortie de géofence
    elif alert_type in ['geofence_enter', 'geofence_exit']:
        geofence_id = conditions.get('geofence_id')
        if geofence_id:
            try:
                geofence = Geofence.objects.get(id=geofence_id, is_active=True)
                is_inside = check_point_in_geofence(position, geofence)
                
                # Vérifier la position précédente
                from tracking.models import GPSPosition
                prev_position = GPSPosition.objects.filter(
                    device=device,
                    timestamp__lt=position.timestamp
                ).order_by('-timestamp').first()
                
                if prev_position:
                    was_inside = check_point_in_geofence(prev_position, geofence)
                    
                    # Entrée dans la zone
                    if alert_type == 'geofence_enter' and is_inside and not was_inside:
                        return True
                    
                    # Sortie de la zone
                    elif alert_type == 'geofence_exit' and not is_inside and was_inside:
                        return True
            except Geofence.DoesNotExist:
                pass
    
    # Device hors ligne
    elif alert_type == 'offline':
        # Vérifier le temps depuis la dernière connexion
        if device.last_connection:
            from datetime import timedelta
            offline_threshold = conditions.get('offline_minutes', 30)
            if (timezone.now() - device.last_connection).total_seconds() / 60 > offline_threshold:
                return True
    
    # Baisse de carburant (vol potentiel)
    elif alert_type == 'fuel_drop':
        if position.fuel_level is not None:
            from tracking.models import GPSPosition
            prev_position = GPSPosition.objects.filter(
                device=device,
                timestamp__lt=position.timestamp,
                fuel_level__isnull=False
            ).order_by('-timestamp').first()
            
            if prev_position and prev_position.fuel_level:
                drop_threshold = conditions.get('fuel_drop_percent', 20)
                drop = prev_position.fuel_level - position.fuel_level
                
                if drop > drop_threshold:
                    return True
    
    # Remorquage (mouvement sans contact)
    elif alert_type == 'tow':
        if position.ignition is False and position.speed > 10:
            return True
    
    # Accélération brusque
    elif alert_type == 'harsh_acceleration':
        # Nécessite le calcul de l'accélération entre deux positions
        from tracking.models import GPSPosition
        prev_position = GPSPosition.objects.filter(
            device=device,
            timestamp__lt=position.timestamp
        ).order_by('-timestamp').first()
        
        if prev_position:
            time_diff = (position.timestamp - prev_position.timestamp).total_seconds()
            if time_diff > 0 and time_diff < 10:  # Dans les 10 dernières secondes
                speed_diff = position.speed - prev_position.speed
                acceleration = speed_diff / time_diff  # km/h/s
                
                threshold = conditions.get('acceleration_threshold', 10)  # km/h/s
                if acceleration > threshold:
                    return True
    
    # Freinage brusque
    elif alert_type == 'harsh_braking':
        from tracking.models import GPSPosition
        prev_position = GPSPosition.objects.filter(
            device=device,
            timestamp__lt=position.timestamp
        ).order_by('-timestamp').first()
        
        if prev_position:
            time_diff = (position.timestamp - prev_position.timestamp).total_seconds()
            if time_diff > 0 and time_diff < 10:
                speed_diff = prev_position.speed - position.speed
                deceleration = speed_diff / time_diff
                
                threshold = conditions.get('braking_threshold', 10)
                if deceleration > threshold:
                    return True
    
    return False


def check_point_in_geofence(position, geofence):
    """
    Vérifie si un point est dans une géofence
    
    Args:
        position: Position GPS
        geofence: Géofence
    
    Returns:
        bool: True si le point est dans la géofence
    """
    import math
    
    if geofence.shape_type == 'circle':
        # Calculer la distance entre le point et le centre
        lat1, lon1 = position.latitude, position.longitude
        lat2, lon2 = geofence.center_lat, geofence.center_lng
        
        # Formule de Haversine
        R = 6371000  # Rayon de la Terre en mètres
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance <= geofence.radius_meters
    
    elif geofence.shape_type in ['polygon', 'rectangle']:
        # Algorithme du raycasting pour polygone
        coordinates = geofence.coordinates
        if not coordinates or len(coordinates) < 3:
            return False
        
        x, y = position.latitude, position.longitude
        inside = False
        
        j = len(coordinates) - 1
        for i in range(len(coordinates)):
            xi, yi = coordinates[i]
            xj, yj = coordinates[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    return False


def create_alert(rule, position, device, user):
    """
    Crée une alerte
    
    Args:
        rule: Règle d'alerte
        position: Position GPS
        device: Device
        user: Utilisateur
    
    Returns:
        Alert: Alerte créée
    """
    from .models import Alert
    
    # Générer le titre et le message selon le type d'alerte
    alert_type = rule.alert_type
    
    if alert_type == 'speed':
        threshold = rule.conditions.get('speed_threshold', 120)
        title = f"Excès de vitesse - {device.name}"
        message = f"Le véhicule {device.name} roule à {position.speed:.1f} km/h (limite: {threshold} km/h)"
    
    elif alert_type == 'ignition_on':
        title = f"Contact allumé - {device.name}"
        message = f"Le contact du véhicule {device.name} a été allumé"
    
    elif alert_type == 'ignition_off':
        title = f"Contact éteint - {device.name}"
        message = f"Le contact du véhicule {device.name} a été éteint"
    
    elif alert_type == 'low_battery':
        title = f"Batterie faible - {device.name}"
        message = f"La batterie du véhicule {device.name} est à {position.battery_level}%"
    
    elif alert_type in ['geofence_enter', 'geofence_exit']:
        geofence_name = rule.conditions.get('geofence_name', 'zone')
        action = "entré dans" if alert_type == 'geofence_enter' else "sorti de"
        title = f"Géofence - {device.name}"
        message = f"Le véhicule {device.name} est {action} la zone {geofence_name}"
    
    elif alert_type == 'tow':
        title = f"Remorquage détecté - {device.name}"
        message = f"Le véhicule {device.name} se déplace sans contact allumé (remorquage possible)"
    
    elif alert_type == 'fuel_drop':
        title = f"Baisse de carburant - {device.name}"
        message = f"Une baisse importante de carburant a été détectée sur {device.name}"
    
    else:
        title = f"{rule.get_alert_type_display()} - {device.name}"
        message = rule.description or f"Alerte {rule.get_alert_type_display()} déclenchée"
    
    alert = Alert.objects.create(
        rule=rule,
        device=device,
        user=user,
        alert_type=alert_type,
        severity=rule.severity,
        title=title,
        message=message,
        position=position,
        data={
            'speed': position.speed,
            'latitude': position.latitude,
            'longitude': position.longitude,
            'timestamp': position.timestamp.isoformat(),
        }
    )
    
    logger.info(f"Alerte créée: {title}")
    
    return alert


def broadcast_alert(alert):
    """Diffuse une alerte en temps réel via WebSocket"""
    
    channel_layer = get_channel_layer()
    
    alert_data = {
        'id': alert.id,
        'title': alert.title,
        'message': alert.message,
        'severity': alert.severity,
        'device_id': alert.device.id,
        'device_name': alert.device.name,
        'triggered_at': alert.triggered_at.isoformat(),
    }
    
    # Envoyer au groupe d'alertes de l'utilisateur
    async_to_sync(channel_layer.group_send)(
        f'alerts_{alert.user.id}',
        {
            'type': 'new_alert',
            'data': alert_data
        }
    )
