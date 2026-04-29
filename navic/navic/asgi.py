"""
ASGI config for navic project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Initialiser Django ASGI application early to ensure AppRegistry is populated
# avant d'importer le code qui peut importer ORM models.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'navic.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from accounts.channels_auth import TokenAuthMiddleware
import tracking.routing

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's ASGI application
    "http": django_asgi_app,
    
    # WebSocket tracker handler
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(
                    tracking.routing.websocket_urlpatterns
                )
            )
        )
    ),
})
