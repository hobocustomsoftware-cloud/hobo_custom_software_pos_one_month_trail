"""
Generate 60 days of realistic shop simulation data:
- Day 1-20: Free Trial mode (normal sales)
- Day 21: License Activated
- Day 25-40: Fluctuating USD→MMK exchange rates (manual + auto-synced)
- At least 5,000 transactions (including bundled items and offline-synced records)
Run: python manage.py run_simulation_data
"""
import random
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


def _safe_str(s):
    try:
        return str(s).encode('ascii', 'replace').decode('ascii')
    except Exception:
        return str(s)[:50]


class Command(BaseCommand):
    help = (
        'Generate 60 days of shop data: trial (day 1-20), license activated (day 21), '
        'exchange rates (day 25-40), 5000+ transactions with bundles and offline-synced.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of simulation data (default 30)',
        )
        parser.add_argument(
            '--min-transactions',
            type=int,
            default=5000,
            help='Minimum number of transactions to create (default 5000)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print plan only, do not create data',
        )
        parser.add_argument(
            '--no-flush',
            action='store_true',
            help='Do not flush the database before generating data (default: flush first)',
        )

    def log(self, msg, style='HTTP_INFO'):
        out = _safe_str(msg)
        style_fn = getattr(self.style, style, self.style.HTTP_INFO)
        self.stdout.write(style_fn(out))

    def handle(self, *args, **options):
        num_days = max(1, min(365, options.get('days', 30)))
        min_tx = max(5000, options['min_transactions'])
        dry_run = options['dry_run']
        no_flush = options['no_flush']

        from django.contrib.auth import get_user_model
        from core.models import Role
        from inventory.models import (
            Category, Product, Location, InventoryMovement,
            SaleTransaction, SaleItem, PaymentMethod,
            GlobalSetting, ExchangeRateLog,
            Bundle, BundleItem,
        )
        from customer.models import Customer
        from license.models import AppInstallation, AppLicense, LicenseType

        User = get_user_model()

        self.log('========================================', 'MIGRATE_HEADING')
        self.log('run_simulation_data: %s days shop data' % num_days, 'MIGRATE_HEADING')
        self.log('========================================', 'MIGRATE_HEADING')

        if dry_run:
            self.log('\n[DRY RUN] No data will be written.', 'WARNING')
            self.log('  Days: %s, Min transactions: %s' % (num_days, min_tx), 'HTTP_INFO')
            return

        # Flush database so previous runs do not cause UNIQUE / Integrity errors
        if not no_flush:
            self.log('\n[0] Flushing database (clean slate)...', 'WARNING')
            call_command('flush', '--noinput')
            self.log('  Database flushed. Creating fresh data.', 'SUCCESS')

        # In-memory channel layer to avoid Redis
        from django.conf import settings
        settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

        base_date = timezone.now().date() - timedelta(days=num_days)
        self.log('\n[1] Base date (Day 1): %s' % base_date, 'WARNING')

        # --- Roles & Users ---
        self.log('\n[2] Roles & users...', 'WARNING')
        owner_role, _ = Role.objects.get_or_create(name='owner', defaults={'description': 'Owner'})
        staff_role, _ = Role.objects.get_or_create(name='sale_staff', defaults={'description': 'Sale Staff'})
        owner = User.objects.filter(role_obj=owner_role).first() or User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not owner:
            owner = User.objects.create_user(
                username='sim_owner',
                first_name='Sim',
                last_name='Owner',
                role_obj=owner_role,
                is_staff=True,
                is_active=True,
            )
            owner.set_password('demo123')
            owner.save()
            self.log('  Created user: sim_owner / demo123', 'SUCCESS')
        staff_users = list(User.objects.filter(role_obj=staff_role)[:3])
        if not staff_users:
            for i in range(2):
                u = User.objects.create_user(
                    username='sim_staff_%s' % (i + 1),
                    first_name='Staff',
                    last_name=str(i + 1),
                    role_obj=staff_role,
                    is_active=True,
                )
                u.set_password('demo123')
                u.save()
                staff_users.append(u)
            self.log('  Created 2 staff users', 'SUCCESS')
        staff_users.append(owner)
        self.log('  Owner + staff ready', 'SUCCESS')

        # --- Location ---
        loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            loc = Location.objects.create(
                name='Sim Branch',
                location_type='branch',
                is_sale_location=True,
            )
            self.log('  Created Location: Sim Branch', 'SUCCESS')
        for u in staff_users:
            if loc not in u.assigned_locations.all():
                u.assigned_locations.add(loc)
            if not u.primary_location_id:
                u.primary_location = loc
                u.save(update_fields=['primary_location'])

        # --- Categories & Products ---
        self.log('\n[3] Categories & products...', 'WARNING')
        categories = list(Category.objects.all())
        if len(categories) < 4:
            for name in ['Electronics', 'Tools', 'Spare Parts', 'Consumables']:
                if not Category.objects.filter(name=name).exists():
                    categories.append(Category.objects.create(name=name))
        products = list(Product.objects.all())
        if len(products) < 40:
            for i in range(40 - len(products)):
                cat = random.choice(categories)
                sku = 'SIM-P-%03d' % (len(products) + i + 1)
                if Product.objects.filter(sku=sku).exists():
                    continue
                p = Product.objects.create(
                    name='Sim Product %s' % (len(products) + i + 1),
                    sku=sku,
                    category=cat,
                    retail_price=Decimal(str(round(random.uniform(3000, 120000), 2))),
                    cost_price=Decimal(str(round(random.uniform(1000, 60000), 2))),
                )
                products.append(p)
        self.log('  Products: %s' % len(products), 'SUCCESS')

        # --- Payment methods ---
        for name in ['Cash', 'KPay', 'Wave Pay']:
            PaymentMethod.objects.get_or_create(name=name, defaults={'display_order': 1})
        payment_methods = list(PaymentMethod.objects.filter(is_active=True)[:5])
        self.log('  Payment methods: %s' % len(payment_methods), 'SUCCESS')

        # --- Bundles (for bundled-item sales) ---
        self.log('\n[4] Bundles...', 'WARNING')
        bundles = list(Bundle.objects.filter(is_active=True))
        if len(products) >= 5 and len(bundles) < 2:
            b1 = Bundle.objects.create(
                name='Sim Starter Bundle',
                bundle_type='Fixed',
                pricing_type='CUSTOM_SET',
                is_active=True,
            )
            for idx, p in enumerate(products[:3]):
                BundleItem.objects.get_or_create(
                    bundle=b1, product=p,
                    defaults={'quantity': 1, 'sort_order': idx},
                )
            bundles.append(b1)
            b2 = Bundle.objects.create(
                name='Sim Pro Bundle',
                bundle_type='Fixed',
                pricing_type='CUSTOM_SET',
                is_active=True,
            )
            for idx, p in enumerate(products[3:6]):
                BundleItem.objects.get_or_create(
                    bundle=b2, product=p,
                    defaults={'quantity': 1, 'sort_order': idx},
                )
            bundles.append(b2)
        bundle_products = []
        for b in bundles:
            bundle_products.extend([bi.product for bi in b.items.all()])
        bundle_products = list(set(bundle_products))
        self.log('  Bundles: %s (bundle products: %s)' % (len(bundles), len(bundle_products)), 'SUCCESS')

        # --- Stock (large inbound) ---
        self.log('\n[5] Stock (inbound)...', 'WARNING')
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import Q
        for p in products:
            in_sum = p.inventorymovement_set.filter(to_location=loc).aggregate(
                s=Coalesce(Sum('quantity'), 0))['s'] or 0
            out_sum = p.inventorymovement_set.filter(from_location=loc).aggregate(
                s=Coalesce(Sum('quantity'), 0))['s'] or 0
            if (in_sum - out_sum) < 500:
                InventoryMovement.objects.create(
                    product=p,
                    quantity=1000,
                    movement_type='inbound',
                    to_location=loc,
                    from_location=None,
                    moved_by=owner,
                )
        self.log('  Stock ensured for all products', 'SUCCESS')

        # --- Customers ---
        customers = list(Customer.objects.all())
        if len(customers) < 50:
            for i in range(50 - len(customers)):
                phone = '09%02d%07d' % (random.randint(10, 99), random.randint(0, 9999999))
                if Customer.objects.filter(phone_number=phone).exists():
                    continue
                Customer.objects.create(
                    name='Sim Customer %s' % (len(customers) + i + 1),
                    phone_number=phone,
                    preferred_branch=loc,
                )
            customers = list(Customer.objects.all())
        self.log('  Customers: %s' % len(customers), 'SUCCESS')

        # --- License: Trial (Day 1-20), Activated (Day 21) ---
        self.log('\n[6] License: Trial day 1-20, Activated day 21...', 'WARNING')
        machine_id = 'sim-machine-60d'
        first_run_naive = datetime.combine(base_date, time.min)
        first_run_dt = timezone.make_aware(first_run_naive) if timezone.is_naive(first_run_naive) else first_run_naive
        inst, created = AppInstallation.objects.get_or_create(
            machine_id=machine_id,
            defaults={'first_run_at': first_run_dt},
        )
        if not created:
            inst.first_run_at = first_run_dt
            inst.save(update_fields=['first_run_at'])
        license_activated_date = base_date + timedelta(days=20)  # Day 21
        activated_naive = datetime.combine(license_activated_date, time.min)
        activated_dt = timezone.make_aware(activated_naive) if timezone.is_naive(activated_naive) else activated_naive
        lic, _ = AppLicense.objects.get_or_create(
            license_key='SIM-LIC-60D',
            defaults={
                'license_type': LicenseType.ON_PREMISE_PERPETUAL,
                'machine_id': machine_id,
                'is_active': True,
                'activated_at': activated_dt,
            },
        )
        if lic.activated_at != activated_dt:
            lic.activated_at = activated_dt
            lic.save(update_fields=['activated_at'])
        self.log('  Trial until day 20; License activated at day 21', 'SUCCESS')

        # --- Exchange rates: Day 25-40 (or 25 to num_days if shorter) ---
        rate_start, rate_end = 25, min(41, num_days + 1)
        if rate_end > rate_start:
            self.log('\n[7] Exchange rates (Day %s-%s)...' % (rate_start, rate_end - 1), 'WARNING')
        gs, _ = GlobalSetting.objects.get_or_create(
            key='usd_exchange_rate',
            defaults={'is_auto_sync': True},
        )
        base_rate = Decimal('2100')
        for d in range(rate_start, rate_end):
            day_date = base_date + timedelta(days=d - 1)
            delta = random.uniform(-80, 100)
            rate = max(Decimal('1900'), min(Decimal('2300'), base_rate + Decimal(str(round(delta, 2)))))
            source = 'Scraped' if random.random() < 0.6 else 'Manual'
            ExchangeRateLog.objects.update_or_create(
                date=day_date,
                currency='USD',
                defaults={'rate': rate, 'source': source},
            )
            if d == rate_start:
                gs.value_decimal = rate
                gs.is_auto_sync = (source == 'Scraped')
                if source == 'Manual':
                    gs.manual_usd_rate = rate
                gs.save()
            self.log('  Day %s: USD=%s (%s)' % (d, rate, source), 'HTTP_INFO')
        if rate_end > rate_start:
            self.log('  Exchange rate log: %s days (%s-%s)' % (rate_end - rate_start, rate_start, rate_end - 1), 'SUCCESS')

        # --- Transactions: min_tx over num_days (bundled + offline-synced) ---
        self.log('\n[8] Transactions (min %s)...' % min_tx, 'WARNING')
        per_day = max(84, (min_tx // num_days) + 1)
        total_target = per_day * num_days
        total_created = 0
        bundled_count = 0
        offline_synced_count = 0
        invoice_counter_per_day = {}

        for day in range(1, num_days + 1):
            day_date = base_date + timedelta(days=day - 1)
            day_key = day_date.isoformat()
            invoice_counter_per_day[day_key] = invoice_counter_per_day.get(day_key, 0)
            n_sales = per_day + random.randint(-5, 15)
            n_sales = max(1, n_sales)
            date_part = day_date.strftime('%y%m%d')

            for _ in range(n_sales):
                inv_seq = invoice_counter_per_day[day_key] + 1
                invoice_counter_per_day[day_key] = inv_seq
                invoice_number = 'INV-%s-%04d' % (date_part, inv_seq)
                if SaleTransaction.objects.filter(invoice_number=invoice_number).exists():
                    invoice_number = 'INV-SIM-%s' % uuid.uuid4().hex[:10].upper()

                when_naive = datetime.combine(
                    day_date,
                    time(random.randint(8, 19), random.randint(0, 59), random.randint(0, 59)),
                )
                when = timezone.make_aware(when_naive) if timezone.is_naive(when_naive) else when_naive
                is_offline_synced = random.random() < 0.10 and day >= 5
                status = 'pending' if is_offline_synced else 'approved'
                staff = random.choice(staff_users)
                payment = random.choice(payment_methods) if payment_methods else None
                customer = random.choice(customers) if customers and random.random() < 0.4 else None

                with transaction.atomic():
                    sale = SaleTransaction(
                        invoice_number=invoice_number,
                        staff=staff,
                        sale_location=loc,
                        customer=customer,
                        total_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        status=status,
                        payment_method=payment,
                        payment_status='cash' if payment and payment.name == 'Cash' else 'paid',
                    )
                    sale.save()
                    SaleTransaction.objects.filter(pk=sale.pk).update(created_at=when)

                    # 1–4 line items; ~15% bundle-style (multiple products from one bundle)
                    use_bundle = bundle_products and random.random() < 0.15
                    if use_bundle and len(bundle_products) >= 2:
                        chosen_products = random.sample(bundle_products, min(2, len(bundle_products)))
                        bundled_count += 1
                    else:
                        chosen_products = random.sample(products, min(random.randint(1, 4), len(products)))
                    tot = Decimal('0')
                    for p in chosen_products:
                        qty = random.randint(1, 3)
                        up = p.retail_price or p.cost_price or Decimal('10000')
                        st = up * qty
                        SaleItem.objects.create(
                            sale_transaction=sale,
                            product=p,
                            quantity=qty,
                            unit_price=up,
                            subtotal=st,
                        )
                        tot += st
                        if status == 'approved':
                            InventoryMovement.objects.create(
                                product=p,
                                quantity=qty,
                                movement_type='outbound',
                                from_location=loc,
                                moved_by=staff,
                                sale_transaction=sale,
                            )
                    sale.total_amount = tot
                    sale.save(update_fields=['total_amount'])

                    if status == 'pending':
                        offline_synced_count += 1
                        approve_when = when + timedelta(minutes=random.randint(5, 120))
                        sale.status = 'approved'
                        sale.approved_by = owner
                        sale.approved_at = approve_when
                        sale.save(update_fields=['status', 'approved_by', 'approved_at'])
                        for item in sale.sale_items.all():
                            InventoryMovement.objects.create(
                                product=item.product,
                                quantity=item.quantity,
                                movement_type='outbound',
                                from_location=loc,
                                moved_by=owner,
                                sale_transaction=sale,
                            )

                total_created += 1
                if total_created % 500 == 0:
                    self.log('  Progress: %s transactions...' % total_created, 'HTTP_INFO')

            if day % 10 == 0:
                self.log('  Day %s/%s done (total %s)' % (day, num_days, total_created), 'SUCCESS')

        # --- E2E: Ensure 2 pending sales for Full Business Day test (morning approval step) ---
        pending_count = SaleTransaction.objects.filter(status='pending').count()
        if pending_count < 2:
            for i in range(2 - pending_count):
                inv_no = 'INV-E2E-%s-%s' % (timezone.now().date().strftime('%y%m%d'), total_created + i + 1)
                if SaleTransaction.objects.filter(invoice_number=inv_no).exists():
                    inv_no = 'INV-E2E-PEND-%s' % (timezone.now().timestamp())
                staff = random.choice(staff_users)
                payment = random.choice(payment_methods) if payment_methods else None
                customer = random.choice(customers) if customers and random.random() < 0.5 else None
                with transaction.atomic():
                    sale = SaleTransaction(
                        invoice_number=inv_no,
                        staff=staff,
                        sale_location=loc,
                        customer=customer,
                        total_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        status='pending',
                        payment_method=payment,
                        payment_status='pending',
                    )
                    sale.save()
                    chosen = random.sample(products, min(2, len(products)))
                    tot = Decimal('0')
                    for p in chosen:
                        qty = random.randint(1, 2)
                        up = p.retail_price or p.cost_price or Decimal('10000')
                        st = up * qty
                        SaleItem.objects.create(
                            sale_transaction=sale,
                            product=p,
                            quantity=qty,
                            unit_price=up,
                            subtotal=st,
                        )
                        tot += st
                    sale.total_amount = tot
                    sale.save(update_fields=['total_amount'])
                total_created += 1
            self.log('  E2E: 2 pending sales ensured for morning approval', 'SUCCESS')

        self.log('\n========================================', 'MIGRATE_HEADING')
        self.log('Done.', 'SUCCESS')
        self.log('  Transactions: %s' % total_created, 'SUCCESS')
        self.log('  With bundle-style items: %s' % bundled_count, 'SUCCESS')
        self.log('  Offline-synced (pending then approved): %s' % offline_synced_count, 'SUCCESS')
        self.log('  Exchange rate log: Day 25-40 (USD fluctuating)', 'SUCCESS')
        self.log('  License: Trial day 1-20, Activated day 21', 'SUCCESS')
