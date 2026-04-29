from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, SubAccountViewSet, 
    SubAccountPermissionViewSet, UserActivityViewSet,
    AdminDashboardStatsView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sub-accounts', SubAccountViewSet, basename='sub-account')
router.register(r'permissions', SubAccountPermissionViewSet, basename='permission')
router.register(r'activities', UserActivityViewSet, basename='activity')

urlpatterns = [
    # JWT Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Admin Stats
    path('admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin_dashboard'),
    
    # API endpoints
    path('', include(router.urls)),
]
