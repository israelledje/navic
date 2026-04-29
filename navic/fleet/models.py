from django.db import models
from django.utils.translation import gettext_lazy as _


class DeviceGroup(models.Model):
    """Groupes de devices pour la gestion de flotte"""
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='device_groups'
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Couleur en hexadécimal"
    )
    icon = models.CharField(max_length=50, default='folder')
    
    # Hiérarchie (groupe parent optionnel)
    parent_group = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subgroups'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Groupe de devices"
        verbose_name_plural = "Groupes de devices"
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return self.name
    
    def get_all_devices(self):
        """Retourne tous les devices du groupe et des sous-groupes"""
        from devices.models import Device
        
        device_ids = set(self.devices.values_list('id', flat=True))
        
        # Récupérer récursivement les devices des sous-groupes
        for subgroup in self.subgroups.all():
            device_ids.update(subgroup.get_all_devices().values_list('id', flat=True))
        
        return Device.objects.filter(id__in=device_ids)


class Driver(models.Model):
    """Conducteurs assignés aux véhicules"""
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='drivers'
    )
    
    # Informations personnelles
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Numéro d'employé"
    )
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(
        upload_to='drivers/',
        blank=True,
        null=True
    )
    
    # Informations du permis
    license_number = models.CharField(max_length=50, blank=True, null=True)
    license_category = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Catégorie du permis (A, B, C, D, E)"
    )
    license_expiry = models.DateField(null=True, blank=True)
    
    # Adresse
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    
    # RFID/iButton pour identification
    rfid_tag = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Tag RFID ou iButton du conducteur"
    )
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['rfid_tag']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class DriverAssignment(models.Model):
    """Assignation des conducteurs aux véhicules"""
    
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='driver_assignments'
    )
    
    # Période d'assignation
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Détection automatique (via RFID) ou manuelle
    is_auto_detected = models.BooleanField(default=False)
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Assignation conducteur"
        verbose_name_plural = "Assignations conducteurs"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['driver', '-start_time']),
            models.Index(fields=['device', '-start_time']),
        ]
    
    def __str__(self):
        return f"{self.driver.get_full_name()} - {self.device.name}"
    
    def is_current(self):
        """Vérifie si l'assignation est en cours"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.end_time:
            return self.start_time <= now <= self.end_time
        return self.start_time <= now


class FuelEntry(models.Model):
    """Entrées de carburant"""
    
    FUEL_TYPES = [
        ('gasoline', 'Essence'),
        ('diesel', 'Diesel'),
        ('lpg', 'GPL'),
        ('electric', 'Électrique'),
        ('hybrid', 'Hybride'),
    ]
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='fuel_entries'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_entries'
    )
    
    # Détails du plein
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    quantity_liters = models.FloatField(help_text="Quantité en litres")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Coût total"
    )
    price_per_liter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='XAF')
    
    # Contexte
    odometer_reading = models.IntegerField(
        help_text="Kilométrage au moment du plein"
    )
    is_full_tank = models.BooleanField(
        default=True,
        help_text="Plein complet ou partiel"
    )
    
    # Lieu
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Document
    receipt = models.ImageField(
        upload_to='fuel_receipts/',
        blank=True,
        null=True
    )
    
    # Timestamp
    filled_at = models.DateTimeField(help_text="Date et heure du plein")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Entrée carburant"
        verbose_name_plural = "Entrées carburant"
        ordering = ['-filled_at']
        indexes = [
            models.Index(fields=['device', '-filled_at']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.quantity_liters}L le {self.filled_at.strftime('%Y-%m-%d')}"
    
    def calculate_consumption(self):
        """Calcule la consommation moyenne depuis le dernier plein"""
        previous_entry = FuelEntry.objects.filter(
            device=self.device,
            filled_at__lt=self.filled_at,
            is_full_tank=True
        ).order_by('-filled_at').first()
        
        if previous_entry and self.is_full_tank:
            distance = self.odometer_reading - previous_entry.odometer_reading
            if distance > 0:
                # Consommation en L/100km
                consumption = (self.quantity_liters / distance) * 100
                return round(consumption, 2)
        
        return None


class MaintenanceRecord(models.Model):
    """Historique de maintenance des véhicules"""
    
    MAINTENANCE_TYPES = [
        ('oil_change', 'Vidange'),
        ('filter_change', 'Changement filtres'),
        ('tire_change', 'Changement pneus'),
        ('brake_service', 'Révision freins'),
        ('battery_replacement', 'Remplacement batterie'),
        ('inspection', 'Contrôle technique'),
        ('repair', 'Réparation'),
        ('other', 'Autre'),
    ]
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='maintenance_records'
    )
    
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Contexte
    odometer_reading = models.IntegerField(
        help_text="Kilométrage au moment de la maintenance"
    )
    
    # Coûts
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Coût de la main d'œuvre"
    )
    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Coût des pièces"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Coût total"
    )
    currency = models.CharField(max_length=3, default='XAF')
    
    # Prestataire
    service_provider = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Garage ou prestataire"
    )
    
    # Documents
    invoice = models.FileField(
        upload_to='maintenance_invoices/',
        blank=True,
        null=True
    )
    
    # Dates
    service_date = models.DateField()
    next_service_date = models.DateField(null=True, blank=True)
    next_service_mileage = models.IntegerField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enregistrement de maintenance"
        verbose_name_plural = "Enregistrements de maintenance"
        ordering = ['-service_date']
        indexes = [
            models.Index(fields=['device', '-service_date']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.get_maintenance_type_display()} ({self.service_date})"


class FleetStatistics(models.Model):
    """Statistiques agrégées de la flotte (calculées quotidiennement)"""
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='fleet_statistics'
    )
    group = models.ForeignKey(
        DeviceGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='statistics'
    )
    
    # Période
    date = models.DateField(db_index=True)
    
    # Statistiques globales
    total_devices = models.IntegerField(default=0)
    active_devices = models.IntegerField(default=0)
    total_distance_km = models.FloatField(default=0.0)
    total_fuel_liters = models.FloatField(default=0.0)
    total_fuel_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    
    # Utilisation
    total_engine_hours = models.FloatField(default=0.0)
    total_idle_hours = models.FloatField(default=0.0)
    
    # Alertes
    total_alerts = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    
    # Données détaillées par device
    device_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Statistiques détaillées par device"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Statistique de flotte"
        verbose_name_plural = "Statistiques de flotte"
        ordering = ['-date']
        unique_together = ['user', 'group', 'date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['group', '-date']),
        ]
    
    def __str__(self):
        group_name = self.group.name if self.group else "Toute la flotte"
        return f"{group_name} - {self.date}"
