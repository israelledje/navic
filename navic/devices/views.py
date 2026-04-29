from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import DeviceModel, Device, DeviceCommand, DeviceSettings
from .serializers import (
    DeviceModelSerializer, DeviceSerializer, DeviceListSerializer,
    DeviceCreateSerializer, DeviceSettingsSerializer,
    DeviceCommandSerializer, DeviceCommandCreateSerializer
)

class DeviceModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catalogue des modèles de devices supportés (Lecture seule pour les utilisateurs)
    """
    queryset = DeviceModel.objects.all()
    serializer_class = DeviceModelSerializer
    permission_classes = [permissions.IsAuthenticated]

class DeviceViewSet(viewsets.ModelViewSet):
    """
    Gestion des trackers GPS appartenant à l'utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Device.objects.all()
        
        # Un utilisateur voit ses propres appareils et ceux pour lesquels il a une permission
        return Device.objects.filter(
            Q(owner=user) | 
            Q(sub_account_permissions__sub_account=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return DeviceListSerializer
        if self.action == 'create':
            return DeviceCreateSerializer
        return DeviceSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get', 'patch', 'put'], url_path='settings')
    def device_settings(self, request, pk=None):
        """Récupérer ou mettre à jour les réglages spécifiques du device"""
        device = self.get_object()
        settings_obj, created = DeviceSettings.objects.get_or_create(device=device)
        
        if request.method in ['PATCH', 'PUT']:
            serializer = DeviceSettingsSerializer(settings_obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = DeviceSettingsSerializer(settings_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_command(self, request, pk=None):
        """Envoyer une commande GPRS/SMS au device"""
        device = self.get_object()
        serializer = DeviceCommandCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Enregistrer la commande en base
        command = serializer.save(
            device=device,
            user=request.user,
            status='pending'
        )
        
        # TODO: Ici on appellerait le service Go ou un worker Celery 
        # pour envoyer réellement la commande au device via TCP/SMS
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DeviceCommandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historique des commandes envoyées
    """
    serializer_class = DeviceCommandSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return DeviceCommand.objects.all().order_by('-created_at')
            
        return DeviceCommand.objects.filter(
            Q(device__owner=user) | 
            Q(device__sub_account_permissions__sub_account=user)
        ).distinct().order_by('-created_at')
