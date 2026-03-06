"""
Signals to auto-create Transaction records when:
- SaleTransaction is approved (Income)
- Expense is created (Expense)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import SaleTransaction
from .models import Transaction, Expense


@receiver(post_save, sender=SaleTransaction)
def create_income_transaction(sender, instance, created, **kwargs):
    """
    Auto-create Transaction when SaleTransaction is approved.
    """
    # Only create transaction for approved sales
    if instance.status == 'approved':
        # Determine transaction date
        from django.utils import timezone
        if instance.approved_at:
            trans_date = instance.approved_at.date()
        elif instance.created_at:
            trans_date = instance.created_at.date()
        else:
            trans_date = timezone.now().date()
        
        # Check if transaction already exists
        transaction, created = Transaction.objects.get_or_create(
            sale_transaction=instance,
            defaults={
                'transaction_type': 'income',
                'transaction_date': trans_date,
            }
        )
        if not created:
            # Update existing transaction
            transaction.amount = instance.total_amount
            transaction.transaction_date = trans_date
            transaction.save()


@receiver(post_save, sender=Expense)
def create_expense_transaction(sender, instance, created, **kwargs):
    """
    Auto-create Transaction when Expense is created.
    """
    if created:
        Transaction.objects.create(
            expense=instance,
            transaction_type='expense',
            amount=-abs(instance.amount),  # Negative for expenses
            transaction_date=instance.expense_date,
        )
