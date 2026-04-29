from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceModelViewSet, DeviceViewSet, DeviceCommandViewSet

router = DefaultRouter()
router.register(r'models', DeviceModelViewSet, basename='devicemodel')
router.register(r'trackers', DeviceViewSet, basename='device')
router.register(r'commands', DeviceCommandViewSet, basename='devicecommand')

urlpatterns = [
    path('', include(router.urls)),
]
