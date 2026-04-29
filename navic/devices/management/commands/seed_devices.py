from django.core.management.base import BaseCommand
from devices.models import Protocol, DeviceModel

class Command(BaseCommand):
    help = 'Initialise la base de données avec les protocoles et modèles de devices courants (Coban, GT06, Teltonika, etc.)'

    def handle(self, *args, **options):
        # 1. Création des Protocoles
        self.stdout.write("Création des protocoles...")
        
        protocols_data = [
            {'code': 'gt06', 'tcp_port': 5027, 'udp_port': 5027, 'description': 'Protocole standard Concox/GT06'},
            {'code': 'tk103', 'tcp_port': 5028, 'udp_port': 5028, 'description': 'Protocole standard Coban/TK103'},
            {'code': 'teltonika', 'tcp_port': 5029, 'udp_port': 5029, 'description': 'Protocole Teltonika FMB'},
            {'code': 'meitrack', 'tcp_port': 5030, 'udp_port': 5030, 'description': 'Protocole Meitrack'},
        ]
        
        protocol_objs = {}
        for p in protocols_data:
            protocol, created = Protocol.objects.get_or_create(
                code=p['code'],
                defaults={
                    'tcp_port': p['tcp_port'],
                    'udp_port': p['udp_port'],
                    'description': p['description']
                }
            )
            protocol_objs[p['code']] = protocol
            if created:
                self.stdout.write(self.style.SUCCESS(f"Protocole créé: {protocol.code}"))

        # 2. Création des Modèles Physiques (DeviceModel)
        self.stdout.write("Création des modèles physiques (DeviceModels)...")
        
        models_data = [
            # ----- COBAN -----
            {
                'name': 'GPS303F',
                'manufacturer': 'Coban',
                'protocol': protocol_objs['tk103'],
                'description': 'Traceur étanche pour voitures et motos',
                'supported_features': ['engine_cut', 'sos_button', 'door_sensor', 'acc_detection']
            },
            {
                'name': 'GPS303G',
                'manufacturer': 'Coban',
                'protocol': protocol_objs['tk103'],
                'description': 'Traceur étanche avec télécommande',
                'supported_features': ['engine_cut', 'sos_button', 'door_sensor', 'acc_detection', 'remote_control']
            },
            {
                'name': 'TK103A',
                'manufacturer': 'Coban',
                'protocol': protocol_objs['tk103'],
                'description': 'Traceur GPS classique',
                'supported_features': ['engine_cut', 'sos_button', 'mic']
            },
            
            # ----- CONCOX / JIMI (GT06) -----
            {
                'name': 'GT06N',
                'manufacturer': 'Concox',
                'protocol': protocol_objs['gt06'],
                'description': 'Traceur multifonction très populaire',
                'supported_features': ['engine_cut', 'sos_button', 'voice_monitoring', 'acc_detection']
            },
            {
                'name': 'CRX1',
                'manufacturer': 'Concox',
                'protocol': protocol_objs['gt06'],
                'description': 'Traceur compact basique',
                'supported_features': ['engine_cut', 'acc_detection']
            },
            {
                'name': 'WeTrack2',
                'manufacturer': 'Concox',
                'protocol': protocol_objs['gt06'],
                'description': 'Traceur de véhicule basique',
                'supported_features': ['engine_cut', 'acc_detection']
            },
            
            # ----- SINOTRACK (souvent sur GT06 ou port similaire) -----
            {
                'name': 'ST901',
                'manufacturer': 'SinoTrack',
                'protocol': protocol_objs['gt06'], # Souvent configuré comme un clone GT06
                'description': 'Traceur étanche compact à brancher sur batterie',
                'supported_features': ['acc_detection']
            },
            
            # ----- TELTONIKA -----
            {
                'name': 'FMB920',
                'manufacturer': 'Teltonika',
                'protocol': protocol_objs['teltonika'],
                'description': 'Traceur intelligent avec Bluetooth',
                'supported_features': ['engine_cut', 'bluetooth', 'crash_detection', 'towing_detection']
            },
        ]
        
        for m in models_data:
            model, created = DeviceModel.objects.get_or_create(
                name=m['name'],
                defaults={
                    'manufacturer': m['manufacturer'],
                    'protocol': m['protocol'],
                    'description': m['description'],
                    'supported_features': m['supported_features']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Modèle créé: {model.manufacturer} {model.name}"))
        
        self.stdout.write(self.style.SUCCESS("Peuplement terminé avec succès !"))
