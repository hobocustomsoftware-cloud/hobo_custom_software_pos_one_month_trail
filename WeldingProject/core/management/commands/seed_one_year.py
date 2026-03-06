"""
တစ်နှစ်စာ စမ်းသပ်ဒေတာ ထုတ်ခြင်း (manual data မရှိလို့ CMD ကနေ run ပြီး screenshot / load test အတွက်)
Run: python manage.py seed_one_year [--months 12] [--sales-per-month 50] [--repairs-per-month 10]
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


def _safe_str(s):
    try:
        return str(s).encode('ascii', 'replace').decode('ascii')
    except Exception:
        return str(s)[:50]


class Command(BaseCommand):
    help = 'Seed ~1 year of fake data for testing/screenshots and load sizing (marketing).'

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=12, help='Number of months of data (default 12)')
        parser.add_argument('--sales-per-month', type=int, default=50, help='Approx sales per month')
        parser.add_argument('--repairs-per-month', type=int, default=10, help='Approx repairs per month')
        parser.add_argument('--customers', type=int, default=80, help='Total customers to create')
        parser.add_argument('--products', type=int, default=30, help='Products if none exist')

    def handle(self, *args, **options):
        months = max(1, min(options['months'], 24))
        sales_per_month = max(1, min(options['sales_per_month'], 200))
        repairs_per_month = max(0, min(options['repairs_per_month'], 50))
        n_customers = max(1, min(options['customers'], 500))
        n_products = max(1, min(options['products'], 100))

        # Avoid Redis for this command
        from django.conf import settings
        settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

        from django.contrib.auth import get_user_model
        from core.models import User, Role
        from inventory.models import (
            Category, Product, Location, InventoryMovement,
            SaleTransaction, SaleItem,
        )
        from customer.models import Customer
        from service.models import RepairService

        User = get_user_model()
        self.stdout.write(self.style.MIGRATE_HEADING('Seed one year data (for testing/screenshots & load sizing)'))

        # --- Roles & User ---
        owner_role, _ = Role.objects.get_or_create(name='owner', defaults={'description': 'Owner'})
        staff_role, _ = Role.objects.get_or_create(name='sale_staff', defaults={'description': 'Sale Staff'})
        owner = User.objects.filter(role_obj=owner_role).first() or User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not owner:
            owner = User.objects.create_user(
                username='seed_owner', first_name='Seed', last_name='Owner',
                role_obj=owner_role, is_staff=True, is_active=True,
            )
            owner.set_password('demo123')
            owner.save()
            self.stdout.write(self.style.SUCCESS('  Created user: seed_owner / demo123'))

        # --- Location ---
        loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            loc = Location.objects.create(
                name='Main Branch',
                location_type='branch',
                is_sale_location=True,
            )
            self.stdout.write(self.style.SUCCESS('  Created Location: Main Branch'))

        # --- Categories & Products ---
        categories = list(Category.objects.all())
        if not categories:
            names = ['Electronics', 'Tools', 'Spare Parts', 'Consumables']
            for n in names:
                categories.append(Category.objects.create(name=n, description='Seed'))
            self.stdout.write(self.style.SUCCESS('  Created %s categories' % len(categories)))

        products = list(Product.objects.all())
        if len(products) < n_products:
            from inventory.models import Product as P
            for i in range(n_products - len(products)):
                cat = random.choice(categories)
                sku = 'SEED-%s-%03d' % (random.randint(100, 999), i + 1)
                if P.objects.filter(sku=sku).exists():
                    continue
                p = P.objects.create(
                    name='Product %s' % (i + 1),
                    sku=sku,
                    category=cat,
                    retail_price=Decimal(str(round(random.uniform(5000, 150000), 2))),
                    cost_price=Decimal(str(round(random.uniform(2000, 80000), 2))),
                )
                products.append(p)
            self.stdout.write(self.style.SUCCESS('  Products: %s' % Product.objects.count()))

        if not products:
            self.stderr.write(self.style.ERROR('No products. Create at least one product.'))
            return

        # --- Stock (inbound) so we can create sales ---
        for p in products[:20]:  # first 20 products get stock
            from django.db.models import Sum
            from django.db.models.functions import Coalesce
            inv = p.inventorymovement_set.filter(to_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
            out = p.inventorymovement_set.filter(from_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
            if (inv - out) < 100:
                InventoryMovement.objects.create(
                    product=p, quantity=200, movement_type='inbound',
                    to_location=loc, from_location=None, moved_by=owner,
                )
        self.stdout.write(self.style.SUCCESS('  Stock (inbound) ensured for products'))

        # --- Customers ---
        existing_customers = list(Customer.objects.all())
        for i in range(n_customers - len(existing_customers)):
            if i >= 500:
                break
            phone = '09%02d%06d' % (random.randint(1, 99), random.randint(0, 999999))
            if Customer.objects.filter(phone_number=phone).exists():
                continue
            Customer.objects.create(
                name='Customer %s' % (Customer.objects.count() + 1),
                phone_number=phone,
                preferred_branch=loc,
            )
        all_customers = list(Customer.objects.all())
        self.stdout.write(self.style.SUCCESS('  Customers: %s' % len(all_customers)))

        # --- Sales over the past N months ---
        now = timezone.now()
        total_sales = 0
        for m in range(months):
            # month start/end
            month_start = now - timedelta(days=30 * (months - m))
            month_end = month_start + timedelta(days=30)
            n_sales = sales_per_month + random.randint(-10, 10)
            n_sales = max(1, n_sales)
            for _ in range(n_sales):
                when = month_start + timedelta(
                    seconds=random.randint(0, int((month_end - month_start).total_seconds()))
                )
                with transaction.atomic():
                    sale = SaleTransaction.objects.create(
                        staff=owner,
                        sale_location=loc,
                        customer=random.choice(all_customers) if all_customers else None,
                        total_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        status='approved',
                        approved_by=owner,
                        approved_at=when,
                    )
                    # 1–3 items per sale
                    items_count = random.randint(1, min(3, len(products)))
                    chosen = random.sample(products, items_count)
                    tot = Decimal('0')
                    for p in chosen:
                        qty = random.randint(1, 3)
                        up = p.retail_price
                        st = up * qty
                        SaleItem.objects.create(
                            sale_transaction=sale,
                            product=p,
                            quantity=qty,
                            unit_price=up,
                            subtotal=st,
                        )
                        tot += st
                        InventoryMovement.objects.create(
                            product=p,
                            quantity=qty,
                            movement_type='outbound',
                            from_location=loc,
                            moved_by=owner,
                            sale_transaction=sale,
                        )
                    sale.total_amount = tot
                    sale.save(update_fields=['total_amount'])
                    SaleTransaction.objects.filter(pk=sale.pk).update(created_at=when)
                    total_sales += 1
        self.stdout.write(self.style.SUCCESS('  Sales (approved): %s over %s months' % (total_sales, months)))

        # --- Repairs over the past N months ---
        total_repairs = 0
        statuses = ['received', 'fixing', 'ready', 'completed', 'completed', 'cancelled']
        for m in range(months):
            month_start = now - timedelta(days=30 * (months - m))
            month_end = month_start + timedelta(days=30)
            n_rep = repairs_per_month + random.randint(-2, 2)
            n_rep = max(0, n_rep)
            for _ in range(n_rep):
                when = month_start + timedelta(
                    seconds=random.randint(0, int((month_end - month_start).total_seconds()))
                )
                c = random.choice(all_customers) if all_customers else None
                if not c:
                    continue
                return_date = (when + timedelta(days=random.randint(3, 14))).date() if hasattr(when, 'date') else (when + timedelta(days=7)).date()
                rep = RepairService.objects.create(
                    customer=c,
                    item_name='Device %s' % random.randint(1000, 9999),
                    problem_description='Seed repair for testing.',
                    location=loc,
                    labour_cost=Decimal(str(round(random.uniform(5000, 30000), 2))),
                    total_estimated_cost=Decimal(str(round(random.uniform(10000, 50000), 2))),
                    deposit_amount=Decimal('0'),
                    status=random.choice(statuses),
                    return_date=return_date,
                    staff=owner,
                )
                RepairService.objects.filter(pk=rep.pk).update(created_at=when, received_date=when)
                total_repairs += 1
        self.stdout.write(self.style.SUCCESS('  Repairs: %s over %s months' % (total_repairs, months)))

        self.stdout.write(self.style.SUCCESS('\nDone. Use this DB for CMD screenshot run and load test (marketing).'))
