"""
Inventory services: price sync, bundle validation, rounding.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q


def round_to_nearest(amount, base=100):
    """
    Round amount to nearest base. E.g. 453214 with base=100 -> 453200; base=500 -> 453500.
    """
    if base <= 0:
        return amount
    amount = Decimal(str(amount))
    base = Decimal(str(base))
    return (amount / base).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * base


def get_usd_exchange_rate():
    """
    Get current active USD exchange rate using hybrid system.
    
    Returns:
        Decimal: Active USD rate (MMK per 1 USD) or None
        
    Uses get_active_usd_rate property which respects is_auto_sync flag.
    """
    from .models import GlobalSetting
    row = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
    if row:
        return row.get_active_usd_rate
    return None


def sync_prices_on_rate_change(new_rate, round_base=100):
    """
    Auto-sync DYNAMIC_USD product prices when exchange rate changes.
    Called by signals or manual triggers.
    
    Args:
        new_rate: Decimal - New exchange rate
        round_base: int - Rounding base (default 100)
        
    Returns:
        int: Number of products updated
    """
    return sync_all_prices(new_rate, round_base=round_base)


def update_selling_prices():
    """
    Fetch usd_exchange_rate from GlobalSetting; for all products with price_type=='DYNAMIC_USD',
    set selling_price_mmk = (cost_usd * exchange_rate) * (1 + markup_percentage/100).
    Does not round (use sync_all_prices for rounding). Updates in bulk.
    """
    from .models import Product, GlobalSetting
    rate = get_usd_exchange_rate()
    if rate is None:
        return 0
    rate = Decimal(str(rate))
    products = list(
        Product.objects.filter(price_type='DYNAMIC_USD').exclude(cost_usd__isnull=True)
    )
    for p in products:
        cost = p.cost_usd or Decimal('0')
        markup = (p.markup_percentage or Decimal('0')) / Decimal('100')
        p.selling_price_mmk = (cost * rate) * (Decimal('1') + markup)
    if products:
        Product.objects.bulk_update(products, ['selling_price_mmk'])
    return len(products)


def sync_all_prices(exchange_rate, round_base=100):
    """
    Bulk price update: all products with price_type=='DYNAMIC_USD'.
    new_price = (cost_usd * exchange_rate) * (1 + markup_percentage/100), then round_to_nearest(price, round_base).
    Uses bulk_update for one DB round-trip.
    """
    from .models import Product, GlobalSetting
    rate = Decimal(str(exchange_rate))
    products = list(
        Product.objects.filter(price_type='DYNAMIC_USD').exclude(cost_usd__isnull=True)
    )
    for p in products:
        cost = p.cost_usd or Decimal('0')
        markup = (p.markup_percentage or Decimal('0')) / Decimal('100')
        raw = (cost * rate) * (Decimal('1') + markup)
        p.selling_price_mmk = round_to_nearest(raw, round_base)
    if products:
        Product.objects.bulk_update(products, ['selling_price_mmk'])
    # Optionally persist rate to GlobalSetting
    gs, _ = GlobalSetting.objects.get_or_create(key='usd_exchange_rate', defaults={'value_decimal': rate})
    if gs.value_decimal != rate:
        gs.value_decimal = rate
        gs.save(update_fields=['value_decimal'])
    return len(products)


def validate_bundle(bundle, selected_items):
    """
    selected_items: list of dicts with 'product_id' and 'quantity' (or product + quantity).
    Returns dict: { 'valid': bool, 'warnings': [str], 'missing_required': [str] }.
    If a required component (e.g. CPU) is missing or below min_qty, add to missing_required and set valid=False.
    """
    from .models import BundleComponent
    warnings = []
    missing_required = []
    # Build selected qty by product_id
    by_product = {}
    for item in selected_items:
        pid = item.get('product_id') or (item.get('product') if isinstance(item.get('product'), int) else item.get('product', {}).get('id'))
        if pid is None and 'product' in item:
            pid = item['product']
        qty = item.get('quantity', 0)
        if pid is not None:
            by_product[int(pid)] = by_product.get(int(pid), 0) + int(qty)
    # Check each required component
    components = BundleComponent.objects.filter(bundle=bundle).select_related('product')
    for comp in components:
        qty = by_product.get(comp.product_id, 0)
        if comp.is_required and qty < comp.min_qty:
            missing_required.append(
                f"Required: {comp.product.name} (min {comp.min_qty})"
            )
        if qty > comp.max_qty:
            warnings.append(
                f"{comp.product.name}: quantity {qty} exceeds max {comp.max_qty}"
            )
    valid = len(missing_required) == 0
    return {
        'valid': valid,
        'warnings': warnings,
        'missing_required': missing_required,
    }


def bundle_total_price(bundle, selected_items, get_unit_price):
    """
    get_unit_price(product) -> Decimal (unit price in MMK).
    Returns (subtotal, discount_amount, total).
    - FIXED_BUNDLE: total = bundle.bundle_price (constant).
    - CUSTOM_SET: subtotal = sum( get_unit_price(p) * qty ) for selected_items.
    Then apply global discount: discount_type PERCENTAGE -> discount_value % of subtotal;
    FIXED_AMOUNT -> discount_value MMK. total = subtotal - discount_amount.
    """
    from decimal import Decimal
    subtotal = Decimal('0')
    for item in selected_items:
        product = item.get('product')  # may be id or object
        if isinstance(product, int):
            from .models import Product
            product = Product.objects.filter(pk=product).first()
        if not product:
            continue
        qty = Decimal(str(item.get('quantity', 0)))
        unit = get_unit_price(product)
        if unit is None:
            unit = getattr(product, 'effective_selling_price_mmk', None) or getattr(product, 'retail_price', 0)
        subtotal += Decimal(str(unit)) * qty

    if getattr(bundle, 'pricing_type', None) == 'FIXED_BUNDLE' and bundle.bundle_price is not None:
        subtotal = Decimal(str(bundle.bundle_price))

    discount_amount = Decimal('0')
    if getattr(bundle, 'discount_type', None) and getattr(bundle, 'discount_value', None):
        dv = Decimal(str(bundle.discount_value))
        if bundle.discount_type == 'PERCENTAGE':
            discount_amount = (subtotal * dv) / Decimal('100')
        elif bundle.discount_type == 'FIXED_AMOUNT':
            discount_amount = dv
    total = max(Decimal('0'), subtotal - discount_amount)
    return (subtotal, discount_amount, total)
