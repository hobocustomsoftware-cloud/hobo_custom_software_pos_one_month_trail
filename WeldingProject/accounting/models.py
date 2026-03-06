"""
Accounting & P&L Module
- Expense: ကုန်ကျစရိတ်များ (rent, utilities, salaries, etc.)
- Transaction: Unified model linking Income (SaleTransaction) and Expenses
- Real-time P&L calculation service
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.Model):
    """ကုန်ကျစရိတ် အမျိုးအစားများ"""
    name = models.CharField(max_length=100, unique=True, verbose_name="အမျိုးအစားအမည်")
    description = models.TextField(blank=True, null=True, verbose_name="ဖော်ပြချက်")
    
    class Meta:
        verbose_name = "ကုန်ကျစရိတ် အမျိုးအစား"
        verbose_name_plural = "ကုန်ကျစရိတ် အမျိုးအစားများ"
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    ကုန်ကျစရိတ်များ (Rent, Utilities, Salaries, Supplies, etc.)
    Outlet-scoped for multi-branch isolation.
    """
    outlet = models.ForeignKey(
        'core.Outlet',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="Outlet"
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        verbose_name="အမျိုးအစား"
    )
    description = models.CharField(max_length=200, verbose_name="ဖော်ပြချက်")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="ငွေပမာဏ (MMK)"
    )
    expense_date = models.DateField(
        default=timezone.now,
        verbose_name="ကုန်ကျသည့်ရက်စွဲ"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="မှတ်တမ်းတင်သူ"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, verbose_name="မှတ်ချက်")
    
    class Meta:
        verbose_name = "ကုန်ကျစရိတ်"
        verbose_name_plural = "ကုန်ကျစရိတ်များ"
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.category.name} - {self.description} ({self.amount} MMK)"


class Transaction(models.Model):
    """
    Unified Transaction Model linking Income (SaleTransaction) and Expenses
    
    Transaction Type:
    - INCOME: Links to SaleTransaction (approved sales)
    - EXPENSE: Links to Expense model
    """
    TRANSACTION_TYPE_CHOICES = (
        ('income', 'Income (ဝင်ငွေ)'),
        ('expense', 'Expense (ကုန်ကျစရိတ်)'),
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name="Transaction Type"
    )
    
    # Income: Link to SaleTransaction
    sale_transaction = models.ForeignKey(
        'inventory.SaleTransaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='accounting_transactions',
        verbose_name="ရောင်းချမှု"
    )
    
    # Expense: Link to Expense
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="ကုန်ကျစရိတ်"
    )
    
    # Amount (positive for income, negative for expense)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="ငွေပမာဏ"
    )
    
    # Transaction date
    transaction_date = models.DateField(
        default=timezone.now,
        db_index=True,
        verbose_name="Transaction Date"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['transaction_date']),
        ]
    
    def __str__(self):
        if self.transaction_type == 'income':
            return f"Income: {self.sale_transaction.invoice_number if self.sale_transaction else 'N/A'} - {self.amount} MMK"
        else:
            return f"Expense: {self.expense.description if self.expense else 'N/A'} - {self.amount} MMK"
    
    def save(self, *args, **kwargs):
        """
        Auto-set amount based on linked model:
        - Income: from SaleTransaction.total_amount
        - Expense: from Expense.amount (negative)
        """
        if self.transaction_type == 'income' and self.sale_transaction:
            self.amount = self.sale_transaction.total_amount
        elif self.transaction_type == 'expense' and self.expense:
            self.amount = -abs(self.expense.amount)  # Negative for expenses
        
        super().save(*args, **kwargs)
