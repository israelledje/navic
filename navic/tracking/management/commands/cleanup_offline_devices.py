from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from devices.models import Device
from tracking.views import broadcast_device_status
import logging

logger = logging.getLogger('tracking')

class Command(BaseCommand):
    help = 'Marque les devices comme offline après une période d\'inactivité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=10,
            help='Timeout en minutes avant de considérer un device comme offline'
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout']
        threshold = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Trouver les devices en ligne qui n'ont pas communiqué depuis le threshold
        offline_devices = Device.objects.filter(
            is_online=True,
            last_connection__lt=threshold
        )
        
        count = offline_devices.count()
        for device in offline_devices:
            device.is_online = False
            device.save(update_fields=['is_online'])
            
            # Diffuser le changement de statut via WebSocket
            try:
                broadcast_device_status(device)
            except Exception as e:
                self.stderr.write(f"Erreur broadcast pour {device.imei}: {e}")
            
            self.stdout.write(self.style.SUCCESS(f"Device {device.imei} marqué offline"))
            
        if count > 0:
            logger.info(f"{count} devices marqués comme offline par le cleanup automatique")
        else:
            self.stdout.write("Aucun device à marquer offline")
