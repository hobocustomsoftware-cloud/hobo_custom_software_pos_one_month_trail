"""
Create approved sales for a specific date (for Playwright/monthly report simulation).
Run: python manage.py create_sales_for_date 2025-01-15 --count 3
Uses InMemory channel layer to avoid Redis.
"""
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create approved sales for a given date (YYYY-MM-DD). For automation/screenshots.'

    def add_arguments(self, parser):
        parser.add_argument('date', help='Date YYYY-MM-DD')
        parser.add_argument('--count', type=int, default=3, help='Number of sales to create')

    def handle(self, *args, **options):
        settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
        try:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write(self.style.ERROR('Invalid date. Use YYYY-MM-DD.'))
            return
        count = max(1, min(options['count'], 20))

        from django.contrib.auth import get_user_model
        from inventory.models import (
            Location, Product, Category, SaleTransaction, SaleItem,
            InventoryMovement,
        )
        from django.db import transaction

        User = get_user_model()
        loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            loc = Location.objects.create(name='Sim Branch', location_type='branch', is_sale_location=True)
        prod = Product.objects.first()
        if not prod:
            cat = Category.objects.first() or Category.objects.create(name='Sim Cat')
            prod = Product.objects.create(name='SimProduct', sku='SIM-001', category=cat, retail_price=10000, cost_price=5000)
        owner = User.objects.filter(role_obj__name__icontains='owner').first() or User.objects.first()
        if not owner:
            self.stderr.write(self.style.ERROR('No user found. Run seed_demo_users or register first.'))
            return

        # Ensure stock
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        stock_in = prod.inventorymovement_set.filter(to_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
        stock_out = prod.inventorymovement_set.filter(from_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
        if (stock_in - stock_out) < count:
            InventoryMovement.objects.create(
                product=prod, quantity=count + 10, movement_type='inbound',
                to_location=loc, from_location=None, moved_by=owner,
            )

        created = 0
        target_dt = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        for _ in range(count):
            with transaction.atomic():
                sale = SaleTransaction.objects.create(
                    staff=owner, sale_location=loc, customer=None,
                    total_amount=0, discount_amount=0, status='approved',
                    approved_by=owner, approved_at=target_dt,
                )
                item = SaleItem.objects.create(
                    sale_transaction=sale, product=prod, quantity=1,
                    unit_price=prod.retail_price, subtotal=prod.retail_price,
                )
                sale.total_amount = item.subtotal
                sale.save(update_fields=['total_amount'])
                InventoryMovement.objects.create(
                    product=prod, quantity=1, movement_type='outbound',
                    from_location=loc, moved_by=owner, sale_transaction=sale,
                )
                SaleTransaction.objects.filter(pk=sale.pk).update(created_at=target_dt)
                created += 1
        self.stdout.write(self.style.SUCCESS('Created %s sales for %s' % (created, target_date)))
