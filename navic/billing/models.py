from django.db import models
from django.utils.translation import gettext_lazy as _


class BillingPackage(models.Model):
    """Packages de facturation pour les utilisateurs"""
    
    PACKAGE_TYPES = [
        ('free', 'Gratuit'),
        ('starter', 'Starter'),
        ('professional', 'Professionnel'),
        ('enterprise', 'Entreprise'),
        ('custom', 'Personnalisé'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Limites du package
    max_devices = models.IntegerField(
        default=1,
        help_text="Nombre maximum de devices autorisés"
    )
    max_sub_accounts = models.IntegerField(
        default=0,
        help_text="Nombre maximum de sous-comptes autorisés"
    )
    
    # Fonctionnalités
    realtime_tracking = models.BooleanField(default=True)
    history_days = models.IntegerField(
        default=30,
        help_text="Nombre de jours d'historique disponibles"
    )
    reports_enabled = models.BooleanField(default=True)
    alerts_enabled = models.BooleanField(default=True)
    api_access = models.BooleanField(default=False)
    geofencing = models.BooleanField(default=False)
    fleet_management = models.BooleanField(default=False)
    custom_reports = models.BooleanField(default=False)
    
    # Tarification
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Prix mensuel en FCFA"
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Prix annuel en FCFA"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=True,
        help_text="Visible pour inscription publique"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Package de facturation"
        verbose_name_plural = "Packages de facturation"
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} ({self.get_package_type_display()})"


class DeviceTariffPlan(models.Model):
    """Plans tarifaires par device (Business $5, Premium $10, etc.)"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan tarifaire device"
        verbose_name_plural = "Plans tarifaires device"
        ordering = ['price_monthly']

    def __str__(self):
        return f"{self.name} - {self.price_monthly} {self.currency}"


class Subscription(models.Model):
    """Abonnements utilisateur"""
    
    BILLING_CYCLES = [
        ('monthly', 'Mensuel'),
        ('yearly', 'Annuel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('pending', 'En attente'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
        ('suspended', 'Suspendu'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    package = models.ForeignKey(
        BillingPackage,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Montants
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')  # FCFA
    
    # Auto-renouvellement
    auto_renew = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.package.name} ({self.get_status_display()})"
    
    def is_active(self):
        """Vérifie si l'abonnement est actif"""
        from django.utils import timezone
        return self.status == 'active' and self.end_date > timezone.now()


class Payment(models.Model):
    """Paiements effectués"""
    
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Virement bancaire'),
        ('credit_card', 'Carte de crédit'),
        ('cash', 'Espèces'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    # Informations de paiement
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Références
    transaction_id = models.CharField(max_length=255, unique=True)
    external_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Référence externe (Mobile Money, banque, etc.)"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} ({self.get_status_display()})"


class Invoice(models.Model):
    """Factures générées"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulée'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    # Informations facture
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Montants
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Taux de TVA en pourcentage"
    )
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Facture {self.invoice_number} - {self.user.email}"
