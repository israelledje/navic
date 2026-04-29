from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceGroupViewSet, DriverViewSet, FuelEntryViewSet,
    MaintenanceRecordViewSet, FleetStatisticsViewSet
)

router = DefaultRouter()
router.register(r'groups', DeviceGroupViewSet, basename='devicegroup')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'fuel', FuelEntryViewSet, basename='fuelentry')
router.register(r'maintenance', MaintenanceRecordViewSet, basename='maintenancerecord')
router.register(r'stats', FleetStatisticsViewSet, basename='fleetstatistics')

urlpatterns = [
    path('', include(router.urls)),
]
