from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('imei', 'name', 'status', 'owner', 'is_online', 'created_at')
    list_filter = ('status', 'is_online', 'owner', 'created_at')
    search_fields = ('imei', 'name', 'owner__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_connection')
