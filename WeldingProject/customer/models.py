# customer/models.py
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    preferred_branch = models.ForeignKey(
        'inventory.Location', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='preferred_customers',
        help_text="ကြိုက်နှစ်သက်သော ဆိုင်ခွဲ (Repair လာယူမည့်နေရာ သို့မဟုတ် ဝယ်ယူမှုအတွက်)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

