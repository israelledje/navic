from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/tracking/(?P<device_id>\d+)/$', consumers.DeviceTrackingConsumer.as_asgi()),
    re_path(r'ws/tracking/user/$', consumers.UserTrackingConsumer.as_asgi()),
    re_path(r'ws/alerts/$', consumers.AlertConsumer.as_asgi()),
]
