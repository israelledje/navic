from django.core.management.base import BaseCommand
from devices.models import DeviceModel

class Command(BaseCommand):
    help = 'Populate database with common GPS tracker models'

    def handle(self, *args, **options):
        models_data = [
            # Teltonika (Protocol FMXXXX)
            {
                "name": "FMB920", "manufacturer": "Teltonika", "protocol": "FMXXXX",
                "capabilities": {
                    "analog_inputs": 1, "digital_inputs": 1, "digital_outputs": 1,
                    "supported_sensors": ["acc", "door", "tow"]
                }
            },
            {
                "name": "FMB120", "manufacturer": "Teltonika", "protocol": "FMXXXX",
                "capabilities": {
                    "analog_inputs": 2, "digital_inputs": 3, "digital_outputs": 2,
                    "supported_sensors": ["acc", "door", "fuel", "temp", "ibutton"]
                }
            },
            {
                "name": "FMB140", "manufacturer": "Teltonika", "protocol": "FMXXXX",
                "capabilities": { # Avec CANBUS intégré
                    "analog_inputs": 2, "digital_inputs": 3, "digital_outputs": 2,
                    "has_canbus": True,
                    "supported_sensors": ["acc", "door", "fuel", "temp", "canbus_fuel", "canbus_rpm"]
                }
            },
            {
                "name": "FMB640", "manufacturer": "Teltonika", "protocol": "FMXXXX",
                "capabilities": { # Haut de gamme
                    "analog_inputs": 4, "digital_inputs": 4, "digital_outputs": 4,
                    "has_canbus": True,
                    "supported_sensors": ["acc", "door", "fuel", "temp", "tachograph", "rfid"]
                }
            },
            
            # Coban (Protocol TK103)
            {
                "name": "GPS103A", "manufacturer": "Coban", "protocol": "TK103",
                "capabilities": {"analog_inputs": 0, "digital_inputs": 2, "digital_outputs": 1, "supported_sensors": ["acc", "door"]}
            },
            {
                "name": "GPS303F", "manufacturer": "Coban", "protocol": "TK103",
                "capabilities": {"analog_inputs": 1, "digital_inputs": 1, "digital_outputs": 1, "supported_sensors": ["acc", "fuel", "oil_cut"]}
            },
            
            # Concox (Protocol GT06)
            {
                "name": "GT06N", "manufacturer": "Concox", "protocol": "GT06",
                "capabilities": {"analog_inputs": 0, "digital_inputs": 1, "digital_outputs": 1, "supported_sensors": ["acc", "sos", "mic"]}
            },
             {
                "name": "WeTrack2", "manufacturer": "Concox", "protocol": "GT06",
                "capabilities": {"analog_inputs": 0, "digital_inputs": 1, "digital_outputs": 1, "supported_sensors": ["acc", "relay"]}
            },
        ]
        
        count = 0
        count = 0
        for data in models_data:
            obj, created = DeviceModel.objects.update_or_create(
                name=data['name'],
                defaults={
                    'manufacturer': data['manufacturer'],
                    'protocol': data['protocol'],
                    'description': f"{data['manufacturer']} {data['name']} standard tracker",
                    'analog_inputs': data['capabilities'].get('analog_inputs', 0),
                    'digital_inputs': data['capabilities'].get('digital_inputs', 0),
                    'digital_outputs': data['capabilities'].get('digital_outputs', 0),
                    'has_canbus': data['capabilities'].get('has_canbus', False),
                    'supported_sensors': data['capabilities'].get('supported_sensors', []),
                }
            )
            if created:
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully added {count} device models'))
