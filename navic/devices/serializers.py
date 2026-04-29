from rest_framework import serializers
from django.core.cache import cache
from .models import Protocol, DeviceModel, Device, DeviceCommand, DeviceSettings


class ProtocolSerializer(serializers.ModelSerializer):
    """Serializer pour les protocoles"""
    class Meta:
        model = Protocol
        fields = ['id', 'code', 'tcp_port', 'udp_port', 'description']


class DeviceModelSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de devices"""
    
    protocol_code = serializers.CharField(source='protocol.code', read_only=True)
    
    class Meta:
        model = DeviceModel
        fields = [
            'id', 'name', 'manufacturer', 'protocol', 'protocol_code',
            'description', 'supported_features', 'is_active',
            'analog_inputs', 'digital_inputs', 'digital_outputs', 'has_canbus', 'supported_sensors',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'protocol_code', 'created_at', 'updated_at']


class DeviceSettingsSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres de device"""
    
    class Meta:
        model = DeviceSettings  
        fields = [
            'device', 'device_plan', 'apn', 'apn_user', 'apn_password',
            'authorized_numbers', 'reporting_interval_moving',
            'reporting_interval_stopped', 'timezone',
            'idling_threshold', 'idling_speed_limit', 'offline_timeout',
            'fuel_sensor_enabled',
            'temperature_sensor_enabled', 'door_sensor_enabled',
            'custom_settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['device', 'created_at', 'updated_at']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer pour les devices GPS"""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    device_model_name = serializers.CharField(source='device_model.name', read_only=True)
    device_model_details = DeviceModelSerializer(source='device_model', read_only=True)
    settings = DeviceSettingsSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    protocol = serializers.CharField(source='get_protocol', read_only=True)
    last_position = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'owner', 'owner_email', 'owner_name',
            'device_model', 'device_model_name', 'device_model_details',
            'imei', 'name', 'description', 'status', 'status_display',
            'vehicle_plate', 'vehicle_type', 'vehicle_brand', 'vehicle_model',
            'vehicle_color', 'vehicle_year',
            'icon', 'color', 'last_connection', 'last_position', 'is_online',
            'update_interval', 'speed_limit',
            'settings', 'protocol', 'notes',
            'created_at', 'updated_at', 'installation_date', 'warranty_expiry'
        ]
        read_only_fields = [
            'created_at', 'updated_at'
        ]

    def get_last_position(self, obj):
        """Récupère la position depuis Redis ou DB"""
        cached = cache.get(f"device_last_pos:{obj.id}")
        return cached if cached else obj.last_position

    def get_is_online(self, obj):
        """Récupère le statut online depuis Redis ou DB"""
        cached = cache.get(f"device_online:{obj.id}")
        return cached if cached is not None else obj.is_online
    
    def validate_imei(self, value):
        """Valide que l'IMEI est unique"""
        if self.instance:
            # Mode mise à jour
            if Device.objects.exclude(pk=self.instance.pk).filter(imei=value).exists():
                raise serializers.ValidationError("Cet IMEI est déjà utilisé.")
        else:
            # Mode création
            if Device.objects.filter(imei=value).exists():
                raise serializers.ValidationError("Cet IMEI est déjà utilisé.")
        return value
    
    def validate(self, attrs):
        """Valide que l'utilisateur peut créer un device"""
        if not self.instance:  # Création
            user = self.context['request'].user
            if not user.can_create_device():
                raise serializers.ValidationError(
                    "Vous avez atteint le nombre maximum de devices autorisé par votre package."
                )
        return attrs


class DeviceListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des devices"""
    
    device_model_name = serializers.CharField(source='device_model.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    last_position = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'imei', 'name', 'device_model_name', 'status', 'status_display',
            'vehicle_plate', 'vehicle_type', 'icon', 'color',
            'last_connection', 'is_online', 'last_position'
        ]
        read_only_fields = fields

    def get_last_position(self, obj):
        cached = cache.get(f"device_last_pos:{obj.id}")
        return cached if cached else obj.last_position

    def get_is_online(self, obj):
        cached = cache.get(f"device_online:{obj.id}")
        return cached if cached is not None else obj.is_online


class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un device"""
    
    class Meta:
        model = Device
        fields = [
            'device_model', 'imei', 'name', 'description',
            'vehicle_plate', 'vehicle_type', 'vehicle_brand',
            'vehicle_model', 'vehicle_color', 'vehicle_year',
            'icon', 'color', 'update_interval', 'speed_limit',
            'installation_date', 'warranty_expiry', 'notes'
        ]
    
    def validate_imei(self, value):
        """Valide que l'IMEI est unique"""
        if Device.objects.filter(imei=value).exists():
            raise serializers.ValidationError("Cet IMEI est déjà utilisé.")
        return value


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un device"""
    
    class Meta:
        model = Device
        fields = [
            'name', 'description', 'status',
            'vehicle_plate', 'vehicle_type', 'vehicle_brand',
            'vehicle_model', 'vehicle_color', 'vehicle_year',
            'icon', 'color', 'update_interval', 'speed_limit',
            'installation_date', 'warranty_expiry', 'notes'
        ]


class DeviceCommandSerializer(serializers.ModelSerializer):
    """Serializer pour les commandes envoyées aux devices"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    command_type_display = serializers.CharField(source='get_command_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeviceCommand
        fields = [
            'id', 'device', 'device_name', 'device_imei',
            'user', 'user_email', 'command_type', 'command_type_display',
            'command_data', 'raw_command', 'status', 'status_display',
            'response', 'error_message',
            'created_at', 'sent_at', 'delivered_at', 'executed_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_imei', 'user_email',
            'command_type_display', 'status_display', 'response',
            'error_message', 'created_at', 'sent_at', 'delivered_at',
            'executed_at'
        ]


class DeviceCommandCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une commande device"""
    
    class Meta:
        model = DeviceCommand
        fields = [
            'device', 'command_type', 'command_data', 'expires_at'
        ]
    
    def validate(self, attrs):
        """Valide que le device est en ligne"""
        device = attrs.get('device')
        
        if not device.is_online:
            raise serializers.ValidationError({
                "device": "Le device doit être en ligne pour recevoir une commande."
            })
        
        # Vérifier que l'utilisateur possède le device
        user = self.context['request'].user
        if device.owner != user and not user.is_superuser:
            raise serializers.ValidationError({
                "device": "Vous n'avez pas l'autorisation d'envoyer des commandes à ce device."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Créer une commande avec génération de la commande brute"""
        user = self.context['request'].user
        
        # Générer la commande brute selon le type et le protocole
        # Cette logique devrait être dans un service séparé
        command_type = validated_data['command_type']
        command_data = validated_data.get('command_data', {})
        
        # Exemple de génération de commande brute
        if command_type == 'locate':
            raw_command = "WHERE#"
        elif command_type == 'reboot':
            raw_command = "RESET#"
        else:
            raw_command = None
        
        command = DeviceCommand.objects.create(
            **validated_data,
            user=user,
            raw_command=raw_command,
            status='pending'
        )
        
        return command


class DeviceStatusSerializer(serializers.Serializer):
    """Serializer pour le statut en temps réel d'un device"""
    
    device_id = serializers.IntegerField()
    device_name = serializers.CharField()
    imei = serializers.CharField()
    is_online = serializers.BooleanField()
    last_connection = serializers.DateTimeField()
    last_position = serializers.JSONField()
    battery_level = serializers.IntegerField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    status = serializers.CharField()
