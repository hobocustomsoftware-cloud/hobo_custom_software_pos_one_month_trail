from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .managers import CustomUserManager  # သင့်ရဲ့ Custom Manager


# ----------------- Multi-Outlet Enterprise -----------------
class Outlet(models.Model):
    """
    Outlet (branch) for multi-outlet enterprise. Strict data isolation.
    Each outlet has two stock locations: Warehouse (bulk) and Shopfloor (sales).
    Optional hierarchy: parent_outlet = null → ဆိုင်ချုပ် (top-level), parent_outlet set → ဆိုင်ခွဲ (under that main).
    ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄–၈ ဆို parent_outlet နဲ့ ဖန်တီးလို့ရသည်။
    """
    name = models.CharField(max_length=200, verbose_name="Outlet Name")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Phone")
    is_main_branch = models.BooleanField(default=False, verbose_name="Main Branch")
    code = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="Code")
    is_active = models.BooleanField(default=True)
    parent_outlet = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_outlets',
        verbose_name="ဆိုင်ချုပ် (Parent)", help_text="null = ဆိုင်ချုပ်၊ set = ဒီဆိုင်ချုပ်ရဲ့ ဆိုင်ခွဲ"
    )

    class Meta:
        verbose_name = "Outlet"
        verbose_name_plural = "Outlets"
        ordering = ['-is_main_branch', 'name']

    def __str__(self):
        return f"{self.name}" + (" (Main)" if self.is_main_branch else "")

    def get_warehouse_location(self):
        """Location of type warehouse for this outlet. Each outlet must have one."""
        from inventory.models import Location
        return Location.objects.filter(outlet=self, location_type='warehouse').first()

    def get_shopfloor_location(self):
        """Location of type shop_floor for this outlet. Each outlet must have one."""
        from inventory.models import Location
        return Location.objects.filter(outlet=self, location_type='shop_floor').first()


@receiver(post_save, sender=Outlet)
def create_outlet_warehouse_and_shopfloor(sender, instance, created, **kwargs):
    """Each new Outlet gets two Locations: Warehouse and Shopfloor (strict data isolation)."""
    if not created:
        return
    from inventory.models import Location
    base = instance.name or "Outlet"
    Location.objects.get_or_create(
        outlet=instance,
        location_type='warehouse',
        defaults={'name': f"{base} - Warehouse", 'is_sale_location': False}
    )
    Location.objects.get_or_create(
        outlet=instance,
        location_type='shop_floor',
        defaults={'name': f"{base} - Shopfloor", 'is_sale_location': True}
    )


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

ASSIGNMENT_TYPE_CHOICES = (
    ('fixed', 'ပုံသေ (တစ်ဆိုင်တည်း)'),
    ('rotating', 'အလှည့်ကျ (ဆိုင်များကို လဲလှည့်သွားသည်)'),
)

class User(AbstractUser):
    # Phone: required unique identifier for public registration and login (Myanmar 09... / +959...).
    # Staff added by Owner may have null until assigned; registration requires phone.
    phone_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True, db_index=True,
        verbose_name="Phone Number"
    )
    # Dynamic Role ချိတ်ဆက်မှု
    role_obj = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    # Password ကို Owner ပြန်ကြည့်နိုင်ရန် (PlainText အနေဖြင့် ခဏသိမ်းထားမည့် Field)
    temp_password = models.CharField(max_length=128, blank=True, null=True)
    # First login: force password change (Owner adds staff with default password)
    requires_password_change = models.BooleanField(default=False, verbose_name="Must change password on first login")

    # Staff Assignment - ပုံသေ/အလှည့်ကျ
    assignment_type = models.CharField(
        max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='fixed',
        help_text="ပုံသေ = တစ်ဆိုင်တည်း၊ အလှည့်ကျ = ဆိုင်များကို လဲလှည့်သွားသည်"
    )
    primary_location = models.ForeignKey(
        'inventory.Location', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='primary_staff', help_text="ပုံသေထားသော ဝန်ထမ်းအတွက် မိမိဆိုင်"
    )
    primary_outlet = models.ForeignKey(
        Outlet, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='staff', help_text="Branch lock: staff see only this outlet. Owner: null = all outlets."
    )

    # Custom Manager ကို ပြန်လည်သတ်မှတ်ပေးရန် (AbstractUser သုံးလျှင် လိုအပ်ပါသည်)
    objects = CustomUserManager()

    @property
    def role(self):
        """ user.role လို့ ခေါ်ရင် role_obj ထဲက name ကို ပေးမှာပါ """
        if self.role_obj:
            return self.role_obj.name.lower() # ဥပမာ - "admin"
        return "employee"

    def save(self, *args, **kwargs):
        # Role အပေါ်မူတည်ပြီး is_staff (Admin Panel ဝင်ခွင့်) ကို ဆုံးဖြတ်ခြင်း
        if self.role_obj:
            role_name = self.role_obj.name.lower()
            # အထူးအခွင့်အရေးရှိသော Role များစာရင်း
            if any(privileged in role_name for privileged in ['owner', 'admin', 'super']):
                self.is_staff = True
            else:
                # ရိုးရိုး Staff များဖြစ်ပါက (superuser မဟုတ်လျှင်) is_staff ဖြုတ်မည်
                if not self.is_superuser:
                    self.is_staff = False
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role_obj.name if self.role_obj else 'No Role'})"


class StaffSession(models.Model):
    """ဝန်ထမ်း ယနေ့အလုပ်လုပ်မည့်ဆိုင် (အလှည့်ကျ ဝန်ထမ်းများအတွက်)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_sessions')
    location = models.ForeignKey(
        'inventory.Location', on_delete=models.CASCADE, related_name='staff_sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']
        get_latest_by = 'started_at'

    def __str__(self):
        return f"{self.user.username} @ {self.location.name}"


class Shift(models.Model):
    """အလုပ်ချိန် (Shift) – နံနက်/ည စသည်။"""
    name = models.CharField(max_length=100, verbose_name="Shift Name")
    start_time = models.TimeField(verbose_name="စတင်ချိန်")
    end_time = models.TimeField(verbose_name="ပြီးဆုံးချိန်")
    is_active = models.BooleanField(default=True, verbose_name="အသုံးပြုမည်")

    class Meta:
        ordering = ['start_time']
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"

    def __str__(self):
        return f"{self.name} ({self.start_time}–{self.end_time})"


# Loyverse-style registration: business category for unit templates
BUSINESS_CATEGORY_CHOICES = (
    ('pharmacy', 'Pharmacy / ဆေးဆိုင်'),
    ('pharmacy_clinic', 'Pharmacy + Clinic / ဆေးခန်းတွဲ ဆေးဆိုင်'),
    ('mobile', 'Mobile / ဖုန်းဆိုင်'),
    ('electronic_solar', 'Electronic / Solar / လျှပ်စစ်ဆိုင်'),
    ('hardware', 'Hardware / အိမ်ဆောက်ပစ္စည်းဆိုင်'),
    ('liquor', 'Liquor Store / အရက်ဆိုင်'),
    ('grocery', 'Grocery / ကုန်မာဆိုင်'),
    ('general', 'General Retail / အထွေထွေ'),
)
CURRENCY_CHOICES = (
    ('MMK', 'ကျပ် (MMK)'),
    ('USD', 'US Dollar (USD)'),
    ('THB', 'ဘတ် (THB)'),
)


class ShopSettings(models.Model):
    """ဆိုင်ချိန်ညှိချက် - Logo နှင့် ဆိုင်အမည် (တစ်ဆိုင်လျှင် တစ်ခု). trial_start_date = 30-day trial for multi-instance hosting."""
    shop_name = models.CharField(max_length=200, default='HoBo POS')
    logo = models.ImageField(upload_to='shop/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    trial_start_date = models.DateTimeField(null=True, blank=True, help_text='When set, trial expires 30 days after this date.')
    # Loyverse-style: Business Name (= shop_name), Category, Currency (from registration)
    business_category = models.CharField(
        max_length=32, choices=BUSINESS_CATEGORY_CHOICES, default='general', blank=True,
        verbose_name='Business Category'
    )
    currency = models.CharField(
        max_length=8, choices=CURRENCY_CHOICES, default='MMK', blank=True,
        verbose_name='Currency'
    )
    setup_wizard_done = models.BooleanField(
        default=False,
        help_text='True after first-time setup wizard completed (Loyverse-style).'
    )
    filter_units_by_business_category = models.BooleanField(
        default=True,
        verbose_name='ဆိုင်အမျိုးအစားအလိုက် unit ပဲပြမယ်',
        help_text='On: only units for selected business type. Off: show all units.'
    )

    class Meta:
        verbose_name = 'ဆိုင်ချိန်ညှိချက်'
        verbose_name_plural = 'ဆိုင်ချိန်ညှိချက်များ'

    @classmethod
    def get_settings(cls):
        from django.utils import timezone
        # Multi-instance: trial_start_date set on first create (30-day trial)
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={'shop_name': 'HoBo POS', 'trial_start_date': timezone.now()}
        )
        return obj


class AuditLog(models.Model):
    """RBAC audit: every Sale, Stock Transfer, Approval records User_ID (and outlet) to prevent theft/errors."""
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='audit_logs', verbose_name="User who performed the action"
    )
    action = models.CharField(max_length=64, db_index=True)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    outlet = models.ForeignKey(
        Outlet, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs'
    )
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=['action', 'created_at'], name='core_audit_act_0a1b0d_idx'),
            models.Index(fields=['outlet', 'created_at'], name='core_audit_out_8c2e4f_idx'),
        ]

    def __str__(self):
        return f"{self.action} by {self.user_id} at {self.created_at}"


class LoginFailAttempt(models.Model):
    """Brute-force protection: 5 failed attempts per phone/email locks the account temporarily."""
    phone_normalized = models.CharField(max_length=320, unique=True, db_index=True)
    fail_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Login Fail Attempt"
        verbose_name_plural = "Login Fail Attempts"

    def __str__(self):
        return f"{self.phone_normalized} ({self.fail_count} fails)"