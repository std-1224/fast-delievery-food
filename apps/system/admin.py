from django.contrib import admin

from apps.system.models import SystemConfig, Menu, Slider, Device, CoreConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "currency")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "public_key", "app_id", "is_connected")


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'order')


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('name', 'content')


@admin.register(CoreConfig)
class CoreConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_admin_emails')
