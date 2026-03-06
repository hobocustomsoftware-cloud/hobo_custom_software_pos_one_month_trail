"""
1-Month Business Simulation Test – backend data only.
Run AFTER Phase 1 (Owner registration + Setup Wizard) in the browser.

Creates:
- 4 roles: Manager, Inventory_Staff, Sale_Staff, Cashier
- 500+ products (bulk simulation for Item List load test)
- 10 Inbound (purchase-style) movements
- 5 Stock Transfers / Adjustments
- 1,000+ sales over the last 30 days (for report load test)

Run: python manage.py simulation_1month_data
  (from repo root with Docker: docker compose -f compose/docker-compose.yml exec backend python manage.py simulation_1month_data)
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from django.conf import settings
settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


class Command(BaseCommand):
    help = '1-Month Simulation: roles, 500+ products, 10 inbound, 5 transfers, 1000+ sales over 30 days'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=520, help='Number of products to create (default 520)')
        parser.add_argument('--sales', type=int, default=1050, help='Number of sales over 30 days (default 1050)')
        parser.add_argument('--dry-run', action='store_true', help='Print what would be done without writing')

    def handle(self, *args, **options):
        dry = options['dry_run']
        n_products = max(500, options['products'])
        n_sales = max(1000, options['sales'])

        from django.contrib.auth import get_user_model
        from core.models import User, Role, ShopSettings, Outlet
        from inventory.models import (
            Category, Product, Location, Unit,
            InventoryMovement, SaleTransaction, SaleItem,
            Purchase, PurchaseLine,
        )
        from customer.models import Customer

        User = get_user_model()
        self.stdout.write(self.style.MIGRATE_HEADING('1-Month Business Simulation Data'))
        self.stdout.write('=' * 50)

        # --- Owner & shop ---
        owner = User.objects.filter(is_superuser=True).first() or User.objects.filter(role_obj__name__iexact='owner').first() or User.objects.order_by('id').first()
        if not owner:
            self.stderr.write(self.style.ERROR('No user found. Run Phase 1: register Owner and complete Setup Wizard in the browser first.'))
            return
        self.stdout.write(self.style.SUCCESS('  Owner: %s' % (owner.username or owner.email)))

        if not dry:
            owner_role, _ = Role.objects.get_or_create(name='owner', defaults={'description': 'Owner'})
            if not owner.role_obj_id:
                owner.role_obj = owner_role
                owner.is_staff = True
                owner.save(update_fields=['role_obj', 'is_staff'])

        # --- Outlet & locations (required for movements) ---
        main_outlet = Outlet.objects.filter(is_active=True).first()
        if not main_outlet and not dry:
            main_outlet = Outlet.objects.create(name='Main Branch', is_main_branch=True, code='MAIN')
            self.stdout.write(self.style.SUCCESS('  Created Outlet: Main Branch'))
        if main_outlet:
            wh = Location.objects.filter(outlet=main_outlet, location_type='warehouse').first()
            sf = Location.objects.filter(outlet=main_outlet, location_type='shop_floor').first()
            if not wh and not dry:
                wh = Location.objects.create(outlet=main_outlet, name='Main - Warehouse', location_type='warehouse', is_sale_location=False)
            if not sf and not dry:
                sf = Location.objects.create(outlet=main_outlet, name='Main - Shopfloor', location_type='shop_floor', is_sale_location=True)
            loc = sf or Location.objects.filter(is_sale_location=True).first() or wh
        else:
            loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            self.stderr.write(self.style.ERROR('No sale location. Complete Setup Wizard and ensure at least one outlet/location exists.'))
            return
        self.stdout.write(self.style.SUCCESS('  Sale location: %s' % loc.name))

        # --- Phase 1 (roles): Manager, Inventory_Staff, Sale_Staff, Cashier ---
        role_names = [
            ('Manager', 'Manager with oversight permissions'),
            ('Inventory_Staff', 'Inventory and stock management'),
            ('Sale_Staff', 'Sales and POS'),
            ('Cashier', 'Cashier and payments'),
        ]
        if not dry:
            for name, desc in role_names:
                Role.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write(self.style.SUCCESS('  Roles: Manager, Inventory_Staff, Sale_Staff, Cashier'))

        # --- Phase 2: 500+ products ---
        categories = list(Category.objects.all())
        if not categories and not dry:
            for n in ['Pharmacy', 'General', 'Consumables', 'Devices']:
                categories.append(Category.objects.create(name=n, description='Simulation'))
        existing_products = list(Product.objects.all())
        to_create = n_products - len(existing_products)
        if to_create > 0 and not dry:
            for i in range(to_create):
                cat = random.choice(categories) if categories else None
                sku = 'SIM-%s-%05d' % (random.randint(100, 999), Product.objects.count() + 1)
                if Product.objects.filter(sku=sku).exists():
                    continue
                Product.objects.create(
                    name='Product %s' % (Product.objects.count() + 1),
                    sku=sku,
                    category=cat,
                    retail_price=Decimal(str(round(random.uniform(500, 50000), 2))),
                    cost_price=Decimal(str(round(random.uniform(200, 20000), 2))),
                )
        self.stdout.write(self.style.SUCCESS('  Products: %s' % (n_products if dry else Product.objects.count())))

        products = list(Product.objects.all())
        if not products:
            self.stderr.write(self.style.ERROR('No products. Create categories first or run without --dry-run.'))
            return

        # --- Phase 2: 10 Inbound (purchase-style) ---
        if not dry and main_outlet and loc:
            wh = Location.objects.filter(outlet=main_outlet, location_type='warehouse').first() or loc
            for i in range(10):
                p = random.choice(products)
                qty = random.randint(10, 100)
                InventoryMovement.objects.create(
                    product=p,
                    quantity=qty,
                    movement_type='inbound',
                    to_location=wh,
                    from_location=None,
                    moved_by=owner,
                    outlet=main_outlet,
                    notes='Simulation inbound #%s' % (i + 1),
                )
            self.stdout.write(self.style.SUCCESS('  Inbound movements: 10'))

        # --- Phase 2: 5 Transfers / Adjustments ---
        if not dry and main_outlet and loc:
            wh = Location.objects.filter(outlet=main_outlet, location_type='warehouse').first()
            sf = Location.objects.filter(outlet=main_outlet, location_type='shop_floor').first()
            if wh and sf:
                for i in range(5):
                    p = random.choice(products)
                    qty = random.randint(1, 20)
                    InventoryMovement.objects.create(
                        product=p,
                        quantity=qty,
                        movement_type='transfer',
                        from_location=wh,
                        to_location=sf,
                        moved_by=owner,
                        outlet=main_outlet,
                        notes='Simulation transfer #%s' % (i + 1),
                    )
            self.stdout.write(self.style.SUCCESS('  Transfers: 5'))

        # --- Stock for sales: ensure some stock at sale location ---
        if not dry:
            from django.db.models import Sum
            from django.db.models.functions import Coalesce
            for p in products[:100]:
                inv = p.inventorymovement_set.filter(to_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
                out = p.inventorymovement_set.filter(from_location=loc).aggregate(s=Coalesce(Sum('quantity'), 0))['s'] or 0
                if (inv - out) < 50:
                    InventoryMovement.objects.create(
                        product=p, quantity=100, movement_type='inbound',
                        to_location=loc, from_location=None, moved_by=owner,
                        outlet=main_outlet or getattr(loc, 'outlet', None),
                    )

        # --- Customers for sales ---
        customers = list(Customer.objects.all())
        if not customers and not dry:
            for i in range(50):
                phone = '09%02d%06d' % (random.randint(1, 99), random.randint(0, 999999))
                if Customer.objects.filter(phone_number=phone).exists():
                    continue
                Customer.objects.create(
                    name='Customer %s' % (Customer.objects.count() + 1),
                    phone_number=phone,
                    preferred_branch=loc,
                )
            customers = list(Customer.objects.all())

        # --- Phase 3: 1000+ sales over 30 days ---
        now = timezone.now()
        start_30 = now - timedelta(days=30)
        total_created = 0
        if not dry:
            for _ in range(n_sales):
                when = start_30 + timedelta(
                    seconds=random.randint(0, int((now - start_30).total_seconds()))
                )
                with transaction.atomic():
                    sale = SaleTransaction.objects.create(
                        staff=owner,
                        sale_location=loc,
                        customer=random.choice(customers) if customers else None,
                        total_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        status='approved',
                        approved_by=owner,
                        approved_at=when,
                    )
                    n_items = random.randint(1, min(4, len(products)))
                    chosen = random.sample(products, n_items)
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
                            outlet=main_outlet or getattr(loc, 'outlet', None),
                        )
                    sale.total_amount = tot
                    sale.save(update_fields=['total_amount'])
                    SaleTransaction.objects.filter(pk=sale.pk).update(created_at=when)
                    total_created += 1
        self.stdout.write(self.style.SUCCESS('  Sales (30 days): %s' % (n_sales if dry else total_created)))
        self.stdout.write(self.style.SUCCESS('Done. Open Reports (Sales Summary, Sale by Item) and capture report_load_1month.png'))
