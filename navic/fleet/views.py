from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import (
    DeviceGroup, Driver, DriverAssignment, 
    FuelEntry, MaintenanceRecord, FleetStatistics
)
from .serializers import (
    DeviceGroupSerializer, DriverSerializer, 
    DriverAssignmentSerializer, FuelEntrySerializer,
    MaintenanceRecordSerializer, FleetStatisticsSerializer
)

class DeviceGroupViewSet(viewsets.ModelViewSet):
    """
    Gestion des groupes de véhicules
    """
    serializer_class = DeviceGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeviceGroup.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DriverViewSet(viewsets.ModelViewSet):
    """
    Gestion des chauffeurs
    """
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Driver.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FuelEntryViewSet(viewsets.ModelViewSet):
    """
    Suivi de la consommation de carburant
    """
    serializer_class = FuelEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FuelEntry.objects.filter(device__owner=self.request.user)

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    """
    Historique des entretiens mécaniques
    """
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MaintenanceRecord.objects.filter(device__owner=self.request.user)

class FleetStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Statistiques globales de la flotte
    """
    serializer_class = FleetStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FleetStatistics.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Retourne les statistiques temps réel pour le tableau de bord
        """
        from django.utils import timezone
        from devices.models import Device
        from tracking.models import Trip
        from django.db.models import Sum, Count
        from datetime import timedelta
        
        user = request.user
        today = timezone.now().date()
        
        # 1. Stats Véhicules
        if user.is_superuser:
            devices_qs = Device.objects.all()
        else:
            devices_qs = Device.objects.filter(owner=user)
            
        total_vehicles = devices_qs.count()
        online_vehicles = devices_qs.filter(is_online=True).count()
        pending_vehicles = devices_qs.filter(last_connection__isnull=True).count()
        # Offline sont ceux qui ne sont pas online et qui ont déjà été connectés
        offline_vehicles = devices_qs.filter(is_online=False, last_connection__isnull=False).count()
        
        # 2. Stats Maintenance
        maintenances_qs = MaintenanceRecord.objects.filter(device__owner=user)
        completed_maintenance = maintenances_qs.filter(service_date__lte=today).count()
        # Expired = Maintenance prévue dépassée
        expired_maintenance = maintenances_qs.filter(next_service_date__lt=today).count()
        
        maintenance_stats = {
            'completed': completed_maintenance,
            'ongoing': 0, # Pas de champ statut actuellement
            'expired': expired_maintenance,
            'other': 0,
            'total': maintenances_qs.count()
        }

        # 3. Stats Missions (Simulé pour l'instant via Trajets)
        # On considère les Trajets complétés comme des "Missions" pour peupler le dashboard
        trips_qs = Trip.objects.filter(device__owner=user)
        completed_trips = trips_qs.filter(is_completed=True).count()
        ongoing_trips = trips_qs.filter(is_completed=False).count()
        
        missions_stats = {
            'completed': completed_trips,
            'assigned': ongoing_trips,
            'failed': 0,
            'other': 0,
            'total': completed_trips + ongoing_trips
        }

        # 4. Données du graphique Kilométrage (7 derniers jours)
        end_date = today
        start_date = end_date - timedelta(days=6)
        
        # Initialiser les labels (Jours)
        labels = []
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%d/%m/%Y'))
            current += timedelta(days=1)
            
        chart_datasets = []
        
        # Prendre les 5 véhicules les plus actifs
        top_devices = devices_qs.annotate(
            total_trips=Count('trips')
        ).order_by('-total_trips')[:5]
        
        colors = ['#f87171', '#38bdf8', '#4ade80', '#fb923c', '#6366f1']
        
        for index, device in enumerate(top_devices):
            data_points = []
            
            # Pour chaque jour, calculer la distance parcourue
            current = start_date
            while current <= end_date:
                # Filtrer les trajets qui ont commencé ce jour-là
                # Note: c'est une approx, idéalement il faut découper les trajets à cheval sur plusieurs jours
                day_distance = Trip.objects.filter(
                    device=device,
                    start_time__date=current
                ).aggregate(total=Sum('distance_km'))['total'] or 0.0
                
                data_points.append(round(day_distance, 1))
                current += timedelta(days=1)
                
            chart_datasets.append({
                'label': device.name,
                'data': data_points,
                'backgroundColor': colors[index % len(colors)]
            })
            
        # Si aucun device, mettre un dataset vide pour pas casser le chart
        if not chart_datasets:
             chart_datasets.append({
                'label': 'Aucune donnée',
                'data': [0, 0, 0, 0, 0, 0, 0],
                'backgroundColor': '#e2e8f0'
            })

        return Response({
            'vehicles': {
                'online': online_vehicles,
                'pending': pending_vehicles,
                'offline': offline_vehicles,
                'other': 0,
                'total': total_vehicles
            },
            'missions': missions_stats,
            'maintenance': maintenance_stats,
            'mileage': {
                'labels': labels,
                'datasets': chart_datasets
            }
        })
