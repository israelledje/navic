from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import BillingPackage, DeviceTariffPlan, Subscription, Payment, Invoice
from .serializers import (
    BillingPackageSerializer, DeviceTariffPlanSerializer, SubscriptionSerializer, 
    PaymentSerializer, InvoiceSerializer
)

class DeviceTariffPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catalogue des plans tarifaires pour devices
    """
    queryset = DeviceTariffPlan.objects.filter(is_active=True)
    serializer_class = DeviceTariffPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class BillingPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catalogue des forfaits disponibles (Lecture seule)
    """
    queryset = BillingPackage.objects.filter(is_active=True)
    serializer_class = BillingPackageSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Gestion des abonnements
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    Suivi des paiements effectués
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def process_mobile_money(self, request):
        """Endpoint expérimental pour initier un paiement mobile money"""
        # TODO: Intégrer API de paiement externe (Stripe, FedaPay, etc.)
        return Response({'status': 'paiement initié'}, status=status.HTTP_200_OK)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consultation des factures
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)
