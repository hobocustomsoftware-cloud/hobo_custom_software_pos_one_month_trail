from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, StaffSession, ShopSettings, Outlet, AuditLog, LoginFailAttempt


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent_outlet', 'is_main_branch', 'phone', 'is_active')
    list_filter = ('is_main_branch', 'is_active', 'parent_outlet')
    search_fields = ('name', 'code', 'address')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'action', 'user', 'object_type', 'object_id', 'outlet', 'created_at')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('action', 'user__username')
    readonly_fields = ('user', 'action', 'object_type', 'object_id', 'outlet', 'details', 'created_at')
    date_hierarchy = 'created_at'


# ၁။ Role Model ကို Admin တွင် Register လုပ်ခြင်း
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)

# ၂။ Custom User Admin ပြင်ဆင်ခြင်း
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # 'role' အစား 'role_obj' ကို ပြောင်းလဲအသုံးပြုပါ
    list_display = ('username', 'phone_number', 'email', 'get_role', 'assignment_type', 'primary_outlet', 'primary_location', 'is_staff', 'is_active')
    list_filter = ('role_obj', 'assignment_type', 'primary_outlet', 'is_staff', 'is_active')
    search_fields = ('username', 'phone_number', 'email', 'first_name', 'last_name')
    
    # ForeignKey ဖြစ်၍ နာမည်တိုက်ရိုက်ပြရန် function တစ်ခုဆောက်ခြင်း
    def get_role(self, obj):
        return obj.role_obj.name if obj.role_obj else "-"
    get_role.short_description = 'Role'

    # Edit Page: User အချက်အလက်ပြင်ဆင်သည့်နေရာ
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role_obj', 'phone_number', 'temp_password', 'requires_password_change')}),
        ('Staff Assignment', {'fields': ('assignment_type', 'primary_outlet', 'primary_location')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role_obj', 'phone_number', 'email', 'temp_password')}),
    )
    readonly_fields = ('temp_password',)


@admin.register(LoginFailAttempt)
class LoginFailAttemptAdmin(admin.ModelAdmin):
    list_display = ('phone_normalized', 'fail_count', 'locked_until', 'updated_at')
    readonly_fields = ('phone_normalized', 'fail_count', 'locked_until', 'updated_at')


@admin.register(StaffSession)
class StaffSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'started_at', 'ended_at', 'is_active')
    list_filter = ('is_active', 'location')
    search_fields = ('user__username', 'location__name')


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'updated_at')