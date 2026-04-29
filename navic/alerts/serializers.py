from rest_framework import serializers
from .models import AlertRule, Alert, NotificationLog, MaintenanceReminder
from devices.serializers import DeviceListSerializer
from tracking.serializers import GPSPositionListSerializer


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer pour les règles d'alerte"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True, allow_null=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    is_in_active_period_flag = serializers.BooleanField(source='is_in_active_period', read_only=True)
    should_trigger_flag = serializers.BooleanField(source='should_trigger', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'user', 'user_email', 'device', 'device_name',
            'name', 'alert_type', 'alert_type_display', 'severity', 'severity_display',
            'description', 'conditions',
            'notify_email', 'notify_sms', 'notify_push', 'notify_webhook', 'webhook_url',
            'additional_emails', 'additional_phones',
            'is_active', 'active_days', 'active_hours_start', 'active_hours_end',
            'cooldown_minutes', 'last_triggered',
            'is_in_active_period_flag', 'should_trigger_flag',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'device_name', 'alert_type_display',
            'severity_display', 'last_triggered', 'is_in_active_period_flag',
            'should_trigger_flag', 'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Valide la règle d'alerte"""
        alert_type = attrs.get('alert_type')
        conditions = attrs.get('conditions', {})
        
        # Validation selon le type d'alerte
        if alert_type == 'speed' and 'speed_threshold' not in conditions:
            raise serializers.ValidationError({
                "conditions": "Pour une alerte de vitesse, 'speed_threshold' est requis."
            })
        
        if alert_type in ['geofence_enter', 'geofence_exit'] and 'geofence_id' not in conditions:
            raise serializers.ValidationError({
                "conditions": "Pour une alerte de géofence, 'geofence_id' est requis."
            })
        
        # Valider le webhook si activé
        if attrs.get('notify_webhook') and not attrs.get('webhook_url'):
            raise serializers.ValidationError({
                "webhook_url": "L'URL du webhook est requise si les notifications webhook sont activées."
            })
        
        return attrs


class AlertRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une règle d'alerte"""
    
    class Meta:
        model = AlertRule
        fields = [
            'device', 'name', 'alert_type', 'severity', 'description', 'conditions',
            'notify_email', 'notify_sms', 'notify_push', 'notify_webhook', 'webhook_url',
            'additional_emails', 'additional_phones',
            'is_active', 'active_days', 'active_hours_start', 'active_hours_end',
            'cooldown_minutes'
        ]


class AlertSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes déclenchées"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True, allow_null=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    position_details = GPSPositionListSerializer(source='position', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_email = serializers.EmailField(
        source='acknowledged_by.email',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Alert
        fields = [
            'id', 'rule', 'rule_name', 'device', 'device_name', 'device_imei',
            'user', 'user_email', 'alert_type', 'severity',
            'title', 'message', 'position', 'position_details', 'data',
            'status', 'status_display',
            'email_sent', 'sms_sent', 'push_sent', 'webhook_sent',
            'triggered_at', 'acknowledged_at', 'acknowledged_by', 'acknowledged_by_email',
            'resolved_at', 'notes'
        ]
        read_only_fields = [
            'id', 'rule_name', 'device_name', 'device_imei', 'user_email',
            'position_details', 'status_display', 'acknowledged_by_email',
            'triggered_at'
        ]


class AlertListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des alertes"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'device', 'device_name', 'alert_type', 'severity',
            'title', 'status', 'status_display', 'triggered_at'
        ]
        read_only_fields = fields


class AlertAcknowledgeSerializer(serializers.Serializer):
    """Serializer pour acquitter une alerte"""
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Valide que l'alerte peut être acquittée"""
        alert = self.context.get('alert')
        
        if alert.status != 'new':
            raise serializers.ValidationError(
                "Cette alerte a déjà été acquittée ou résolue."
            )
        
        return attrs


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer pour le journal des notifications"""
    
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'alert', 'alert_title', 'notification_type', 'notification_type_display',
            'recipient', 'status', 'status_display', 'subject', 'content',
            'response', 'error_message', 'created_at', 'sent_at'
        ]
        read_only_fields = fields


class MaintenanceReminderSerializer(serializers.ModelSerializer):
    """Serializer pour les rappels de maintenance"""
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MaintenanceReminder
        fields = [
            'id', 'device', 'device_name', 'device_imei', 'user', 'user_email',
            'title', 'description', 'reminder_type', 'reminder_type_display',
            'status', 'status_display', 'due_date', 'due_mileage',
            'notify_days_before', 'notify_km_before', 'last_notification',
            'completed_at', 'actual_mileage', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'device_name', 'device_imei', 'user_email',
            'reminder_type_display', 'status_display', 'last_notification',
            'created_at', 'updated_at'
        ]


class MaintenanceReminderCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un rappel de maintenance"""
    
    class Meta:
        model = MaintenanceReminder
        fields = [
            'device', 'title', 'description', 'reminder_type',
            'due_date', 'due_mileage', 'notify_days_before', 'notify_km_before'
        ]
    
    def validate(self, attrs):
        """Valide le rappel selon le type"""
        reminder_type = attrs.get('reminder_type')
        
        if reminder_type == 'time' and not attrs.get('due_date'):
            raise serializers.ValidationError({
                "due_date": "La date d'échéance est requise pour un rappel temporel."
            })
        
        if reminder_type == 'mileage' and not attrs.get('due_mileage'):
            raise serializers.ValidationError({
                "due_mileage": "Le kilométrage d'échéance est requis pour un rappel kilométrique."
            })
        
        if reminder_type == 'both':
            if not attrs.get('due_date') or not attrs.get('due_mileage'):
                raise serializers.ValidationError(
                    "La date et le kilométrage d'échéance sont requis pour un rappel combiné."
                )
        
        return attrs


class MaintenanceCompleteSerializer(serializers.Serializer):
    """Serializer pour marquer une maintenance comme effectuée"""
    
    actual_mileage = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Valide que le rappel peut être marqué comme complété"""
        reminder = self.context.get('reminder')
        
        if reminder.status == 'completed':
            raise serializers.ValidationError(
                "Cette maintenance a déjà été marquée comme effectuée."
            )
        
        return attrs


class AlertStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'alertes"""
    
    total_alerts = serializers.IntegerField()
    new_alerts = serializers.IntegerField()
    acknowledged_alerts = serializers.IntegerField()
    resolved_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    warning_alerts = serializers.IntegerField()
    info_alerts = serializers.IntegerField()
    alerts_by_type = serializers.DictField()
    alerts_by_device = serializers.DictField()
