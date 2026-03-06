"""
P&L Calculation Service
Real-time profit & loss calculation with USD inflation analysis
"""
from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, date


def calculate_net_profit(start_date=None, end_date=None, outlet_id=None):
    """
    Calculate Net Profit (ဝင်ငွေ - ကုန်ကျစရိတ်) for a date range.
    outlet_id: optional; when set, filter to that outlet (income from sale_transaction, expense from expense).
    
    Returns:
        {
            'total_income': Decimal,
            'total_expenses': Decimal,
            'net_profit': Decimal,
            'profit_margin_percent': Decimal,
            'transaction_count': int
        }
    """
    from .models import Transaction
    
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        start_date = end_date - timedelta(days=30)  # Last 30 days default
    
    transactions = Transaction.objects.filter(
        transaction_date__gte=start_date,
        transaction_date__lte=end_date
    )
    if outlet_id is not None:
        transactions = transactions.filter(
            Q(sale_transaction__outlet_id=outlet_id) | Q(expense__outlet_id=outlet_id)
        )
    
    # Calculate totals
    income_sum = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    expense_sum = abs(transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0'))
    
    net_profit = income_sum - expense_sum
    
    # Profit margin percentage
    profit_margin = Decimal('0')
    if income_sum > 0:
        profit_margin = (net_profit / income_sum) * Decimal('100')
    
    return {
        'total_income': income_sum,
        'total_expenses': expense_sum,
        'net_profit': net_profit,
        'profit_margin_percent': profit_margin,
        'transaction_count': transactions.count(),
        'start_date': start_date,
        'end_date': end_date,
    }


def calculate_profit_from_sales(start_date=None, end_date=None, outlet_id=None):
    """
    Calculate profit from sales only (excluding expenses).
    outlet_id: optional; when set, filter sales to that outlet.
    
    Returns:
        {
            'total_revenue': Decimal,
            'total_cost': Decimal,
            'gross_profit': Decimal,
            'gross_profit_margin_percent': Decimal
        }
    """
    from inventory.models import SaleTransaction, SaleItem
    
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    sales = SaleTransaction.objects.filter(
        status='approved',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    if outlet_id is not None:
        sales = sales.filter(outlet_id=outlet_id)
    
    total_revenue = Decimal('0')
    total_cost = Decimal('0')
    
    for sale in sales:
        total_revenue += sale.total_amount
        
        # Calculate cost from sale items
        for item in sale.sale_items.all():
            product = item.product
            # Get cost price (use cost_usd * rate if DYNAMIC_USD, else cost_price)
            cost_per_unit = product.cost_price or Decimal('0')
            
            # If DYNAMIC_USD, calculate cost from USD
            if product.price_type == 'DYNAMIC_USD' and product.cost_usd:
                from inventory.models import GlobalSetting
                gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
                if gs and gs.value_decimal:
                    usd_rate = gs.value_decimal
                    cost_per_unit = product.cost_usd * usd_rate
            
            total_cost += cost_per_unit * item.quantity
    
    gross_profit = total_revenue - total_cost
    gross_profit_margin = Decimal('0')
    if total_revenue > 0:
        gross_profit_margin = (gross_profit / total_revenue) * Decimal('100')
    
    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'gross_profit': gross_profit,
        'gross_profit_margin_percent': gross_profit_margin,
        'start_date': start_date,
        'end_date': end_date,
    }


def get_pnl_by_outlet(start_date=None, end_date=None):
    """
    Owner only: P&L per outlet for chart.
    Returns list of {outlet_id, outlet_name, total_income, total_expenses, net_profit}.
    """
    from core.models import Outlet
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    outlets = Outlet.objects.filter(is_active=True).order_by('-is_main_branch', 'name')
    result = []
    for outlet in outlets:
        pnl = calculate_net_profit(start_date, end_date, outlet_id=outlet.id)
        result.append({
            'outlet_id': outlet.id,
            'outlet_name': outlet.name,
            'total_income': pnl['total_income'],
            'total_expenses': pnl['total_expenses'],
            'net_profit': pnl['net_profit'],
        })
    return result


def get_profit_trend(days=30):
    """
    Get daily profit trend for the last N days.
    Returns list of {date, income, expenses, net_profit, profit_margin}
    """
    from .models import Transaction
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    transactions = Transaction.objects.filter(
        transaction_date__gte=start_date,
        transaction_date__lte=end_date
    ).values('transaction_date').annotate(
        income=Sum('amount', filter=Q(transaction_type='income')),
        expenses=Sum('amount', filter=Q(transaction_type='expense'))
    ).order_by('transaction_date')
    
    trend = []
    for day_data in transactions:
        date_val = day_data['transaction_date']
        income = day_data['income'] or Decimal('0')
        expenses = abs(day_data['expenses'] or Decimal('0'))
        net_profit = income - expenses
        
        profit_margin = Decimal('0')
        if income > 0:
            profit_margin = (net_profit / income) * Decimal('100')
        
        trend.append({
            'date': date_val,
            'income': income,
            'expenses': expenses,
            'net_profit': net_profit,
            'profit_margin_percent': profit_margin,
        })
    
    return trend


def analyze_profit_margin_shrinkage():
    """
    Analyze if profit margin is shrinking due to USD inflation.
    
    Returns:
        {
            'is_shrinking': bool,
            'current_margin': Decimal,
            'previous_margin': Decimal,
            'usd_rate_change_percent': Decimal,
            'suggestion': str (Burmese)
        }
    """
    from inventory.models import GlobalSetting, ExchangeRateLog
    
    # Get current and previous profit margins (last 7 days vs previous 7 days)
    today = timezone.now().date()
    current_period_start = today - timedelta(days=7)
    previous_period_start = today - timedelta(days=14)
    
    current_pnl = calculate_profit_from_sales(current_period_start, today)
    previous_pnl = calculate_profit_from_sales(previous_period_start, current_period_start)
    
    current_margin = current_pnl['gross_profit_margin_percent']
    previous_margin = previous_pnl['gross_profit_margin_percent']
    
    # Get USD rate change
    gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
    current_rate = float(gs.value_decimal) if gs and gs.value_decimal else None
    
    logs = ExchangeRateLog.objects.filter(
        date__lt=today
    ).order_by('-date')[:7]
    
    usd_rate_change = Decimal('0')
    if current_rate and logs.exists():
        avg_previous_rate = sum(float(log.rate) for log in logs) / logs.count()
        if avg_previous_rate > 0:
            usd_rate_change = ((Decimal(str(current_rate)) - Decimal(str(avg_previous_rate))) / Decimal(str(avg_previous_rate))) * Decimal('100')
    
    # Check if margin is shrinking
    margin_change = current_margin - previous_margin
    is_shrinking = margin_change < Decimal('-2')  # More than 2% drop
    
    # Check if USD is rising significantly
    usd_rising = usd_rate_change > Decimal('2')  # More than 2% increase
    
    suggestion = ""
    if is_shrinking and usd_rising:
        suggestion = f"ဒေါ်လာဈေး {usd_rate_change:.1f}% တက်နေပြီး အမြတ်အစွန်း {abs(margin_change):.1f}% ကျဆင်းနေပါသည်။ ဈေးနှုန်းများ ပြန်လည်သုံးသပ်ရန် အကြံပြုပါသည်။"
    elif is_shrinking:
        suggestion = f"အမြတ်အစွန်း {abs(margin_change):.1f}% ကျဆင်းနေပါသည်။ ကုန်ကျစရိတ်များကို စစ်ဆေးရန် အကြံပြုပါသည်။"
    elif usd_rising:
        suggestion = f"ဒေါ်လာဈေး {usd_rate_change:.1f}% တက်နေပါသည်။ ဈေးနှုန်းများ စဉ်းစားရန် အကြံပြုပါသည်။"
    
    return {
        'is_shrinking': is_shrinking,
        'current_margin': current_margin,
        'previous_margin': previous_margin,
        'margin_change': margin_change,
        'usd_rate_change_percent': usd_rate_change,
        'usd_rising': usd_rising,
        'suggestion': suggestion,
    }
