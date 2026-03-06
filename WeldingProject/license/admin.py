from django.contrib import admin
from .models import AppInstallation, AppLicense


@admin.register(AppInstallation)
class AppInstallationAdmin(admin.ModelAdmin):
    list_display = ('machine_id', 'first_run_at', 'deployment_mode', 'updated_at')
    search_fields = ('machine_id',)
    readonly_fields = ('first_run_at', 'updated_at')


@admin.register(AppLicense)
class AppLicenseAdmin(admin.ModelAdmin):
    list_display = ('license_key', 'license_type', 'machine_id', 'activated_at', 'expires_at', 'is_active')
    list_filter = ('license_type', 'is_active')
    search_fields = ('license_key', 'machine_id')
    readonly_fields = ('activated_at', 'created_at', 'updated_at')
