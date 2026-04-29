from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ingest_gps_data, update_device_status, GPSPositionViewSet, 
    TripViewSet, GeofenceViewSet, ReportViewSet
)

router = DefaultRouter()
router.register(r'positions', GPSPositionViewSet, basename='gpsposition')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'geofences', GeofenceViewSet, basename='geofence')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # Ingestion endpoints (pour le service Go)
    path('ingest/', ingest_gps_data, name='ingest-gps-data'),
    path('status/', update_device_status, name='update-device-status'),
    
    # API endpoints
    path('', include(router.urls)),
]
