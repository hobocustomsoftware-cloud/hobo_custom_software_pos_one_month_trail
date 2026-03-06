from django.db import models
from django.conf import settings
from customer.models import Customer
import datetime
from inventory.models import *

class RepairService(models.Model):
    STATUS_CHOICES = (
        ('received', 'လက်ခံရရှိ (Pending)'),
        ('fixing', 'ပြင်ဆင်ဆဲ (In Progress)'),
        ('ready', 'လာယူနိုင်ပြီ (Ready for Pickup)'),
        ('completed', 'ပေးအပ်ပြီး'),
        ('cancelled', 'ပယ်ဖျက်'),
    )

    repair_no = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='repairs')
    item_name = models.CharField(max_length=200)
    problem_description = models.TextField()

    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.CASCADE,
        related_name='repairs',
        null=True,
        blank=True,
        verbose_name="ဆိုင်ခွဲ (လာယူမည့်နေရာ / preferred_pickup_location)"
    )
    
    # ငွေကြေးပိုင်း
    labour_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="လုပ်အားခ")
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_deposit_paid = models.BooleanField(default=False)
    
    # ရက်စွဲပိုင်း
    received_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateField() # Calendar အတွက်
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Customer ကို ဖုန်းဆက်ရန်အတွက်
    is_customer_notified = models.BooleanField(default=False, help_text="ဖုန်းဆက်ပြီး/မပြီး")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def parts_total(self):
        """Spare Parts စုစုပေါင်းကုန်ကျစရိတ်"""
        return sum(p.subtotal for p in self.spare_parts.all())

    @property
    def total_cost_breakdown(self):
        """Labour + Parts စုစုပေါင်း"""
        return self.labour_cost + self.parts_total

    @property
    def balance_amount(self):
        """ကျန်ငွေ တွက်ချက်ခြင်း"""
        total = self.total_estimated_cost if self.total_estimated_cost > 0 else self.total_cost_breakdown
        return total - self.deposit_amount

    def save(self, *args, **kwargs):
        if not self.repair_no:
            date_str = datetime.date.today().strftime('%y%m%d')
            last_rep = RepairService.objects.filter(repair_no__startswith=f"REP-{date_str}").last()
            new_no = (int(last_rep.repair_no.split('-')[-1]) + 1) if last_rep else 1
            self.repair_no = f"REP-{date_str}-{new_no:03d}"
        super().save(*args, **kwargs)


class RepairSparePart(models.Model):
    """စက်ပြင်တွင် အသုံးပြုသော Spare Parts စာရင်း"""
    repair_service = models.ForeignKey(
        RepairService, on_delete=models.CASCADE, related_name='spare_parts'
    )
    product = models.ForeignKey(
        'inventory.Product', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Inventory မှ ပစ္စည်း (ရွေးချယ်နိုင်သည်)"
    )
    part_name = models.CharField(max_length=200, verbose_name="အမည်")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_name} x {self.quantity} = {self.subtotal}"


class RepairStatusHistory(models.Model):
    """Status ပြောင်းလဲမှု မှတ်တမ်း"""
    repair_service = models.ForeignKey(
        RepairService, on_delete=models.CASCADE, related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )


# ---------- ဆေးခန်း ကုသမှုမှတ်တမ်း (Clinic Treatment Record) ----------
class TreatmentRecord(models.Model):
    """
    ဆေးခန်းအတွက် လူနာ ကုသမှုမှတ်တမ်း။
    Patient name, age, condition, drug allergies; view anytime.
    """
    patient_name = models.CharField(max_length=200, verbose_name="လူနာအမည်")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="အသက်")
    condition = models.TextField(blank=True, verbose_name="အခြေအနေ / ရောဂါဖော်ပြချက်")
    drug_allergies = models.TextField(
        blank=True,
        verbose_name="မတည့်သောဆေးများ",
        help_text="Comma-separated or one per line"
    )
    notes = models.TextField(blank=True, verbose_name="မှတ်ချက်")
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='treatment_records',
        verbose_name="ဖောက်သည်မှတ်တမ်း (optional)"
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "ကုသမှုမှတ်တမ်း"
        verbose_name_plural = "ကုသမှုမှတ်တမ်းများ"

    def __str__(self):
        return f"{self.patient_name} ({self.created_at.date()})"


class TreatmentRecordFile(models.Model):
    """ဓာတ်မှန် / X-ray, Ultrasound စသည့် ပုံများ မှတ်တမ်းတင်ခြင်း"""
    FILE_TYPE_CHOICES = (
        ('xray', 'X-Ray'),
        ('ultrasound', 'Ultrasound'),
        ('other', 'Other'),
    )
    treatment_record = models.ForeignKey(
        TreatmentRecord, on_delete=models.CASCADE, related_name='files'
    )
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file = models.FileField(upload_to='treatment_files/%Y/%m/', verbose_name="ဖိုင်")
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "ကုသမှုဖိုင်"
        verbose_name_plural = "ကုသမှုဖိုင်များ"