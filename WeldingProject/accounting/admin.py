from django.contrib import admin
from .models import ExpenseCategory, Expense, Transaction


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'description', 'amount', 'expense_date', 'created_by', 'created_at']
    list_filter = ['category', 'expense_date', 'created_at']
    search_fields = ['description', 'notes']
    date_hierarchy = 'expense_date'
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'amount', 'transaction_date', 'sale_transaction', 'expense', 'created_at']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['sale_transaction__invoice_number', 'expense__description']
    date_hierarchy = 'transaction_date'
    readonly_fields = ['created_at']
