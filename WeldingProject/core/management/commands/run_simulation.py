"""
CLI simulation: Register -> Login -> Sales (then approve). ~1 month style.
Run: python manage.py run_simulation
Uses Django test client (no browser, no live server). Each step is explained.
No Redis required: channel layer is forced to InMemory for this command.
"""
import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from rest_framework.test import APIClient


class Command(BaseCommand):
    help = 'CLI simulation: Register -> Login -> Sales -> Approve (~1 month style). Explains each step.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Spread sales over N days (default 30)')
        parser.add_argument('--sales-per-day', type=int, default=3, help='Sales to create per day')
        parser.add_argument('--skip-register', action='store_true', help='Use existing user (e.g. after seed_demo_users)')

    def _safe_str(self, s):
        """Avoid UnicodeEncodeError on CMD (cp1252) by using ASCII where possible."""
        try:
            return str(s).encode('ascii', 'replace').decode('ascii')
        except Exception:
            return str(s)[:50]

    def log(self, msg, style='HTTP_INFO'):
        out = str(msg)
        try:
            out.encode('ascii')
        except UnicodeEncodeError:
            out = out.encode('ascii', 'replace').decode('ascii')
        self.stdout.write(getattr(self.style, style, self.style.HTTP_INFO)(out))

    def handle(self, *args, **options):
        days = options['days']
        sales_per_day = options['sales_per_day']
        skip_register = options['skip_register']

        self.log('========================================', 'MIGRATE_HEADING')
        self.log('HoBo POS - CLI Simulation (no browser)', 'MIGRATE_HEADING')
        self.log('========================================', 'MIGRATE_HEADING')
        # No Redis: use in-memory channel layer so signals (notifications) do not require Redis
        settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
        # Allow Django test client's default host (when running in Docker or strict ALLOWED_HOSTS)
        hosts = list(settings.ALLOWED_HOSTS) if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) else [settings.ALLOWED_HOSTS]
        if 'testserver' not in hosts:
            settings.ALLOWED_HOSTS = hosts + ['testserver']

        from django.contrib.auth import get_user_model
        from core.models import Role
        from inventory.models import Location, Product, Category, SaleTransaction, InventoryMovement

        User = get_user_model()
        client = APIClient()

        # --- Step 0: Ensure minimal data (Location, Product, Stock) ---
        self.log('\n[Step 0] Ensure Location, Category, Product, Stock...', 'WARNING')
        loc = Location.objects.filter(is_sale_location=True).first()
        if not loc:
            loc = Location.objects.create(
                name='Sim Branch',
                location_type='branch',
                is_sale_location=True,
            )
            self.log('  Created Location: %s (id=%s)' % (self._safe_str(loc.name), loc.id))
        else:
            self.log('  Location: %s (id=%s)' % (self._safe_str(loc.name), loc.id))

        cat = Category.objects.first()
        if not cat:
            cat = Category.objects.create(name='Sim Category')
            self.log('  Created Category: %s' % self._safe_str(cat.name))
        prod = Product.objects.filter(category=cat).first() or Product.objects.first()
        if not prod:
            prod = Product.objects.create(
                name='SimProduct',
                sku='SIM-001',
                category=cat,
                retail_price=10000,
                cost_price=5000,
            )
            self.log('  Created Product: %s (id=%s)' % (self._safe_str(prod.name), prod.id))
        else:
            self.log('  Product: %s (id=%s)' % (self._safe_str(prod.name), prod.id))

        # Ensure stock at location (inbound) so approval won't fail
        from django.db.models import Sum, DecimalField, Value
        from django.db.models.functions import Coalesce
        from django.db.models import Q
        dec_zero = Value(0, output_field=DecimalField(max_digits=18, decimal_places=4))
        to_sum = prod.inventorymovement_set.filter(to_location=loc).aggregate(
            s=Coalesce(Sum('quantity'), dec_zero))['s'] or 0
        from_sum = prod.inventorymovement_set.filter(from_location=loc).aggregate(
            s=Coalesce(Sum('quantity'), dec_zero))['s'] or 0
        stock = to_sum - from_sum
        need = max(0, (sales_per_day * days * 2) - (stock or 0))
        if need > 0:
            owner = User.objects.filter(role_obj__name__icontains='owner').first() or User.objects.first()
            InventoryMovement.objects.create(
                product=prod,
                quantity=need,
                movement_type='inbound',
                to_location=loc,
                from_location=None,
                moved_by=owner,
            )
            self.log('  Added %s units stock at %s' % (need, self._safe_str(loc.name)))

        # --- Step 1: Register or use existing user ---
        sim_email, password = 'sim@test.local', 'sim123456'
        # Register API uses email/phone to build username (no 'username' field); login uses that same value
        username = sim_email
        if not skip_register and not User.objects.filter(email__iexact=sim_email).exists():
            self.log('\n[Step 1] Register (POST /api/core/register/)', 'WARNING')
            self.log('  Purpose: First user becomes owner, can login immediately.', 'HTTP_INFO')
            r = client.post('/api/core/register/', {
                'email': sim_email,
                'password': password,
                'password_confirm': password,
                'shop_name': 'Sim Shop',
            }, format='json')
            if r.status_code not in (200, 201):
                self.log('  FAIL: %s %s' % (r.status_code, self._safe_str(r.json())), 'ERROR')
                return
            self.log('  OK: registered', 'SUCCESS')
            # API creates user with username = email (or phone); fetch by email
            user = User.objects.get(email__iexact=sim_email)
            username = user.username
            user.assigned_locations.add(loc)
            if not user.primary_location_id:
                user.primary_location = loc
                user.save(update_fields=['primary_location'])
            self.log('  Assigned location to user.', 'HTTP_INFO')
        else:
            if skip_register:
                user = User.objects.filter(role_obj__name__icontains='owner').first() or User.objects.first()
                if not user:
                    self.log('  No user. Run seed_demo_users or omit --skip-register.', 'ERROR')
                    return
                username, password = user.username, 'demo123'
                self.log('\n[Step 1] Using existing user: %s' % username, 'WARNING')
            else:
                user = User.objects.get(username=username)
                self.log('\n[Step 1] User exists: %s' % username, 'WARNING')
            if loc not in user.assigned_locations.all():
                user.assigned_locations.add(loc)
            if not user.primary_location_id:
                user.primary_location = loc
                user.save(update_fields=['primary_location'])

        # --- Step 2: Login (JWT) ---
        self.log('\n[Step 2] Login (POST /api/token/)', 'WARNING')
        self.log('  Purpose: Get JWT for API calls.', 'HTTP_INFO')
        r = client.post('/api/token/', {'username': username, 'password': password}, format='json')
        if r.status_code != 200:
            self.log('  FAIL: %s %s' % (r.status_code, self._safe_str(r.json() if r.content else r.content)), 'ERROR')
            return
        token = r.json().get('access')
        if not token:
            self.log('  FAIL: No access token in response.', 'ERROR')
            return
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        self.log('  OK: JWT obtained.', 'SUCCESS')

        # --- Step 2b: Exchange rate (GET + PATCH) - owner/staff can edit in testing ---
        self.log('\n[Step 2b] Exchange rate GET + PATCH (settings/exchange-rate/)', 'WARNING')
        self.log('  Purpose: User (owner/staff in DEBUG) can view and edit rate.', 'HTTP_INFO')
        r = client.get('/api/settings/exchange-rate/')
        if r.status_code != 200:
            self.log('  GET FAIL: %s %s' % (r.status_code, self._safe_str(r.json() if r.content else '')), 'ERROR')
        else:
            self.log('  GET OK: rate=%s' % self._safe_str(r.json().get('usd_exchange_rate')), 'SUCCESS')
        r = client.patch('/api/settings/exchange-rate/', {'usd_exchange_rate': 2100}, format='json')
        if r.status_code != 200:
            self.log('  PATCH FAIL: %s %s' % (r.status_code, self._safe_str(r.json() if r.content else '')), 'ERROR')
        else:
            self.log('  PATCH OK: exchange rate updated (testing editable).', 'SUCCESS')

        # --- Step 3: Create sales (POST /api/sales/request/) ---
        total_sales = days * sales_per_day
        self.log('\n[Step 3] Create %s sales (POST /api/sales/request/)' % total_sales, 'WARNING')
        self.log('  Purpose: Staff submits sale requests (pending).', 'HTTP_INFO')
        created_ids = []
        price = float(prod.retail_price)
        for i in range(total_sales):
            payload = {
                'customer': None,
                'sale_items': [{'product': prod.id, 'quantity': 1, 'unit_price': price}],
                'sale_location': loc.id,
                'discount_amount': 0,
            }
            r = client.post('/api/sales/request/', payload, format='json')
            if r.status_code in (200, 201):
                created_ids.append(r.json().get('id'))
            else:
                self.log('  Sale %s FAIL: %s %s' % (i + 1, r.status_code, self._safe_str(r.json())), 'ERROR')
        self.log('  OK: %s sales created (pending).' % len(created_ids), 'SUCCESS')

        # --- Step 4: Approve sales (PATCH /api/admin/approve/<id>/) ---
        self.log('\n[Step 4] Approve sales (PATCH /api/admin/approve/<id>/)', 'WARNING')
        self.log('  Purpose: Admin approves; stock deducted.', 'HTTP_INFO')
        approved = 0
        for pk in created_ids:
            if not pk:
                continue
            r = client.patch('/api/admin/approve/%s/' % pk, {'status': 'approved'}, format='json')
            if r.status_code == 200:
                approved += 1
            else:
                self.log('  Approve %s FAIL: %s %s' % (pk, r.status_code, self._safe_str(r.json())), 'ERROR')
        self.log('  OK: %s sales approved.' % approved, 'SUCCESS')

        # --- Step 5: Optionally spread created_at over N days (for report testing) ---
        if approved and days > 1:
            self.log('\n[Step 5] Spread sale dates over %s days' % days, 'WARNING')
            self.log('  Purpose: Reports show data across period.', 'HTTP_INFO')
            base = timezone.now() - timedelta(days=days)
            for i, pk in enumerate(created_ids):
                if not pk:
                    continue
                try:
                    t = SaleTransaction.objects.get(pk=pk)
                    t.created_at = base + timedelta(days=i % days, seconds=random.randint(0, 86400))
                    t.save(update_fields=['created_at'])
                except SaleTransaction.DoesNotExist:
                    pass
            self.log('  OK: created_at updated for report-style period.', 'SUCCESS')

        self.log('\n========================================', 'MIGRATE_HEADING')
        self.log('Done. Register -> Login -> Sales -> Approve OK.', 'SUCCESS')
        self.log('Server: same APIs work when server runs (run_lite.bat).', 'HTTP_INFO')
