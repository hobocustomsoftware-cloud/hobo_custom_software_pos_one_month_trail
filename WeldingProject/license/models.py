"""
License System Models
- Trial: ၁ လ + ၅ ရက် grace
- On-Premise: တစ်ခါဝယ် perpetual
- Hosted: တစ်နှစ်တစ်ခါ renewal
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta


class LicenseType(models.TextChoices):
    TRIAL = 'trial', 'Trial (၁ လ + ၅ ရက် grace)'
    ON_PREMISE_PERPETUAL = 'on_premise_perpetual', 'On-Premise (တစ်ခါဝယ် အမြဲသုံး)'
    HOSTED_ANNUAL = 'hosted_annual', 'Hosted (တစ်နှစ်တစ်ခါ renewal)'


class AppInstallation(models.Model):
    """
    App ပထမဆုံး run သည့်အခါ သိမ်းခြင်း (Trial tracking)
    """
    machine_id = models.CharField(max_length=255, unique=True, db_index=True)
    first_run_at = models.DateTimeField(auto_now_add=True)
    deployment_mode = models.CharField(
        max_length=30,
        default='on_premise',
        choices=[
            ('on_premise', 'On-Premise (စက်ထဲမှာထား)'),
            ('hosted', 'Hosted (Server ပေါ်တင်)'),
        ]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'license_app_installation'
        verbose_name = 'App Installation'
        verbose_name_plural = 'App Installations'

    def __str__(self):
        return f"{self.machine_id} - {self.first_run_at.date()}"

    @property
    def trial_expires_at(self):
        """၁ လ trial ကုန်သည့်ရက်"""
        return self.first_run_at + timedelta(days=30)

    @property
    def grace_expires_at(self):
        """၅ ရက် grace ကုန်သည့်ရက်"""
        return self.trial_expires_at + timedelta(days=5)

    @property
    def is_trial_expired(self):
        """Trial ကုန်ပြီးပြီလား"""
        return timezone.now() > self.trial_expires_at

    @property
    def is_grace_expired(self):
        """Grace period ကုန်ပြီးပြီလား (ပိတ်ရမည်)"""
        return timezone.now() > self.grace_expires_at

    @property
    def days_remaining_in_trial(self):
        """Trial ထဲမှာ ဘယ်နှစ်ရက် ကျန်သေးလဲ"""
        if timezone.now() > self.trial_expires_at:
            return 0
        return (self.trial_expires_at - timezone.now()).days

    @property
    def days_remaining_in_grace(self):
        """Grace ထဲမှာ ဘယ်နှစ်ရက် ကျန်သေးလဲ"""
        if timezone.now() > self.grace_expires_at:
            return 0
        return (self.grace_expires_at - timezone.now()).days


class AppLicense(models.Model):
    """
    ဝယ်ပြီး / Activate လုပ်ပြီး license
    """
    license_type = models.CharField(
        max_length=30,
        choices=LicenseType.choices,
    )
    machine_id = models.CharField(max_length=255, db_index=True, blank=True)
    license_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # HOSTED_ANNUAL အတွက်သာ
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'license_app_license'
        verbose_name = 'App License'
        verbose_name_plural = 'App Licenses'

    def __str__(self):
        return f"{self.license_type} - {self.machine_id or 'N/A'}"

    @property
    def is_perpetual(self):
        """အမြဲသုံးခွင့်ရှိလား (On-Premise)"""
        return self.license_type == LicenseType.ON_PREMISE_PERPETUAL

    @property
    def is_expired(self):
        """သက်တမ်းကုန်ပြီးပြီလား"""
        if self.is_perpetual:
            return False
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_valid(self):
        """License မှန်ကန်ပြီး သုံးလို့ရသေးလား"""
        return self.is_active and not self.is_expired
