import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.cache import cache


class DeviceTrackingConsumer(AsyncWebsocketConsumer):
    """Consumer pour le tracking en temps réel d'un device spécifique"""
    
    async def connect(self):
        self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.room_group_name = f'device_{self.device_id}'
        
        # Vérifier que l'utilisateur a accès à ce device
        has_access = await self.check_device_access()
        
        if not has_access:
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer la dernière position connue
        last_position = await self.get_last_position()
        if last_position:
            await self.send(text_data=json.dumps({
                'type': 'last_position',
                'data': last_position
            }))
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du client"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'request_position':
            # Client demande une mise à jour de position
            last_position = await self.get_last_position()
            await self.send(text_data=json.dumps({
                'type': 'position_update',
                'data': last_position
            }))
    
    async def position_update(self, event):
        """Recevoir une mise à jour de position du groupe"""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event['data']
        }))
    
    async def device_status(self, event):
        """Recevoir une mise à jour du statut du device"""
        await self.send(text_data=json.dumps({
            'type': 'device_status',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def check_device_access(self):
        """Vérifie si l'utilisateur a accès au device"""
        from devices.models import Device
        from accounts.models import SubAccountPermission
        
        user = self.scope['user']
        if not user.is_authenticated:
            return False
        
        try:
            device = Device.objects.get(id=self.device_id)
            
            # Propriétaire ou admin
            if device.owner == user or user.is_superuser:
                return True
            
            # Sous-compte avec permission
            if user.is_sub_account():
                permission = SubAccountPermission.objects.filter(
                    sub_account=user,
                    device=device
                ).first()
                return permission and permission.has_permission('track')
            
            return False
        except Device.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_last_position(self):
        """Récupère la dernière position du device (depuis le cache ou DB)"""
        from devices.models import Device
        from tracking.models import GPSPosition
        
        try:
            device = Device.objects.get(id=self.device_id)
            
            # Essayer de récupérer depuis le cache d'abord
            cached_pos = cache.get(f"device_last_pos:{device.id}")
            is_online = cache.get(f"device_online:{device.id}", device.is_online)
            
            if cached_pos:
                return {
                    'device_id': device.id,
                    'device_name': device.name,
                    'latitude': cached_pos['lat'],
                    'longitude': cached_pos['lng'],
                    'altitude': cached_pos.get('altitude'),
                    'speed': cached_pos['speed'],
                    'heading': cached_pos.get('heading'),
                    'satellites': cached_pos.get('satellites'),
                    'ignition': cached_pos.get('ignition'),
                    'battery_level': cached_pos.get('battery'),
                    'external_power': cached_pos.get('external_power'),
                    'odometer': cached_pos.get('odometer'),
                    'signal': cached_pos.get('signal'),
                    'timestamp': cached_pos['timestamp'],
                    'is_online': is_online,
                }

            # Fallback sur la DB si non trouvé en cache
            last_position = GPSPosition.objects.filter(
                device=device
            ).order_by('-timestamp').first()
            
            if last_position:
                return {
                    'device_id': device.id,
                    'device_name': device.name,
                    'latitude': last_position.latitude,
                    'longitude': last_position.longitude,
                    'altitude': last_position.altitude,
                    'speed': last_position.speed,
                    'heading': last_position.heading,
                    'satellites': last_position.satellites,
                    'ignition': last_position.ignition,
                    'battery_level': last_position.battery_level,
                    'external_power': last_position.external_power,
                    'odometer': last_position.odometer,
                    'signal': last_position.signal_strength,
                    'timestamp': last_position.timestamp.isoformat(),
                    'is_online': device.is_online,
                }
            
            return None
        except Device.DoesNotExist:
            return None


class UserTrackingConsumer(AsyncWebsocketConsumer):
    """Consumer pour le tracking en temps réel de tous les devices d'un utilisateur"""
    
    async def connect(self):
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'user_{user.id}'
        
        # Rejoindre le groupe utilisateur
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer toutes les dernières positions
        devices_positions = await self.get_all_devices_positions()
        await self.send(text_data=json.dumps({
            'type': 'initial_positions',
            'data': devices_positions
        }))
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du client"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'request_positions':
            # Client demande une mise à jour de toutes les positions
            devices_positions = await self.get_all_devices_positions()
            await self.send(text_data=json.dumps({
                'type': 'positions_update',
                'data': devices_positions
            }))
    
    async def position_update(self, event):
        """Recevoir une mise à jour de position"""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event['data']
        }))
    
    async def devices_status(self, event):
        """Recevoir une mise à jour des statuts"""
        await self.send(text_data=json.dumps({
            'type': 'devices_status',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_all_devices_positions(self):
        """Récupère les dernières positions de tous les devices de l'utilisateur (via Cache)"""
        from devices.models import Device
        from tracking.models import GPSPosition
        
        user = self.scope['user']
        devices = Device.objects.filter(owner=user, status='active')
        
        positions_data = []
        
        for device in devices:
            # Tenter le cache
            cached_pos = cache.get(f"device_last_pos:{device.id}")
            is_online = cache.get(f"device_online:{device.id}", device.is_online)
            
            if cached_pos:
                positions_data.append({
                    'device_id': device.id,
                    'device_name': device.name,
                    'latitude': cached_pos['lat'],
                    'longitude': cached_pos['lng'],
                    'speed': cached_pos['speed'],
                    'ignition': cached_pos.get('ignition'),
                    'battery_level': cached_pos.get('battery'),
                    'timestamp': cached_pos['timestamp'],
                    'is_online': is_online,
                    'icon': device.icon,
                    'color': device.color,
                })
            else:
                # Fallback DB
                last_position = GPSPosition.objects.filter(device=device).order_by('-timestamp').first()
                if last_position:
                    positions_data.append({
                        'device_id': device.id,
                        'device_name': device.name,
                        'latitude': last_position.latitude,
                        'longitude': last_position.longitude,
                        'speed': last_position.speed,
                        'ignition': last_position.ignition,
                        'battery_level': last_position.battery_level,
                        'timestamp': last_position.timestamp.isoformat(),
                        'is_online': device.is_online,
                        'icon': device.icon,
                        'color': device.color,
                    })
        
        return positions_data


class AlertConsumer(AsyncWebsocketConsumer):
    """Consumer pour les alertes en temps réel"""
    
    async def connect(self):
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'alerts_{user.id}'
        
        # Rejoindre le groupe d'alertes
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les alertes non acquittées
        unacknowledged_alerts = await self.get_unacknowledged_alerts()
        await self.send(text_data=json.dumps({
            'type': 'unacknowledged_alerts',
            'data': unacknowledged_alerts
        }))
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du client"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'acknowledge_alert':
            alert_id = text_data_json.get('alert_id')
            await self.acknowledge_alert(alert_id)
    
    async def new_alert(self, event):
        """Recevoir une nouvelle alerte"""
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'data': event['data']
        }))
    
    async def alert_acknowledged(self, event):
        """Alerte acquittée"""
        await self.send(text_data=json.dumps({
            'type': 'alert_acknowledged',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_unacknowledged_alerts(self):
        """Récupère les alertes non acquittées"""
        from alerts.models import Alert
        
        user = self.scope['user']
        alerts = Alert.objects.filter(
            user=user,
            status='new'
        ).order_by('-triggered_at')[:20]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity,
                'device_id': alert.device.id,
                'device_name': alert.device.name,
                'triggered_at': alert.triggered_at.isoformat(),
            })
        
        return alerts_data
    
    @database_sync_to_async
    def acknowledge_alert(self, alert_id):
        """Acquitte une alerte"""
        from alerts.models import Alert
        
        user = self.scope['user']
        
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
            alert.acknowledge(user)
            return True
        except Alert.DoesNotExist:
            return False
