from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertRuleViewSet, AlertViewSet, MaintenanceReminderViewSet

router = DefaultRouter()
router.register(r'rules', AlertRuleViewSet, basename='alertrule')
router.register(r'history', AlertViewSet, basename='alert')
router.register(r'maintenance', MaintenanceReminderViewSet, basename='maintenancereminder')

urlpatterns = [
    path('', include(router.urls)),
]
