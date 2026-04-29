from django.db import models
from django.utils.translation import gettext_lazy as _


class AlertRule(models.Model):
    """Règles d'alerte configurées par les utilisateurs"""
    
    ALERT_TYPES = [
        ('speed', 'Excès de vitesse'),
        ('geofence_enter', 'Entrée dans zone'),
        ('geofence_exit', 'Sortie de zone'),
        ('ignition_on', 'Contact allumé'),
        ('ignition_off', 'Contact éteint'),
        ('low_battery', 'Batterie faible'),
        ('power_cut', 'Coupure alimentation'),
        ('tow', 'Remorquage détecté'),
        ('sos', 'Bouton SOS'),
        ('harsh_acceleration', 'Accélération brusque'),
        ('harsh_braking', 'Freinage brusque'),
        ('sharp_turn', 'Virage serré'),
        ('idle', 'Ralenti prolongé'),
        ('offline', 'Device hors ligne'),
        ('maintenance_due', 'Maintenance due'),
        ('fuel_drop', 'Baisse de carburant'),
        ('temperature', 'Alerte température'),
        ('custom', 'Personnalisée'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='alert_rules',
        null=True,
        blank=True,
        help_text="Device spécifique ou null pour tous les devices"
    )
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='warning')
    description = models.TextField(blank=True, null=True)
    
    # Configuration de l'alerte
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions de déclenchement (ex: {speed_threshold: 120})"
    )
    
    # Notification
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)
    notify_push = models.BooleanField(default=True)
    notify_webhook = models.BooleanField(default=False)
    webhook_url = models.URLField(blank=True, null=True)
    
    # Destinataires supplémentaires
    additional_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste d'emails supplémentaires à notifier"
    )
    additional_phones = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste de numéros de téléphone à notifier par SMS"
    )
    
    # Horaires d'activité
    is_active = models.BooleanField(default=True)
    active_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Jours actifs [0-6] où 0=Lundi"
    )
    active_hours_start = models.TimeField(null=True, blank=True)
    active_hours_end = models.TimeField(null=True, blank=True)
    
    # Anti-spam
    cooldown_minutes = models.IntegerField(
        default=5,
        help_text="Délai minimum entre deux alertes du même type (minutes)"
    )
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Règle d'alerte"
        verbose_name_plural = "Règles d'alerte"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device', 'is_active']),
        ]
    
    def __str__(self):
        device_name = self.device.name if self.device else "Tous les devices"
        return f"{self.name} - {device_name}"
    
    def is_in_active_period(self):
        """Vérifie si l'alerte est dans sa période active"""
        from django.utils import timezone
        
        if not self.is_active:
            return False
        
        now = timezone.localtime()
        
        # Vérifier le jour
        if self.active_days and now.weekday() not in self.active_days:
            return False
        
        # Vérifier l'heure
        if self.active_hours_start and self.active_hours_end:
            current_time = now.time()
            if not (self.active_hours_start <= current_time <= self.active_hours_end):
                return False
        
        return True
    
    def should_trigger(self):
        """Vérifie si l'alerte peut être déclenchée (cooldown)"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.is_in_active_period():
            return False
        
        if not self.last_triggered:
            return True
        
        cooldown_delta = timedelta(minutes=self.cooldown_minutes)
        return timezone.now() - self.last_triggered > cooldown_delta


class Alert(models.Model):
    """Alertes déclenchées"""
    
    STATUS_CHOICES = [
        ('new', 'Nouvelle'),
        ('acknowledged', 'Acquittée'),
        ('resolved', 'Résolue'),
        ('ignored', 'Ignorée'),
    ]
    
    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.SET_NULL,
        null=True,
        related_name='alerts'
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    # Type et sévérité (copiés de la règle pour historique)
    alert_type = models.CharField(max_length=30)
    severity = models.CharField(max_length=20)
    
    # Message
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Données contextuelles
    position = models.ForeignKey(
        'tracking.GPSPosition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    data = models.JSONField(
        default=dict,
        help_text="Données supplémentaires liées à l'alerte"
    )
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Notifications
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    webhook_sent = models.BooleanField(default=False)
    
    # Timestamps
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['user', 'status', '-triggered_at']),
            models.Index(fields=['device', '-triggered_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.triggered_at.strftime('%Y-%m-%d %H:%M')}"
    
    def acknowledge(self, user):
        """Acquitte l'alerte"""
        from django.utils import timezone
        
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save()
    
    def resolve(self):
        """Résout l'alerte"""
        from django.utils import timezone
        
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()


class NotificationLog(models.Model):
    """Journal des notifications envoyées"""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification push'),
        ('webhook', 'Webhook'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyée'),
        ('failed', 'Échouée'),
    ]
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(
        max_length=255,
        help_text="Email, numéro de téléphone ou URL"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Message
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    
    # Réponse
    response = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Journal de notification"
        verbose_name_plural = "Journaux de notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} à {self.recipient} - {self.get_status_display()}"


class MaintenanceReminder(models.Model):
    """Rappels de maintenance pour les véhicules"""
    
    REMINDER_TYPES = [
        ('time', 'Temporel'),
        ('mileage', 'Kilométrage'),
        ('both', 'Temporel et kilométrage'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('completed', 'Effectué'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulé'),
    ]
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='maintenance_reminders'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='maintenance_reminders'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Conditions de déclenchement
    due_date = models.DateField(null=True, blank=True)
    due_mileage = models.IntegerField(
        null=True,
        blank=True,
        help_text="Kilométrage de maintenance en km"
    )
    
    # Notification
    notify_days_before = models.IntegerField(
        default=7,
        help_text="Nombre de jours avant échéance pour notifier"
    )
    notify_km_before = models.IntegerField(
        default=500,
        help_text="Nombre de km avant échéance pour notifier"
    )
    
    last_notification = models.DateTimeField(null=True, blank=True)
    
    # Historique
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_mileage = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rappel de maintenance"
        verbose_name_plural = "Rappels de maintenance"
        ordering = ['due_date', 'due_mileage']
        indexes = [
            models.Index(fields=['device', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.title}"
    
    def mark_completed(self, actual_mileage=None, notes=None):
        """Marque la maintenance comme effectuée"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        if actual_mileage:
            self.actual_mileage = actual_mileage
        if notes:
            self.notes = notes
        self.save()
