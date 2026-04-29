from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Gestionnaire personnalisé pour le modèle User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Créer et retourner un utilisateur standard"""
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Créer et retourner un super utilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser doit avoir is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    
    USER_TYPE_CHOICES = [
        ('admin', 'Administrateur'),
        ('company', 'Entreprise'),
        ('individual', 'Particulier'),
        ('sub_account', 'Sous-compte'),
    ]
    
    username = None  # On utilise email comme identifiant
    email = models.EmailField(_('adresse email'), unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='individual')
    phone = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Congo')
    
    # Relations
    parent_account = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_accounts',
        help_text="Compte parent pour les sous-comptes"
    )
    
    # Package de facturation
    billing_package = models.ForeignKey(
        'billing.BillingPackage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Préférences utilisateur
    language = models.CharField(max_length=10, default='fr')
    timezone = models.CharField(max_length=50, default='Africa/Brazzaville')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def is_sub_account(self):
        """Vérifie si c'est un sous-compte"""
        return self.user_type == 'sub_account' and self.parent_account is not None
    
    def can_create_device(self):
        """Vérifie si l'utilisateur peut créer un device"""
        if self.is_superuser or self.user_type == 'admin':
            return True
        
        if self.billing_package:
            current_devices = self.devices.count()
            return current_devices < self.billing_package.max_devices
        
        return False


class SubAccountPermission(models.Model):
    """Permissions pour les sous-comptes"""
    
    PERMISSION_CHOICES = [
        ('view', 'Voir'),
        ('track', 'Suivre en temps réel'),
        ('history', 'Voir l\'historique'),
        ('reports', 'Générer des rapports'),
        ('alerts', 'Gérer les alertes'),
        ('edit', 'Modifier'),
    ]
    
    sub_account = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_permissions',
        limit_choices_to={'user_type': 'sub_account'}
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='sub_account_permissions'
    )
    permissions = models.JSONField(
        default=list,
        help_text="Liste des permissions accordées"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Permission sous-compte"
        verbose_name_plural = "Permissions sous-comptes"
        unique_together = ['sub_account', 'device']
    
    def __str__(self):
        return f"{self.sub_account.email} - {self.device.name}"
    
    def has_permission(self, permission):
        """Vérifie si le sous-compte a une permission spécifique"""
        return permission in self.permissions


class UserActivity(models.Model):
    """Historique des activités utilisateur"""
    
    ACTIVITY_TYPES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('device_created', 'Device créé'),
        ('device_updated', 'Device modifié'),
        ('device_deleted', 'Device supprimé'),
        ('alert_created', 'Alerte créée'),
        ('report_generated', 'Rapport généré'),
        ('settings_updated', 'Paramètres modifiés'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateur"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} - {self.created_at}"

class WhiteLabelConfig(models.Model):
    """Configuration de Marque Blanche pour une entreprise ou le superadmin"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='whitelabel'
    )
    domain = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True, 
        help_text="Domaine personnalisé (ex: track.monentreprise.com)"
    )
    platform_name = models.CharField(max_length=100, default="Navic")
    primary_color = models.CharField(max_length=7, default="#00CC99")
    logo = models.ImageField(upload_to='whitelabel/logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='whitelabel/favicons/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration Marque Blanche"
        verbose_name_plural = "Configurations Marque Blanche"
        
    def __str__(self):
        return f"Marque Blanche - {self.platform_name} ({self.user.email})"
