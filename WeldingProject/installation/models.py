"""
Installation Module for Solar/Machinery shops
- Links to Sales (Bundle or Product)
- Technician assignment
- Status tracking: Pending -> In Progress -> Completed -> Signed Off
- Signature capture
- Warranty sync on completion
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class InstallationJob(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending (စောင့်ဆိုင်းဆဲ)'),
        ('site_visit', 'Site visit (သွားတိုင်းရမည်)'),
        ('in_progress', 'In Progress (တပ်ဆင်ဆဲ)'),
        ('completed', 'Completed (ပြီးစီးပြီး)'),
        ('signed_off', 'Signed Off (လက်မှတ်ရေးထိုးပြီး)'),
        ('cancelled', 'Cancelled (ပယ်ဖျက်)'),
    )

    installation_no = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Installation No.")
    
    # Link to Sale Transaction (Bundle or Product sale)
    sale_transaction = models.ForeignKey(
        'inventory.SaleTransaction',
        on_delete=models.CASCADE,
        related_name='installation_jobs',
        verbose_name="ရောင်းချမှု"
    )
    
    # Customer from sale transaction
    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installations',
        verbose_name="ဖောက်သည်"
    )
    
    # Installation details
    installation_address = models.TextField(verbose_name="တပ်ဆင်မည့်လိပ်စာ")
    installation_date = models.DateField(verbose_name="တပ်ဆင်မည့်ရက်စွဲ")
    estimated_completion_date = models.DateField(null=True, blank=True, verbose_name="ခန့်မှန်းပြီးစီးမည့်ရက်")
    # သွားတိုင်းရမည့်ရက် (တပ်ဆင်မပြုလုပ်မီ သွားရောက်စစ်ဆေးမှု)
    site_visit_date = models.DateField(null=True, blank=True, verbose_name="သွားတိုင်းရမည့်ရက်")
    
    # Technician assignment
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_installations',
        limit_choices_to={'role_obj__name__icontains': 'technician'},
        verbose_name="တပ်ဆင်သူ (Technician)"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="အခြေအနေ"
    )
    
    # Notes and description
    description = models.TextField(blank=True, null=True, verbose_name="ဖော်ပြချက်")
    notes = models.TextField(blank=True, null=True, verbose_name="မှတ်ချက်")
    
    # Signature capture (file upload or canvas data)
    customer_signature = models.ImageField(
        upload_to='installation_signatures/',
        null=True,
        blank=True,
        verbose_name="ဖောက်သည် လက်မှတ်"
    )
    signed_off_at = models.DateTimeField(null=True, blank=True, verbose_name="လက်မှတ်ရေးထိုးသည့်ရက်စွဲ")
    signed_off_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_off_installations',
        verbose_name="လက်မှတ်ရေးထိုးသူ"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="ပြီးစီးသည့်ရက်စွဲ")
    
    # Created by
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_installations',
        verbose_name="ဖန်တီးသူ"
    )

    def save(self, *args, **kwargs):
        # Auto-generate installation number
        if not self.installation_no:
            date_str = datetime.date.today().strftime('%y%m%d')
            last_inst = InstallationJob.objects.filter(
                installation_no__startswith=f"INST-{date_str}"
            ).order_by('installation_no').last()
            
            if last_inst:
                try:
                    last_no = int(last_inst.installation_no.split('-')[-1])
                    new_no = last_no + 1
                except (ValueError, IndexError):
                    new_no = 1
            else:
                new_no = 1
            
            self.installation_no = f"INST-{date_str}-{new_no:04d}"
        
        # Auto-set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed':
            self.completed_at = None
        
        # Auto-set signed_off_at when status changes to signed_off
        if self.status == 'signed_off' and not self.signed_off_at:
            self.signed_off_at = timezone.now()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.installation_no} - {self.customer.name if self.customer else 'N/A'} ({self.get_status_display()})"

    class Meta:
        verbose_name = "တပ်ဆင်မှု (Installation Job)"
        verbose_name_plural = "တပ်ဆင်မှုများ (Installation Jobs)"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['technician', 'status']),
        ]


class InstallationStatusHistory(models.Model):
    """Status ပြောင်းလဲမှု မှတ်တမ်း"""
    installation_job = models.ForeignKey(
        InstallationJob,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Status မှတ်တမ်း"
        verbose_name_plural = "Status မှတ်တမ်းများ"

    def __str__(self):
        return f"{self.installation_job.installation_no} - {self.old_status} → {self.new_status}"
