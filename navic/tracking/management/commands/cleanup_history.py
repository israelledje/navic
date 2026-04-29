from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from tracking.models import GPSPosition, Trip, Stop
import logging

logger = logging.getLogger('tracking')

class Command(BaseCommand):
    help = "Supprime définitivement l'historique GPS dépassant la limite autorisée par le plan tarifaire de l'utilisateur."

    def handle(self, *args, **options):
        self.stdout.write("Démarrage du nettoyage de l'historique GPS...")
        
        # Récupérer tous les utilisateurs (à l'exception des superusers si on veut garder leurs données indéfiniment)
        users = User.objects.filter(is_superuser=False)
        
        total_positions_deleted = 0
        total_trips_deleted = 0
        total_stops_deleted = 0
        
        for user in users:
            # Récupérer la limite d'historique en jours
            history_days = 30 # Défaut
            if user.billing_package:
                history_days = user.billing_package.history_days
                
            cutoff_date = timezone.now() - timezone.timedelta(days=history_days)
            
            # Cibler les devices de cet utilisateur
            devices = user.devices.all()
            
            if not devices.exists():
                continue
                
            # 1. Supprimer les positions GPS
            # On utilise .filter() puis .delete() qui gère les opérations en lot (bulk) par défaut
            positions_query = GPSPosition.objects.filter(device__in=devices, timestamp__lt=cutoff_date)
            pos_count, _ = positions_query.delete()
            total_positions_deleted += pos_count
            
            # 2. Supprimer les Trajets (Trips)
            trips_query = Trip.objects.filter(device__in=devices, start_time__lt=cutoff_date)
            trips_count, _ = trips_query.delete()
            total_trips_deleted += trips_count
            
            # 3. Supprimer les Arrêts (Stops)
            stops_query = Stop.objects.filter(device__in=devices, start_time__lt=cutoff_date)
            stops_count, _ = stops_query.delete()
            total_stops_deleted += stops_count
            
            if pos_count > 0 or trips_count > 0:
                msg = f"Utilisateur {user.email} (Plan: {history_days} jours) -> Supprimé : {pos_count} positions, {trips_count} trajets, {stops_count} arrêts."
                logger.info(msg)
                self.stdout.write(msg)
        
        # Résumé final
        self.stdout.write(self.style.SUCCESS(
            f"Nettoyage terminé avec succès.\n"
            f"Total supprimé : {total_positions_deleted} positions, {total_trips_deleted} trajets, {total_stops_deleted} arrêts."
        ))
