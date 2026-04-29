from rest_framework import serializers
from django.db import models
from django.utils import timezone
from .models import (
    DeviceGroup, Driver, DriverAssignment,
    FuelEntry, MaintenanceRecord, FleetStatistics
)
from devices.serializers import DeviceListSerializer


class DeviceGroupSerializer(serializers.ModelSerializer):
    """Serializer pour les groupes de devices"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    parent_group_name = serializers.CharField(source='parent_group.name', read_only=True, allow_null=True)
    devices_count = serializers.SerializerMethodField()
    subgroups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceGroup
        fields = [
            'id', 'user', 'user_email', 'name', 'description', 'color', 'icon',
            'parent_group', 'parent_group_name', 'devices_count', 'subgroups_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'parent_group_name', 'devices_count',
            'subgroups_count', 'created_at', 'updated_at'
        ]
    
    def get_devices_count(self, obj):
        """Retourne le nombre de devices dans le groupe"""
        return obj.devices.count()
    
    def get_subgroups_count(self, obj):
        """Retourne le nombre de sous-groupes"""
        return obj.subgroups.count()


class DeviceGroupTreeSerializer(serializers.ModelSerializer):
    """Serializer hiérarchique pour les groupes de devices"""
    
    subgroups = serializers.SerializerMethodField()
    devices = DeviceListSerializer(many=True, read_only=True)
    
    class Meta:
        model = DeviceGroup
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'devices', 'subgroups'
        ]
    
    def get_subgroups(self, obj):
        """Retourne les sous-groupes de manière récursive"""
        subgroups = obj.subgroups.all()
        return DeviceGroupTreeSerializer(subgroups, many=True).data


class DriverSerializer(serializers.ModelSerializer):
    """Serializer pour les conducteurs"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    current_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = Driver
        fields = [
            'id', 'user', 'user_email', 'first_name', 'last_name', 'full_name',
            'employee_id', 'phone', 'email', 'photo',
            'license_number', 'license_category', 'license_expiry',
            'address', 'city', 'is_active', 'rfid_tag', 'notes',
            'current_assignment', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'full_name', 'current_assignment',
            'created_at', 'updated_at'
        ]
    
    def get_current_assignment(self, obj):
        """Retourne l'assignation actuelle du conducteur"""
        from django.utils import timezone
        
        current = obj.assignments.filter(
            start_time__lte=timezone.now()
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gte=timezone.now())
        ).first()
        
        if current:
            return {
                'id': current.id,
                'device_id': current.device.id,
                'device_name': current.device.name,
                'start_time': current.start_time
            }
        return None
    
    def validate_rfid_tag(self, value):
        """Valide que le tag RFID est unique"""
        if value:
            if self.instance:
                if Driver.objects.exclude(pk=self.instance.pk).filter(rfid_tag=value).exists():
                    raise serializers.ValidationError("Ce tag RFID est déjà utilisé.")
            else:
                if Driver.objects.filter(rfid_tag=value).exists():
                    raise serializers.ValidationError("Ce tag RFID est déjà utilisé.")
        return value


class DriverListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des conducteurs"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Driver
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'employee_id',
            'phone', 'is_active'
        ]
        read_only_fields = fields


class DriverAssignmentSerializer(serializers.ModelSerializer):
    """Serializer pour les assignations conducteur-véhicule"""
    
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    driver_details = DriverListSerializer(source='driver', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    is_current_assignment = serializers.BooleanField(source='is_current', read_only=True)
    
    class Meta:
        model = DriverAssignment
        fields = [
            'id', 'driver', 'driver_name', 'driver_details',
            'device', 'device_name', 'device_imei',
            'start_time', 'end_time', 'is_auto_detected',
            'is_current_assignment', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'driver_name', 'driver_details', 'device_name', 'device_imei',
            'is_current_assignment', 'created_at', 'updated_at'
        ]


class DriverAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une assignation"""
    
    class Meta:
        model = DriverAssignment
        fields = [
            'driver', 'device', 'start_time', 'end_time', 'notes'
        ]
    
    def validate(self, attrs):
        """Valide l'assignation"""
        driver = attrs.get('driver')
        device = attrs.get('device')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        # Vérifier qu'il n'y a pas de chevauchement pour le conducteur
        overlapping = DriverAssignment.objects.filter(
            driver=driver,
            start_time__lt=end_time if end_time else timezone.now() + timezone.timedelta(days=365)
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gt=start_time)
        ).exists()
        
        if overlapping:
            raise serializers.ValidationError(
                "Ce conducteur a déjà une assignation pendant cette période."
            )
        
        return attrs


class FuelEntrySerializer(serializers.ModelSerializer):
    """Serializer pour les entrées de carburant"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_plate = serializers.CharField(source='device.vehicle_plate', read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True, allow_null=True)
    fuel_type_display = serializers.CharField(source='get_fuel_type_display', read_only=True)
    consumption = serializers.SerializerMethodField()
    
    class Meta:
        model = FuelEntry
        fields = [
            'id', 'device', 'device_name', 'device_plate', 'driver', 'driver_name',
            'fuel_type', 'fuel_type_display', 'quantity_liters', 'cost',
            'price_per_liter', 'currency', 'odometer_reading', 'is_full_tank',
            'location', 'latitude', 'longitude', 'receipt', 'filled_at',
            'consumption', 'notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_plate', 'driver_name',
            'fuel_type_display', 'consumption', 'created_at'
        ]
    
    def get_consumption(self, obj):
        """Retourne la consommation calculée"""
        return obj.calculate_consumption()


class FuelEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une entrée de carburant"""
    
    class Meta:
        model = FuelEntry
        fields = [
            'device', 'driver', 'fuel_type', 'quantity_liters', 'cost',
            'price_per_liter', 'currency', 'odometer_reading', 'is_full_tank',
            'location', 'latitude', 'longitude', 'receipt', 'filled_at', 'notes'
        ]
    
    def validate(self, attrs):
        """Calcule automatiquement le prix par litre si non fourni"""
        if not attrs.get('price_per_liter') and attrs.get('cost') and attrs.get('quantity_liters'):
            attrs['price_per_liter'] = attrs['cost'] / attrs['quantity_liters']
        
        return attrs


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    """Serializer pour les enregistrements de maintenance"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_plate = serializers.CharField(source='device.vehicle_plate', read_only=True)
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'id', 'device', 'device_name', 'device_plate',
            'maintenance_type', 'maintenance_type_display', 'title', 'description',
            'odometer_reading', 'labor_cost', 'parts_cost', 'total_cost', 'currency',
            'service_provider', 'invoice', 'service_date',
            'next_service_date', 'next_service_mileage', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_plate', 'maintenance_type_display',
            'created_at', 'updated_at'
        ]


class MaintenanceRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un enregistrement de maintenance"""
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'device', 'maintenance_type', 'title', 'description', 'odometer_reading',
            'labor_cost', 'parts_cost', 'currency', 'service_provider', 'invoice',
            'service_date', 'next_service_date', 'next_service_mileage', 'notes'
        ]
    
    def validate(self, attrs):
        """Calcule automatiquement le coût total"""
        labor_cost = attrs.get('labor_cost', 0)
        parts_cost = attrs.get('parts_cost', 0)
        attrs['total_cost'] = labor_cost + parts_cost
        
        return attrs


class FleetStatisticsSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques de flotte"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    
    class Meta:
        model = FleetStatistics
        fields = [
            'id', 'user', 'user_email', 'group', 'group_name', 'date',
            'total_devices', 'active_devices', 'total_distance_km',
            'total_fuel_liters', 'total_fuel_cost', 'total_engine_hours',
            'total_idle_hours', 'total_alerts', 'critical_alerts',
            'device_data', 'created_at'
        ]
        read_only_fields = fields


class FleetSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé de flotte en temps réel"""
    
    total_devices = serializers.IntegerField()
    online_devices = serializers.IntegerField()
    offline_devices = serializers.IntegerField()
    moving_devices = serializers.IntegerField()
    stopped_devices = serializers.IntegerField()
    total_distance_today = serializers.FloatField()
    alerts_today = serializers.IntegerField()
    devices_by_status = serializers.DictField()


class FuelAnalysisSerializer(serializers.Serializer):
    """Serializer pour l'analyse de consommation de carburant"""
    
    device_id = serializers.IntegerField()
    device_name = serializers.CharField()
    total_fuel = serializers.FloatField()
    total_cost = serializers.FloatField()
    total_distance = serializers.FloatField()
    avg_consumption = serializers.FloatField()
    entries_count = serializers.IntegerField()
    last_fill_date = serializers.DateTimeField()


class MaintenanceSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé de maintenance"""
    
    device_id = serializers.IntegerField()
    device_name = serializers.CharField()
    total_maintenance_cost = serializers.FloatField()
    last_maintenance_date = serializers.DateField()
    next_maintenance_date = serializers.DateField(allow_null=True)
    next_maintenance_mileage = serializers.IntegerField(allow_null=True)
    current_odometer = serializers.IntegerField()
    maintenance_count = serializers.IntegerField()
