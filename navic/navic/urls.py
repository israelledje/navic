from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_root(request, format=None):
    """
    Point d'entrée principal de l'API Navic GPS.
    """
    return Response({
        'accounts': reverse('user-list', request=request, format=format),
        'auth': {
            'login': request.build_absolute_uri('/api/accounts/auth/login/'),
            'refresh': request.build_absolute_uri('/api/accounts/auth/refresh/'),
        },
        'devices': request.build_absolute_uri('/api/devices/'),
        'tracking': request.build_absolute_uri('/api/tracking/'),
        'alerts': request.build_absolute_uri('/api/alerts/'),
        'fleet': request.build_absolute_uri('/api/fleet/'),
        'billing': request.build_absolute_uri('/api/billing/'),
    })

from accounts.views import PublicSettingsView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Routes
    path('api/', api_root, name='api-root'),
    path('api/settings/public/', PublicSettingsView.as_view(), name='public-settings'),
    path('api/accounts/', include('accounts.urls')),
    path('api/devices/', include('devices.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/fleet/', include('fleet.urls')),
    path('api/billing/', include('billing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
