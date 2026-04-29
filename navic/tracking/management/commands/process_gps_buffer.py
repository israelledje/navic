import json
import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_redis import get_redis_connection
from tracking.models import GPSPosition
from devices.models import Device

logger = logging.getLogger('tracking')

class Command(BaseCommand):
    help = 'Traite le buffer de positions GPS dans Redis et les insère par lots dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Nombre maximum de positions à insérer par lot'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalle entre chaque traitement en secondes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch-size']
        interval = options['interval']
        
        self.stdout.write(self.style.SUCCESS(f"Démarrage du processeur de buffer GPS (Intervalle: {interval}s, Batch: {batch_size})"))
        
        redis_conn = get_redis_connection("default")
        
        while True:
            try:
                # 1. Récupérer les données du buffer
                # On utilise une transaction atomique pour vider une partie de la liste
                positions_batch = []
                
                # Récupérer jusqu'à batch_size éléments
                # L'utilisation de pipeline permet d'optimiser les échanges avec Redis
                pipe = redis_conn.pipeline()
                for _ in range(batch_size):
                    pipe.rpop("gps_position_buffer")
                
                raw_positions = pipe.execute()
                
                # Filtrer les valeurs None (quand la liste est vide)
                raw_positions = [p for p in raw_positions if p is not None]
                
                if not raw_positions:
                    time.sleep(2) # Attendre un peu si le buffer est vide
                    continue
                
                self.stdout.write(f"Traitement de {len(raw_positions)} positions...")
                
                # 2. Préparer les objets GPSPosition
                gps_objects = []
                device_cache = {} # Cache local pour éviter les requêtes répétées sur Device
                
                for raw_data in raw_positions:
                    try:
                        data = json.loads(raw_data)
                        device_id = data.get('device_id')
                        
                        if device_id not in device_cache:
                            device_cache[device_id] = Device.objects.get(id=device_id)
                        
                        device = device_cache[device_id]
                        
                        # Création de l'objet (sans sauvegarde)
                        gps_objects.append(GPSPosition(
                            device=device,
                            latitude=data.get('latitude', 0.0),
                            longitude=data.get('longitude', 0.0),
                            altitude=data.get('altitude'),
                            speed=data.get('speed', 0.0),
                            heading=data.get('heading'),
                            satellites=data.get('satellites'),
                            battery_level=data.get('battery_level'),
                            signal_strength=data.get('signal_strength'),
                            ignition=data.get('ignition'),
                            external_power=data.get('external_power'),
                            odometer=data.get('odometer'),
                            fuel_level=data.get('fuel_level'),
                            io_data=data.get('io_data', {}),
                            timestamp=data.get('timestamp'),
                            protocol=data.get('protocol'),
                            raw_data=data.get('raw_data'),
                        ))
                    except Exception as e:
                        self.stderr.write(f"Erreur formatage position: {e}")
                
                # 3. Insertion par lot (Bulk Create)
                if gps_objects:
                    GPSPosition.objects.bulk_create(gps_objects)
                    self.stdout.write(self.style.SUCCESS(f"Insertion réussie de {len(gps_objects)} positions."))
                
                # Pause avant le prochain cycle
                time.sleep(interval)
                
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Erreur processeur buffer: {e}"))
                time.sleep(5)
