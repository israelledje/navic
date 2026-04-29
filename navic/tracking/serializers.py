from rest_framework import serializers
from .models import GPSPosition, Trip, Stop, Geofence, GeofenceEvent, Report
from devices.serializers import DeviceListSerializer


class GPSPositionSerializer(serializers.ModelSerializer):
    """Serializer pour les positions GPS"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    is_moving_flag = serializers.BooleanField(source='is_moving', read_only=True)
    location = serializers.SerializerMethodField()
    
    class Meta:
        model = GPSPosition
        fields = [
            'id', 'device', 'device_name', 'device_imei',
            'latitude', 'longitude', 'altitude', 'speed', 'heading',
            'satellites', 'hdop', 'ignition', 'battery_level', 'external_power',
            'odometer', 'fuel_level', 'temperature_1', 'temperature_2',
            'io_data', 'timestamp', 'server_time', 'protocol', 'raw_data',
            'is_processed', 'is_moving_flag', 'location'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_imei', 'server_time',
            'is_processed', 'is_moving_flag', 'location'
        ]
    
    def get_location(self, obj):
        """Retourne la position sous forme de dict"""
        return obj.get_location()


class GPSPositionListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des positions"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = GPSPosition
        fields = [
            'id', 'device', 'device_name', 'latitude', 'longitude',
            'speed', 'heading', 'timestamp', 'ignition', 'battery_level'
        ]
        read_only_fields = fields


class TripSerializer(serializers.ModelSerializer):
    """Serializer pour les trajets"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    start_position_details = GPSPositionListSerializer(source='start_position', read_only=True)
    end_position_details = GPSPositionListSerializer(source='end_position', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'device', 'device_name', 'device_imei',
            'start_position', 'start_position_details',
            'end_position', 'end_position_details',
            'start_time', 'end_time', 'duration_seconds',
            'start_address', 'end_address',
            'distance_km', 'max_speed', 'avg_speed', 'fuel_consumed',
            'is_completed', 'summary', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_imei', 'start_position_details',
            'end_position_details', 'created_at', 'updated_at'
        ]


class TripListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des trajets"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'device', 'device_name', 'start_time', 'end_time',
            'duration_seconds', 'distance_km', 'avg_speed', 'is_completed'
        ]
        read_only_fields = fields


class StopSerializer(serializers.ModelSerializer):
    """Serializer pour les arrêts"""
    
    trip_id = serializers.IntegerField(source='trip.id', read_only=True, allow_null=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = Stop
        fields = [
            'id', 'trip', 'trip_id', 'device', 'device_name',
            'latitude', 'longitude', 'address',
            'start_time', 'end_time', 'duration_seconds', 'ignition_off',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'trip_id', 'device_name', 'created_at', 'updated_at'
        ]


class GeofenceSerializer(serializers.ModelSerializer):
    """Serializer pour les géofences"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    shape_type_display = serializers.CharField(source='get_shape_type_display', read_only=True)
    devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Geofence
        fields = [
            'id', 'user', 'user_email', 'name', 'description',
            'shape_type', 'shape_type_display',
            'center_lat', 'center_lng', 'radius_meters', 'coordinates',
            'color', 'is_active', 'devices', 'devices_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'shape_type_display', 'devices_count',
            'created_at', 'updated_at'
        ]
    
    def get_devices_count(self, obj):
        """Retourne le nombre de devices associés"""
        return obj.devices.count()
    
    def validate(self, attrs):
        """Valide la géométrie de la géofence"""
        shape_type = attrs.get('shape_type')
        
        if shape_type == 'circle':
            if not all([attrs.get('center_lat'), attrs.get('center_lng'), attrs.get('radius_meters')]):
                raise serializers.ValidationError(
                    "Pour un cercle, center_lat, center_lng et radius_meters sont requis."
                )
        elif shape_type in ['polygon', 'rectangle']:
            coordinates = attrs.get('coordinates', [])
            if len(coordinates) < 3:
                raise serializers.ValidationError(
                    "Un polygone nécessite au moins 3 points."
                )
        
        return attrs


class GeofenceEventSerializer(serializers.ModelSerializer):
    """Serializer pour les événements de géofence"""
    
    geofence_name = serializers.CharField(source='geofence.name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    position_details = GPSPositionListSerializer(source='position', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = GeofenceEvent
        fields = [
            'id', 'geofence', 'geofence_name', 'device', 'device_name',
            'position', 'position_details', 'event_type', 'event_type_display',
            'timestamp', 'notification_sent'
        ]
        read_only_fields = [
            'id', 'geofence_name', 'device_name', 'position_details',
            'event_type_display', 'timestamp'
        ]


class ReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    devices_names = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'user', 'user_email', 'devices', 'devices_names',
            'report_type', 'report_type_display', 'status', 'status_display',
            'start_date', 'end_date', 'data', 'file_path',
            'title', 'description', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'devices_names', 'report_type_display',
            'status_display', 'data', 'file_path', 'created_at', 'completed_at'
        ]
    
    def get_devices_names(self, obj):
        """Retourne les noms des devices"""
        return [device.name for device in obj.devices.all()]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un rapport"""
    
    class Meta:
        model = Report
        fields = [
            'devices', 'report_type', 'start_date', 'end_date', 'title', 'description'
        ]
    
    def validate(self, attrs):
        """Valide les dates du rapport"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date >= end_date:
            raise serializers.ValidationError({
                "end_date": "La date de fin doit être postérieure à la date de début."
            })
        
        # Vérifier que l'utilisateur possède les devices
        user = self.context['request'].user
        devices = attrs.get('devices')
        
        for device in devices:
            if device.owner != user and not user.is_superuser:
                raise serializers.ValidationError({
                    "devices": f"Vous n'avez pas accès au device {device.name}."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Créer un rapport avec statut initial 'pending'"""
        user = self.context['request'].user
        devices = validated_data.pop('devices')
        
        report = Report.objects.create(
            **validated_data,
            user=user,
            status='pending'
        )
        report.devices.set(devices)
        
        # TODO: Lancer la tâche de génération du rapport (Celery)
        
        return report


class PositionHistoryFilterSerializer(serializers.Serializer):
    """Serializer pour filtrer l'historique des positions"""
    
    device_id = serializers.IntegerField(required=True)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    min_speed = serializers.FloatField(required=False, allow_null=True)
    max_speed = serializers.FloatField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Valide les paramètres de filtre"""
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError({
                "end_date": "La date de fin doit être postérieure à la date de début."
            })
        return attrs


class TripStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de trajet"""
    
    total_trips = serializers.IntegerField()
    total_distance = serializers.FloatField()
    total_duration = serializers.IntegerField()
    avg_speed = serializers.FloatField()
    max_speed = serializers.FloatField()
    total_fuel = serializers.FloatField(required=False, allow_null=True)
