# customer/admin.py (App အသစ်တွင် ဖန်တီးရန်)
from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_number', 'email', 'preferred_branch', 'created_at')
    search_fields = ('name', 'phone_number')
    list_filter = ('preferred_branch',)
    readonly_fields = ('created_at',)