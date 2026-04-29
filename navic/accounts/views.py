from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import SubAccountPermission, UserActivity
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    UserUpdateSerializer, ChangePasswordSerializer,
    SubAccountSerializer, SubAccountPermissionSerializer,
    UserActivitySerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs et du profil personnel
    """
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Récupérer ou mettre à jour le profil de l'utilisateur connecté"""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        serializer = self.get_serializer(user, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Changer le mot de passe de l'utilisateur connecté"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Ancien mot de passe incorrect."]}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Mot de passe mis à jour avec succès."}, status=status.HTTP_200_OK)

class SubAccountViewSet(viewsets.ModelViewSet):
    """
    Gestion des sous-comptes par le compte parent
    """
    serializer_class = SubAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(parent_account=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent_account=self.request.user, user_type='sub_account')

class SubAccountPermissionViewSet(viewsets.ModelViewSet):
    """
    Gestion des permissions accordées aux sous-comptes
    """
    serializer_class = SubAccountPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un utilisateur peut voir les permissions des sous-comptes qu'il gère
        return SubAccountPermission.objects.filter(sub_account__parent_account=self.request.user)

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historique des activités de l'utilisateur
    """
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by('-created_at')

from rest_framework.views import APIView

class AdminDashboardStatsView(APIView):
    """
    Vue de statistiques globales pour le Superadmin
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        from devices.models import Device
        from billing.models import Invoice
        from django.db.models import Sum
        
        total_users = User.objects.filter(is_superuser=False).count()
        total_companies = User.objects.filter(user_type='company').count()
        total_devices = Device.objects.count()
        online_devices = Device.objects.filter(is_online=True).count()
        
        revenue = Invoice.objects.filter(status='paid').aggregate(total=Sum('total'))['total'] or 0
        
        recent_users = UserSerializer(User.objects.filter(is_superuser=False).order_by('-created_at')[:5], many=True).data
        
        return Response({
            'stats': {
                'total_users': total_users,
                'total_companies': total_companies,
                'total_devices': total_devices,
                'online_devices': online_devices,
                'total_revenue': revenue
            },
            'recent_users': recent_users
        })

from .models import WhiteLabelConfig
from .serializers import WhiteLabelConfigSerializer

class PublicSettingsView(APIView):
    """
    Endpoint public pour récupérer la configuration de la marque blanche.
    Sert à peindre l'interface (logo, couleur) avant même le login.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        domain = request.GET.get('domain')
        # Si aucun domaine passé, essayer de le deviner depuis le header Host
        if not domain:
            domain = request.get_host().split(':')[0]
            
        try:
            # Chercher une configuration spécifique au domaine
            config = WhiteLabelConfig.objects.get(domain=domain)
            serializer = WhiteLabelConfigSerializer(config)
            return Response(serializer.data)
        except WhiteLabelConfig.DoesNotExist:
            # Si aucune config trouvée pour ce domaine, on retourne les valeurs par défaut
            return Response({
                "platform_name": "Navic",
                "primary_color": "#00cc99",
                "logo": None,
                "favicon": None,
                "domain": domain
            })
