"""
Celery tasks for background jobs (Exchange Rate Fetching, etc.)
Requires: celery, redis
Install: pip install celery redis
"""
from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task(name='inventory.fetch_exchange_rates_daily')
def fetch_exchange_rates_daily():
    """
    Daily task to fetch exchange rates from CBM API.
    Scheduled to run at 10:00 AM daily.
    """
    try:
        logger.info('Starting daily exchange rate fetch...')
        call_command('fetch_exchange_rates')
        logger.info('Exchange rate fetch completed successfully')
        return {'status': 'success', 'message': 'Exchange rates fetched successfully'}
    except Exception as e:
        logger.error(f'Exchange rate fetch failed: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(name='inventory.fetch_exchange_rates_now')
def fetch_exchange_rates_now():
    """
    Manual trigger for exchange rate fetch (can be called from admin or API).
    """
    return fetch_exchange_rates_daily()


@shared_task(name='inventory.bulk_import_products', bind=True)
def bulk_import_products(self, payload, user_id):
    """Background bulk import for files >500 rows (see ProductBulkImportView).

    Payload: {rows, columns, mapping, location_id}. Reuses the same row logic
    as the inline path; result is the task return value (query via Celery
    result backend). Never raises: per-row errors are collected.
    """
    from decimal import Decimal, InvalidOperation
    from django.contrib.auth import get_user_model
    from .models import Category, InventoryMovement, Location, Product
    from .services import generate_unique_sku

    def safe_decimal(val, default=None):
        if val is None:
            return default
        if isinstance(val, float) and __import__('math').isnan(val):
            return default
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        try:
            return Decimal(str(val).strip())
        except (InvalidOperation, ValueError):
            return default

    def safe_str(val, max_len):
        if val is None:
            return ''
        s = str(val).strip()
        return s[:max_len]

    def safe_int(val, default=0):
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return default

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'imported': 0, 'updated': 0, 'failed': 0,
                'errors': [{'row': 0, 'reason': 'Uploading user no longer exists.'}]}
    rows = payload.get('rows') or []
    mapping = payload.get('mapping') or {}
    location = None
    try:
        if payload.get('location_id'):
            location = Location.objects.get(pk=int(payload['location_id']))
    except (Location.DoesNotExist, ValueError):
        location = None
    if not location:
        location = Location.objects.filter(is_sale_location=True).first()

    rename = {}
    for col in (payload.get('columns') or []):
        if str(col).strip() in mapping:
            rename[col] = mapping[str(col).strip()]

    imported = updated = failed = 0
    errors = []
    for i, row in enumerate(rows):
        row_num = i + 2
        mapped = {rename.get(k, k): v for k, v in row.items()}

        def get(field):
            v = mapped.get(field)
            if v is None or (isinstance(v, float) and __import__('math').isnan(v)):
                return None
            return v

        from django.db import transaction
        model_no = safe_str(get('model_no'), 100)
        name_val = safe_str(get('name'), 200)
        sku_val = safe_str(get('sku'), 50)
        quantity_val = safe_decimal(get('quantity'), None)
        if quantity_val is not None and quantity_val < 0:
            quantity_val = Decimal('0')
        existing = Product.objects.filter(model_no=model_no).first() if model_no else None
        if existing:
            if quantity_val is not None and quantity_val > 0 and location:
                try:
                    with transaction.atomic():
                        InventoryMovement.objects.create(
                            product=existing, quantity=quantity_val,
                            movement_type='inbound', to_location=location,
                            from_location=None, moved_by=user,
                            notes='Bulk import stock (background)',
                            outlet_id=location.outlet_id,
                        )
                    updated += 1
                except Exception as e:
                    failed += 1
                    errors.append({'row': row_num, 'reason': f'Stock update failed: {e}'})
            else:
                updated += 1
            continue
        if not name_val:
            failed += 1
            errors.append({'row': row_num, 'reason': 'Missing mandatory field: name.'})
            continue
        if not sku_val or Product.objects.filter(sku=sku_val).exists():
            sku_val = generate_unique_sku(name_val)
        category = None
        cat_name = safe_str(get('category_name'), 100)
        if cat_name:
            category = Category.objects.filter(name__iexact=cat_name).first()
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    name=name_val, sku=sku_val, model_no=model_no or None,
                    category=category,
                    retail_price=safe_decimal(get('retail_price'), Decimal('0')) or Decimal('0'),
                    cost_price=safe_decimal(get('cost_price'), Decimal('0')) or Decimal('0'),
                    warranty_months=max(0, safe_int(get('warranty_months'), 0)),
                    is_serial_tracked=bool(get('is_serial_tracked')),
                    serial_number_required=bool(get('serial_number_required')),
                )
                if quantity_val is not None and quantity_val > 0 and location:
                    InventoryMovement.objects.create(
                        product=product, quantity=quantity_val,
                        movement_type='inbound', to_location=location,
                        from_location=None, moved_by=user, notes='Bulk import (background)',
                        outlet_id=location.outlet_id,
                    )
                imported += 1
        except Exception as e:
            failed += 1
            errors.append({'row': row_num, 'reason': str(e)})
    return {'imported': imported, 'updated': updated, 'failed': failed, 'errors': errors}
