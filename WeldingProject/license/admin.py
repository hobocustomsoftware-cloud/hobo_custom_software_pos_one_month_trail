from django.contrib import admin
from .models import AppInstallation, AppLicense, BackupAddOn, PlanFeature, SubscriptionPlan


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


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 0


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'price_mmk', 'billing_cycle', 'is_active', 'sort_order')
    list_filter = ('is_active', 'billing_cycle')
    inlines = [PlanFeatureInline]


@admin.register(BackupAddOn)
class BackupAddOnAdmin(admin.ModelAdmin):
    list_display = ('license_key', 'machine_id', 'shop', 'is_active', 'expires_at')
    list_filter = ('is_active',)
    search_fields = ('license_key', 'machine_id')
