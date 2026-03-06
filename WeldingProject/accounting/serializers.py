from rest_framework import serializers
from .models import ExpenseCategory, Expense, Transaction


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'outlet', 'category', 'category_name', 'description', 'amount',
            'expense_date', 'created_by', 'created_by_username', 'created_at', 'notes'
        ]
        read_only_fields = ['created_by', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    sale_invoice = serializers.CharField(source='sale_transaction.invoice_number', read_only=True, allow_null=True)
    expense_description = serializers.CharField(source='expense.description', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'sale_transaction', 'sale_invoice',
            'expense', 'expense_description', 'amount', 'transaction_date', 'created_at'
        ]
        read_only_fields = ['created_at']


class PnLSummarySerializer(serializers.Serializer):
    """Serializer for P&L calculation results"""
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit_margin_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    transaction_count = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class ProfitMarginAnalysisSerializer(serializers.Serializer):
    """Serializer for profit margin analysis"""
    is_shrinking = serializers.BooleanField()
    current_margin = serializers.DecimalField(max_digits=6, decimal_places=2)
    previous_margin = serializers.DecimalField(max_digits=6, decimal_places=2)
    margin_change = serializers.DecimalField(max_digits=6, decimal_places=2)
    usd_rate_change_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    usd_rising = serializers.BooleanField()
    suggestion = serializers.CharField()
