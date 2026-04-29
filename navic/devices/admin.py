from django.contrib import admin
from .models import Device, DeviceState

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('imei', 'label', 'device_type', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'device_type', 'owner', 'created_at')
    search_fields = ('imei', 'label', 'owner__username', 'owner__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_connection', 'last_heartbeat')

@admin.register(DeviceState)
class DeviceStateAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'latitude', 'longitude', 'speed', 'status')
    list_filter = ('status', 'device__device_type', 'device__is_active', 'timestamp')
    search_fields = ('device__imei', 'device__label')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
