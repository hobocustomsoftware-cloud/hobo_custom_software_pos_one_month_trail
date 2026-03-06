from django.contrib import admin
from .models import InstallationJob, InstallationStatusHistory


@admin.register(InstallationJob)
class InstallationJobAdmin(admin.ModelAdmin):
    list_display = [
        'installation_no',
        'sale_transaction',
        'customer',
        'technician',
        'status',
        'installation_date',
        'created_at',
    ]
    list_filter = ['status', 'installation_date', 'created_at']
    search_fields = ['installation_no', 'customer__name', 'sale_transaction__invoice_number']
    readonly_fields = ['installation_no', 'created_at', 'updated_at', 'completed_at', 'signed_off_at']


@admin.register(InstallationStatusHistory)
class InstallationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['installation_job', 'old_status', 'new_status', 'created_at', 'updated_by']
    list_filter = ['new_status', 'created_at']
    readonly_fields = ['created_at']
