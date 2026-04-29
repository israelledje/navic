from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import AlertRule, Alert, MaintenanceReminder
from .serializers import (
    AlertRuleSerializer, AlertSerializer, 
    MaintenanceReminderSerializer
)

class AlertRuleViewSet(viewsets.ModelViewSet):
    """
    Configuration des règles d'alertes
    """
    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historique des alertes déclenchées
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(device__owner=self.request.user).order_by('-triggered_at')

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Marquer l'alerte comme lue/acquittée"""
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response({'status': 'alerte acquittée'})

class MaintenanceReminderViewSet(viewsets.ModelViewSet):
    """
    Gestion des rappels de maintenance
    """
    serializer_class = MaintenanceReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MaintenanceReminder.objects.filter(device__owner=self.request.user)
