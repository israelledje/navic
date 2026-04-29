from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, SubAccountPermission, UserActivity


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'phone',
            'company_name', 'address', 'city', 'country'
        ]
        read_only_fields = ['id']
    
    def validate(self, attrs):
        """Valide que les mots de passe correspondent"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_sub_account_user = serializers.BooleanField(source='is_sub_account', read_only=True)
    can_create_device_flag = serializers.BooleanField(source='can_create_device', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'company_name', 'address', 'city', 'country',
            'is_sub_account_user', 'can_create_device_flag',
            'language', 'timezone', 'notifications_enabled',
            'email_notifications', 'sms_notifications',
            'is_email_verified', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'full_name', 'is_sub_account_user', 'can_create_device_flag',
            'is_email_verified', 'created_at', 'updated_at', 'last_login'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'company_name',
            'address', 'city', 'country', 'language', 'timezone',
            'notifications_enabled', 'email_notifications', 'sms_notifications'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valide que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les mots de passe ne correspondent pas."
            })
        return attrs


class SubAccountPermissionSerializer(serializers.ModelSerializer):
    """Serializer pour les permissions des sous-comptes"""
    
    sub_account_email = serializers.EmailField(source='sub_account.email', read_only=True)
    sub_account_name = serializers.CharField(source='sub_account.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = SubAccountPermission
        fields = [
            'id', 'sub_account', 'sub_account_email', 'sub_account_name',
            'device', 'device_name', 'device_imei',
            'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sub_account_email', 'sub_account_name',
            'device_name', 'device_imei', 'created_at', 'updated_at'
        ]
    
    def validate_permissions(self, value):
        """Valide que les permissions sont valides"""
        valid_perms = ['view', 'track', 'history', 'reports', 'alerts', 'edit']
        for perm in value:
            if perm not in valid_perms:
                raise serializers.ValidationError(
                    f"Permission invalide: {perm}. Valeurs autorisées: {', '.join(valid_perms)}"
                )
        return value


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des activités utilisateur"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_email', 'activity_type', 'activity_type_display',
            'description', 'ip_address', 'user_agent', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'activity_type_display', 'created_at']


class SubAccountSerializer(serializers.ModelSerializer):
    """Serializer pour créer un sous-compte"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'phone', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Créer un sous-compte"""
        # Le parent_account sera défini dans la vue
        validated_data['user_type'] = 'sub_account'
        user = User.objects.create_user(**validated_data)
        return user

from .models import WhiteLabelConfig

class WhiteLabelConfigSerializer(serializers.ModelSerializer):
    """Serializer pour la configuration de la marque blanche"""
    
    class Meta:
        model = WhiteLabelConfig
        fields = ['domain', 'platform_name', 'primary_color', 'logo', 'favicon']
