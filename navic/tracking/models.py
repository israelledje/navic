from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GinIndex


class GPSPosition(models.Model):
    """Positions GPS reçues des devices"""
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='positions',
        db_index=True
    )
    
    # Données GPS
    latitude = models.FloatField(help_text="Latitude en degrés décimaux")
    longitude = models.FloatField(help_text="Longitude en degrés décimaux")
    altitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Altitude en mètres"
    )
    speed = models.FloatField(
        default=0.0,
        help_text="Vitesse en km/h"
    )
    heading = models.FloatField(
        null=True,
        blank=True,
        help_text="Direction en degrés (0-360)"
    )
    
    # Qualité du signal
    satellites = models.IntegerField(
        null=True,
        blank=True,
        help_text="Nombre de satellites"
    )
    hdop = models.FloatField(
        null=True,
        blank=True,
        help_text="Horizontal Dilution of Precision"
    )
    signal_strength = models.IntegerField(
        null=True,
        blank=True,
        help_text="Force du signal GSM en pourcentage (0-100)"
    )
    
    # État du véhicule
    ignition = models.BooleanField(
        null=True,
        blank=True,
        help_text="État du contact"
    )
    battery_level = models.IntegerField(
        null=True,
        blank=True,
        help_text="Niveau de batterie en pourcentage"
    )
    external_power = models.FloatField(
        null=True,
        blank=True,
        help_text="Tension alimentation externe en volts"
    )
    
    # Odomètre et carburant
    odometer = models.FloatField(
        null=True,
        blank=True,
        help_text="Kilométrage total en km"
    )
    fuel_level = models.FloatField(
        null=True,
        blank=True,
        help_text="Niveau de carburant en %"
    )
    
    # Températures
    temperature_1 = models.FloatField(null=True, blank=True)
    temperature_2 = models.FloatField(null=True, blank=True)
    
    # IO et capteurs
    io_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données des entrées/sorties (portes, capteurs, etc.)"
    )
    
    # Métadonnées
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Timestamp de la position GPS"
    )
    server_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de réception par le serveur"
    )
    protocol = models.CharField(max_length=20, blank=True, null=True)
    raw_data = models.TextField(
        blank=True,
        null=True,
        help_text="Données brutes reçues"
    )
    
    # Statut de traitement
    is_processed = models.BooleanField(
        default=False,
        help_text="Position traitée pour alertes et rapports"
    )
    
    class Meta:
        verbose_name = "Position GPS"
        verbose_name_plural = "Positions GPS"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['-server_time']),
            models.Index(fields=['is_processed']),
        ]
        # Partition potentielle par mois pour optimisation
        
    def __str__(self):
        return f"{self.device.name} - {self.timestamp}"
    
    def get_location(self):
        """Retourne la position sous forme de dictionnaire"""
        return {
            'lat': self.latitude,
            'lng': self.longitude,
            'alt': self.altitude,
        }
    
    def is_moving(self):
        """Vérifie si le véhicule est en mouvement"""
        return self.speed > 5  # Seuil de 5 km/h


class Trip(models.Model):
    """Trajets effectués par les devices"""
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='trips'
    )
    
    # Points du trajet
    start_position = models.ForeignKey(
        GPSPosition,
        on_delete=models.SET_NULL,
        null=True,
        related_name='trips_started'
    )
    end_position = models.ForeignKey(
        GPSPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips_ended'
    )
    
    # Informations temporelles
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True, db_index=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Adresses (géocodage inversé)
    start_address = models.TextField(blank=True, null=True)
    end_address = models.TextField(blank=True, null=True)
    
    # Statistiques du trajet
    distance_km = models.FloatField(
        default=0.0,
        help_text="Distance totale en km"
    )
    max_speed = models.FloatField(
        default=0.0,
        help_text="Vitesse maximale en km/h"
    )
    avg_speed = models.FloatField(
        default=0.0,
        help_text="Vitesse moyenne en km/h"
    )
    
    # Consommation (si disponible)
    fuel_consumed = models.FloatField(
        null=True,
        blank=True,
        help_text="Consommation de carburant en litres"
    )
    
    # État
    is_completed = models.BooleanField(default=False)
    
    # Résumé du trajet
    summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Résumé incluant arrêts, vitesses, etc."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trajet"
        verbose_name_plural = "Trajets"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['device', '-start_time']),
            models.Index(fields=['is_completed']),
        ]
    
    def __str__(self):
        status = "En cours" if not self.is_completed else "Terminé"
        return f"{self.device.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({status})"
    
    def calculate_duration(self):
        """Calcule la durée du trajet"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
            return self.duration_seconds
        return None


class Stop(models.Model):
    """Arrêts détectés pendant les trajets"""
    
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='stops',
        null=True,
        blank=True
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='stops'
    )
    
    # Position de l'arrêt
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True, null=True)
    
    # Temps
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # Contact
    ignition_off = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Arrêt"
        verbose_name_plural = "Arrêts"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['device', '-start_time']),
            models.Index(fields=['trip']),
        ]
    
    def __str__(self):
        duration_min = self.duration_seconds // 60
        return f"Arrêt de {duration_min} min - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class Geofence(models.Model):
    """Zones géographiques définies par l'utilisateur"""
    
    SHAPE_TYPES = [
        ('circle', 'Cercle'),
        ('polygon', 'Polygone'),
        ('rectangle', 'Rectangle'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='geofences'
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Géométrie
    shape_type = models.CharField(max_length=20, choices=SHAPE_TYPES)
    
    # Pour cercle
    center_lat = models.FloatField(null=True, blank=True)
    center_lng = models.FloatField(null=True, blank=True)
    radius_meters = models.FloatField(null=True, blank=True)
    
    # Pour polygone/rectangle
    coordinates = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste de coordonnées [[lat, lng], ...]"
    )
    
    # Configuration
    color = models.CharField(max_length=7, default='#FF0000')
    is_active = models.BooleanField(default=True)
    
    # Devices concernés
    devices = models.ManyToManyField(
        'devices.Device',
        blank=True,
        related_name='geofences'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Géofence"
        verbose_name_plural = "Géofences"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GeofenceEvent(models.Model):
    """Événements d'entrée/sortie de géofence"""
    
    EVENT_TYPES = [
        ('enter', 'Entrée'),
        ('exit', 'Sortie'),
    ]
    
    geofence = models.ForeignKey(
        Geofence,
        on_delete=models.CASCADE,
        related_name='events'
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='geofence_events'
    )
    position = models.ForeignKey(
        GPSPosition,
        on_delete=models.SET_NULL,
        null=True
    )
    
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Notification
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Événement géofence"
        verbose_name_plural = "Événements géofence"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['geofence', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.get_event_type_display()} {self.geofence.name}"


class Report(models.Model):
    """Rapports générés par les utilisateurs"""
    
    REPORT_TYPES = [
        ('daily', 'Rapport journalier'),
        ('weekly', 'Rapport hebdomadaire'),
        ('monthly', 'Rapport mensuel'),
        ('custom', 'Rapport personnalisé'),
        ('trip', 'Rapport de trajet'),
        ('fuel', 'Rapport de carburant'),
        ('speed', 'Rapport de vitesse'),
        ('stops', 'Rapport d\'arrêts'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    devices = models.ManyToManyField(
        'devices.Device',
        related_name='reports'
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Période
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Résultats
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données du rapport"
    )
    file_path = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True,
        help_text="Fichier PDF/Excel généré"
    )
    
    # Métadonnées
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
