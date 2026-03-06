"""
ဆေးဆိုင် တစ်လစာ demo data – Register/Setup ပြီးသား ဆိုင်အတွက် ရက်လိုက် အရောင်းများ ထည့်ပေးမယ်။
Run: python manage.py seed_pharmacy_month [--days 30] [--sales-per-day 3]
- Location / Category / Product မရှိရင် ဆေးဆိုင်အတွက် ဖန်တီးမယ်။
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


class Command(BaseCommand):
    help = 'Seed one month of pharmacy sales (for demo after register+setup).'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to seed')
        parser.add_argument('--sales-per-day', type=int, default=3, help='Min–max sales per day (random up to this)')

    def handle(self, *args, **options):
        days = max(1, min(options['days'], 90))
        per_day = max(1, min(options['sales_per_day'], 10))

        from django.contrib.auth import get_user_model
        from core.models import Outlet
        from inventory.models import (
            Location, Product, Category, SaleTransaction, SaleItem,
            InventoryMovement,
        )
        import random

        User = get_user_model()
        owner = User.objects.filter(role_obj__name__icontains='owner').first() or User.objects.first()
        if not owner:
            self.stderr.write(self.style.ERROR('No user found. Register first in the browser.'))
            return

        # Ensure sale location (outlet creates warehouse + shopfloor via signal)
        loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            outlet = Outlet.objects.filter(is_main_branch=True).first()
            if not outlet:
                outlet = Outlet.objects.create(
                    name='Main Branch',
                    code='MAIN',
                    is_main_branch=True,
                )
            loc = outlet.get_shopfloor_location() or Location.objects.filter(
                outlet=outlet, is_sale_location=True
            ).first()
            if not loc:
                loc = Location.objects.filter(is_sale_location=True).first()
            self.stdout.write(self.style.SUCCESS('Using location: %s' % (loc.name if loc else 'created')))

        # Pharmacy category + products
        cat, _ = Category.objects.get_or_create(
            name='Pharmacy (ဆေးဆိုင်)',
            defaults={'order': 0},
        )
        products = list(Product.objects.filter(category=cat)[:5])
        if not products:
            for name, sku, price in [
                ('Paracetamol 500mg', 'PH-PARA-001', 500),
                ('Vitamin C 1000mg', 'PH-VITC-001', 800),
                ('Omeprazole 20mg', 'PH-OMEP-001', 1200),
            ]:
                p, _ = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'name': name,
                        'category': cat,
                        'retail_price': Decimal(price),
                        'cost_price': Decimal(price * 0.6),
                    },
                )
                products.append(p)
            self.stdout.write(self.style.SUCCESS('Created %s pharmacy products' % len(products)))

        # Ensure stock at location
        for prod in products:
            stock_in = prod.inventorymovement_set.filter(to_location=loc).aggregate(
                s=Coalesce(Sum('quantity'), 0)
            )['s'] or 0
            stock_out = prod.inventorymovement_set.filter(from_location=loc).aggregate(
                s=Coalesce(Sum('quantity'), 0)
            )['s'] or 0
            if (stock_in - stock_out) < (days * per_day):
                need = (days * per_day) + 50 - (stock_in - stock_out)
                InventoryMovement.objects.create(
                    product=prod,
                    quantity=max(need, 50),
                    movement_type='inbound',
                    to_location=loc,
                    moved_by=owner,
                )

        # Last N days
        today = timezone.now().date()
        start = today - timedelta(days=days)
        total_sales = 0
        for d in range(days):
            target_date = start + timedelta(days=d)
            target_dt = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
            n = random.randint(1, per_day)
            for _ in range(n):
                prod = random.choice(products)
                qty = random.randint(1, 3)
                with transaction.atomic():
                    sale = SaleTransaction.objects.create(
                        staff=owner,
                        sale_location=loc,
                        customer=None,
                        total_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        status='approved',
                        approved_by=owner,
                        approved_at=target_dt,
                    )
                    unit_price = prod.retail_price
                    subtotal = unit_price * qty
                    SaleItem.objects.create(
                        sale_transaction=sale,
                        product=prod,
                        quantity=qty,
                        unit_price=unit_price,
                        subtotal=subtotal,
                    )
                    sale.total_amount = subtotal
                    sale.save(update_fields=['total_amount'])
                    InventoryMovement.objects.create(
                        product=prod,
                        quantity=qty,
                        movement_type='outbound',
                        from_location=loc,
                        moved_by=owner,
                        sale_transaction=sale,
                    )
                    SaleTransaction.objects.filter(pk=sale.pk).update(created_at=target_dt)
                    total_sales += 1
        self.stdout.write(self.style.SUCCESS(
            'Created %s sales over %s days (pharmacy demo).' % (total_sales, days)
        ))
