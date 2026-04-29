from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class Protocol(models.Model):
    """Protocoles de communication GPS supportés par l'ingestion"""
    
    code = models.CharField(max_length=50, unique=True, help_text="Code du protocole (ex: GT06, TK103) envoyé par l'ingestion")
    tcp_port = models.IntegerField(null=True, blank=True, help_text="Port TCP utilisé par l'ingestion")
    udp_port = models.IntegerField(null=True, blank=True, help_text="Port UDP utilisé par l'ingestion")
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Protocole"
        verbose_name_plural = "Protocoles"
        ordering = ['code']
    
    def __str__(self):
        return self.code


class DeviceModel(models.Model):
    """Modèles de devices GPS"""
    
    name = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=100)
    protocol = models.ForeignKey(Protocol, on_delete=models.PROTECT, related_name='device_models', help_text="Protocole de communication (ex: GT06)")
    description = models.TextField(blank=True, null=True)
    
    # Spécifications techniques
    supported_features = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des fonctionnalités supportées (ex: ['engine_cut', 'sos_button'])"
    )
    
    is_active = models.BooleanField(default=True)
    
    # Capacités
    analog_inputs = models.IntegerField(default=0, help_text="Nombre d'entrées analogiques")
    digital_inputs = models.IntegerField(default=0, help_text="Nombre d'entrées numériques")
    digital_outputs = models.IntegerField(default=0, help_text="Nombre de sorties numériques")
    has_canbus = models.BooleanField(default=False, help_text="Support CANBUS")
    supported_sensors = models.JSONField(
        default=list, 
        blank=True,
        help_text="Liste des capteurs supportés (ex: ['fuel', 'temp', 'door'])"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Modèle de device"
        verbose_name_plural = "Modèles de devices"
        ordering = ['manufacturer', 'name']
    
    def __str__(self):
        return f"{self.manufacturer} {self.name} ({self.protocol})"


class Device(models.Model):
    """Devices GPS des utilisateurs"""
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('maintenance', 'En maintenance'),
        ('lost', 'Perdu'),
        ('deactivated', 'Désactivé'),
    ]
    
    # Validateur pour IMEI
    imei_validator = RegexValidator(
        regex=r'^\d{15}$',
        message="L'IMEI doit contenir exactement 15 chiffres"
    )
    
    # Relations
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='devices'
    )
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.PROTECT,
        related_name='devices'
    )
    
    # Identification
    imei = models.CharField(
        max_length=15,
        unique=True,
        validators=[imei_validator],
        help_text="Numéro IMEI du device (15 chiffres)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Nom personnalisé du device"
    )
    description = models.TextField(blank=True, null=True)
    
    # Informations du véhicule/objet suivi
    vehicle_plate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Plaque d'immatriculation"
    )
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type de véhicule (voiture, moto, camion, etc.)"
    )
    vehicle_brand = models.CharField(max_length=50, blank=True, null=True)
    vehicle_model = models.CharField(max_length=50, blank=True, null=True)
    vehicle_color = models.CharField(max_length=30, blank=True, null=True)
    vehicle_year = models.IntegerField(blank=True, null=True)
    
    # État et configuration
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    icon = models.CharField(
        max_length=50,
        default='car',
        help_text="Icône à afficher sur la carte"
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Couleur en hexadécimal"
    )
    
    # Connexion
    last_connection = models.DateTimeField(null=True, blank=True)
    last_position = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dernière position connue (lat, lng, etc.)"
    )
    is_online = models.BooleanField(default=False)
    
    # Configuration avancée
    update_interval = models.IntegerField(
        default=60,
        help_text="Intervalle de mise à jour en secondes"
    )
    speed_limit = models.IntegerField(
        default=0,
        help_text="Limite de vitesse pour les alertes (km/h)"
    )
    
    # Groupes (pour la gestion de flotte)
    groups = models.ManyToManyField(
        'fleet.DeviceGroup',
        blank=True,
        related_name='devices'
    )
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    installation_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['imei']),
            models.Index(fields=['is_online']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.imei})"
    
    def is_active_device(self):
        """Vérifie si le device est actif"""
        return self.status == 'active'
    
    def get_protocol(self):
        """Retourne le protocole du device"""
        return self.device_model.protocol.code


class DeviceCommand(models.Model):
    """Commandes envoyées aux devices"""
    
    COMMAND_TYPES = [
        ('locate', 'Localisation'),
        ('reboot', 'Redémarrage'),
        ('set_interval', 'Définir intervalle'),
        ('set_apn', 'Configurer APN'),
        ('engine_stop', 'Arrêt moteur'),
        ('engine_resume', 'Reprise moteur'),
        ('custom', 'Personnalisée'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyée'),
        ('delivered', 'Délivrée'),
        ('executed', 'Exécutée'),
        ('failed', 'Échouée'),
        ('timeout', 'Expirée'),
    ]
    
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='commands'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='device_commands'
    )
    
    command_type = models.CharField(max_length=50, choices=COMMAND_TYPES)
    command_data = models.JSONField(
        default=dict,
        help_text="Paramètres de la commande"
    )
    raw_command = models.TextField(
        blank=True,
        null=True,
        help_text="Commande brute envoyée au device"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Réponse du device
    response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'expiration de la commande"
    )
    
    class Meta:
        verbose_name = "Commande device"
        verbose_name_plural = "Commandes devices"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.get_command_type_display()} ({self.get_status_display()})"


class DeviceSettings(models.Model):
    """Paramètres de configuration des devices"""
    
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name='settings',
        primary_key=True
    )
    
    # Configuration réseau
    device_plan = models.ForeignKey(
        'billing.DeviceTariffPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings',
        help_text="Plan tarifaire associé au device"
    )
    apn = models.CharField(max_length=100, blank=True, null=True)
    apn_user = models.CharField(max_length=100, blank=True, null=True)
    apn_password = models.CharField(max_length=100, blank=True, null=True)
    
    # Numéros de téléphone autorisés
    authorized_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des numéros autorisés à envoyer des SMS au device"
    )
    
    # Paramètres de reporting
    reporting_interval_moving = models.IntegerField(
        default=60,
        help_text="Intervalle en mouvement (secondes)"
    )
    reporting_interval_stopped = models.IntegerField(
        default=300,
        help_text="Intervalle à l'arrêt (secondes)"
    )
    
    # Fuseau horaire
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="Fuseau horaire du device (ex: 'Africa/Douala')"
    )
    
    # Détection de stationnement / Ralenti
    idling_threshold = models.IntegerField(
        default=5,
        help_text="Durée du moteur au ralenti avant alerte (minutes)"
    )
    idling_speed_limit = models.IntegerField(
        default=3,
        help_text="Vitesse max considérée comme ralenti (km/h)"
    )
    
    # État de connexion
    offline_timeout = models.IntegerField(
        default=10,
        help_text="Délai avant de considérer le device hors ligne (minutes)"
    )

    # Capteurs et IO
    fuel_sensor_enabled = models.BooleanField(default=False)
    temperature_sensor_enabled = models.BooleanField(default=False)
    door_sensor_enabled = models.BooleanField(default=False)
    
    # Configuration avancée
    custom_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Paramètres personnalisés spécifiques au modèle"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paramètres device"
        verbose_name_plural = "Paramètres devices"
    
    def __str__(self):
        return f"Paramètres de {self.device.name}"
