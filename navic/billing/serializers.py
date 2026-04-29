from rest_framework import serializers
from .models import BillingPackage, DeviceTariffPlan, Subscription, Payment, Invoice


class DeviceTariffPlanSerializer(serializers.ModelSerializer):
    """Serializer pour les plans tarifaires device"""
    class Meta:
        model = DeviceTariffPlan
        fields = ['id', 'name', 'description', 'price_monthly', 'currency', 'is_active']


class BillingPackageSerializer(serializers.ModelSerializer):
    """Serializer pour les packages de facturation"""
    
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    
    class Meta:
        model = BillingPackage
        fields = [
            'id', 'name', 'package_type', 'package_type_display', 'description',
            'max_devices', 'max_sub_accounts', 'realtime_tracking', 'history_days',
            'reports_enabled', 'alerts_enabled', 'api_access', 'geofencing',
            'fleet_management', 'custom_reports',
            'price_monthly', 'price_yearly', 'is_active', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'package_type_display', 'created_at', 'updated_at']


class BillingPackageListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des packages"""
    
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    
    class Meta:
        model = BillingPackage
        fields = [
            'id', 'name', 'package_type', 'package_type_display',
            'description', 'max_devices', 'max_sub_accounts',
            'price_monthly', 'price_yearly', 'is_active'
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_details = BillingPackageListSerializer(source='package', read_only=True)
    billing_cycle_display = serializers.CharField(source='get_billing_cycle_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active_subscription = serializers.BooleanField(source='is_active', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_email', 'package', 'package_name', 'package_details',
            'billing_cycle', 'billing_cycle_display', 'status', 'status_display',
            'start_date', 'end_date', 'next_billing_date',
            'amount', 'currency', 'auto_renew', 'is_active_subscription',
            'created_at', 'updated_at', 'cancelled_at', 'cancellation_reason'
        ]
        read_only_fields = [
            'id', 'user_email', 'package_name', 'package_details',
            'billing_cycle_display', 'status_display', 'is_active_subscription',
            'created_at', 'updated_at'
        ]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un abonnement"""
    
    class Meta:
        model = Subscription
        fields = [
            'package', 'billing_cycle', 'auto_renew'
        ]
    
    def validate(self, attrs):
        """Valide les données de l'abonnement"""
        # Le user sera défini dans la vue
        package = attrs.get('package')
        
        if not package.is_active:
            raise serializers.ValidationError({
                "package": "Ce package n'est pas disponible actuellement."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Créer un abonnement avec calcul des dates et montant"""
        from django.utils import timezone
        from datetime import timedelta
        
        package = validated_data['package']
        billing_cycle = validated_data['billing_cycle']
        
        # Calculer les dates
        start_date = timezone.now()
        if billing_cycle == 'monthly':
            end_date = start_date + timedelta(days=30)
            amount = package.price_monthly
        else:  # yearly
            end_date = start_date + timedelta(days=365)
            amount = package.price_yearly
        
        subscription = Subscription.objects.create(
            **validated_data,
            start_date=start_date,
            end_date=end_date,
            next_billing_date=end_date,
            amount=amount,
            status='pending'
        )
        
        return subscription


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer pour les paiements"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    subscription_details = SubscriptionSerializer(source='subscription', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'subscription', 'subscription_details',
            'payment_method', 'payment_method_display',  'amount', 'currency',
            'status', 'status_display', 'transaction_id', 'external_reference',
            'metadata', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'subscription_details', 'payment_method_display',
            'status_display', 'created_at', 'updated_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un paiement"""
    
    class Meta:
        model = Payment
        fields = [
            'subscription', 'payment_method', 'amount', 'currency', 'external_reference'
        ]
    
    def validate(self, attrs):
        """Valide les données du paiement"""
        subscription = attrs.get('subscription')
        
        if subscription and subscription.status == 'active':
            raise serializers.ValidationError({
                "subscription": "Cet abonnement est déjà actif."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Créer un paiement avec génération du transaction_id"""
        import uuid
        
        # Générer un transaction_id unique
        transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
        
        payment = Payment.objects.create(
            **validated_data,
            transaction_id=transaction_id,
            status='pending'
        )
        
        return payment


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer pour les factures"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    subscription_details = SubscriptionSerializer(source='subscription', read_only=True)
    payment_details = PaymentSerializer(source='payment', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'subscription', 'subscription_details',
            'payment', 'payment_details',
            'invoice_number', 'status', 'status_display',
            'subtotal', 'tax_rate', 'tax_amount', 'total', 'currency',
            'issue_date', 'due_date', 'paid_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'subscription_details',
            'payment_details', 'status_display', 'created_at', 'updated_at'
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une facture"""
    
    class Meta:
        model = Invoice
        fields = [
            'user', 'subscription', 'payment',
            'subtotal', 'tax_rate', 'notes'
        ]
    
    def create(self, validated_data):
        """Créer une facture avec calcul automatique"""
        from django.utils import timezone
        from datetime import timedelta
        import uuid
        
        # Générer un numéro de facture
        invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculer la TVA et le total
        subtotal = validated_data['subtotal']
        tax_rate = validated_data.get('tax_rate', 0)
        tax_amount = (subtotal * tax_rate) / 100
        total = subtotal + tax_amount
        
        # Dates
        issue_date = timezone.now().date()
        due_date = issue_date + timedelta(days=30)
        
        invoice = Invoice.objects.create(
            **validated_data,
            invoice_number=invoice_number,
            tax_amount=tax_amount,
            total=total,
            issue_date=issue_date,
            due_date=due_date,
            status='sent'
        )
        
        return invoice


class SubscriptionCancelSerializer(serializers.Serializer):
    """Serializer pour annuler un abonnement"""
    
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Valide que l'abonnement peut être annulé"""
        subscription = self.context.get('subscription')
        
        if subscription.status in ['cancelled', 'expired']:
            raise serializers.ValidationError(
                "Cet abonnement est déjà annulé ou expiré."
            )
        
        return attrs
