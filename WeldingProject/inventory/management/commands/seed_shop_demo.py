"""
ဆိုင်အမျိုးအစားအလိုက် စမ်းသပ်ရန် Demo Data ထည့်ခြင်း။
တစ်ဆိုင်ချင်းစီ ကိုယ်တိုင်စမ်းကြည့်နိုင်ရန် categories, products, units, outlets, stock ထည့်ပေးသည်။

Usage:
  # ဆေးဆိုင် dataပ်သပ်ထည့်မယ် (DB flush ပါ)
  python manage.py seed_shop_demo --shop pharmacy

  # အကုန်တစ်ခါထည့်မယ် (ဆေးဆိုင်၊ ဆေးခန်းတွဲ၊ ဖုန်း၊ ကွန်ပျူတာ၊ ဆိုလာ၊ သံပစ္စည်း၊ အထွေထွေ)
  python manage.py seed_shop_demo --shop all

  # DB ရှင်းပြီးမှ ဆေးဆိုင် data သပ်ထည့်မယ်
  python manage.py seed_shop_demo --shop pharmacy --flush

  # Login: admin@example.com / admin123 (သို့) ဖုန်း 09xxxxxxxx သတ်မှတ်ထားရင် ဖုန်းနဲ့ဝင်ပါ
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet, ShopSettings
from core.unit_templates import seed_units_for_business_category
from inventory.models import (
    Unit, Product, Category, Location, InventoryMovement,
    Purchase, PurchaseLine,
)

User = get_user_model()

SHOP_CHOICES = ['pharmacy', 'pharmacy_clinic', 'mobile', 'computer', 'solar', 'hardware', 'general', 'all']


def ensure_user(stdout, style):
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
    )
    if created or not user.check_password('admin123'):
        user.set_password('admin123')
        user.save()
    if not user.phone_number:
        user.phone_number = '09123456789'
        user.save(update_fields=['phone_number'])
    stdout.write(style.SUCCESS("  User: admin / admin123 (သို့) 09123456789"))
    return user


def ensure_roles(stdout, style):
    from core.models import Role
    for name, desc in [
        ('Owner', 'Full access'),
        ('Manager', 'Manage sales & staff'),
        ('Cashier', 'POS only'),
        ('Inventory', 'Inventory management'),
    ]:
        Role.objects.get_or_create(name=name, defaults={'description': desc})
    owner = Role.objects.get(name='Owner')
    stdout.write(style.SUCCESS("  Roles: Owner, Manager, Cashier, Inventory"))
    return owner


def ensure_outlets(stdout, style):
    main = Outlet.objects.filter(code='MAIN').first()
    if not main:
        main = Outlet.objects.create(name="ဆိုင်ချုပ် (Main)", code="MAIN", is_main_branch=True)
    branch_a = Outlet.objects.filter(code='BRANCH_A').first()
    if not branch_a:
        branch_a = Outlet.objects.create(name="ဆိုင်ခွဲ အေ", code="BRANCH_A", is_main_branch=False)
    main_wh = main.get_warehouse_location()
    main_sf = main.get_shopfloor_location()
    branch_a_sf = branch_a.get_shopfloor_location()
    if not main_wh or not main_sf:
        raise RuntimeError("Outlet locations not created.")
    stdout.write(style.SUCCESS("  Outlets: ဆိုင်ချုပ်, ဆိုင်ခွဲ အေ"))
    return main, main_wh, main_sf, branch_a, branch_a_sf


def ensure_shop_settings(business_category, stdout, style):
    settings_obj = ShopSettings.get_settings()
    settings_obj.business_category = business_category
    settings_obj.currency = 'MMK'
    settings_obj.shop_name = settings_obj.shop_name or 'HoBo POS Demo'
    settings_obj.setup_wizard_done = True
    settings_obj.save()
    seed_units_for_business_category(business_category)
    stdout.write(style.SUCCESS(f"  Shop: business_category={business_category}, units seeded"))


# ---------- Pharmacy (ဆေးဆိုင်) ----------
PHARMACY_DATA = {
    'categories': [
        ('ပဋိဇီဝဆေး', 'Antibiotics'),
        ('အကိုက်အခဲပျောက်ဆေး', 'Pain Relief'),
        ('ဗီတာမင်နှင့်အားဆေး', 'Vitamins'),
    ],
    'products': [
        ('Amoxicillin 500mg', 'AMOX-500', 120, 80, 'PCS', 'TABLET', 'STRIP', 10),
        ('Paracetamol 500mg', 'PARA-500', 50, 30, 'PCS', 'TABLET', 'BOX', 100),
        ('Vitamin C 1000mg', 'VITC-1K', 200, 120, 'PCS', 'TABLET', 'BOTTLE', 30),
        ('Cetirizine 10mg', 'CETI-10', 80, 50, 'PCS', 'TABLET', 'STRIP', 10),
    ],
}


# ---------- Pharmacy + Clinic (ဆေးခန်းတွဲ) ----------
PHARMACY_CLINIC_DATA = {
    'categories': [
        ('ဆေးဆိုင်', 'Pharmacy'),
        ('ဆေးခန်းသုံးပစ္စည်း', 'Clinic Supplies'),
    ],
    'products': [
        ('Amoxicillin 500mg', 'AMOX', 120, 80, 'PCS', 'TABLET', 'STRIP', 10),
        ('Surgical Mask (50pcs)', 'MASK50', 3500, 2000, 'PCS', 'BOX', None, 1),
        ('Gloves M (100pcs)', 'GLV-M', 8500, 5000, 'PCS', 'BOX', None, 1),
        ('Betadine 500ml', 'BET500', 4500, 2800, 'PCS', 'BOTTLE', None, 1),
    ],
}


# ---------- Mobile / Smartphone (ဖုန်းဆိုင်) ----------
MOBILE_DATA = {
    'categories': [
        ('Smartphone', 'Smartphone'),
        ('Accessories', 'Accessories'),
    ],
    'products': [
        ('Samsung A54', 'MB-SAM-A54', 850000, 720000, 'PCS', None, None, 1),
        ('iPhone 15', 'MB-IP15', 2100000, 1850000, 'PCS', None, None, 1),
        ('Oppo A78', 'MB-OPP-A78', 450000, 380000, 'PCS', None, None, 1),
        ('Phone Case Universal', 'MB-CASE', 8500, 4000, 'PCS', None, None, 1),
        ('Screen Protector', 'MB-SCR', 3500, 1500, 'PCS', None, None, 1),
    ],
}


# ---------- Computer (ကွန်ပျူတာဆိုင်) ----------
COMPUTER_DATA = {
    'categories': [
        ('Laptop', 'Laptop'),
        ('Desktop & Parts', 'Desktop'),
        ('Accessories', 'Accessories'),
    ],
    'products': [
        ('Laptop Dell Inspiron 15', 'DELL-15', 1250000, 1050000, 'PCS', None, None, 1),
        ('Laptop HP Pavilion', 'HP-PAV', 980000, 820000, 'PCS', None, None, 1),
        ('Mouse Wireless', 'MOU-WL', 25000, 12000, 'PCS', None, None, 1),
        ('Keyboard USB', 'KBD', 35000, 18000, 'PCS', None, None, 1),
        ('USB Flash 32GB', 'USB32', 18000, 9000, 'PCS', None, None, 1),
    ],
}


# ---------- Solar (ဆိုလာ/ဘက်ထရီဆိုင်) ----------
SOLAR_DATA = {
    'categories': [
        ('Solar Panel', 'Solar Panel'),
        ('Inverter & Battery', 'Inverter & Battery'),
        ('Cable & Accessories', 'Cable'),
    ],
    'products': [
        ('Solar Panel 330W', 'SL-PANEL-330', 185000, 150000, 'PCS', None, None, 1),
        ('Solar Panel 450W', 'SL-PANEL-450', 245000, 200000, 'PCS', None, None, 1),
        ('Inverter 2.4kW', 'SL-INV-24', 450000, 380000, 'PCS', None, None, 1),
        ('Battery 100AH', 'SL-BAT-100', 320000, 265000, 'PCS', None, None, 1),
        ('DC Cable 4mm (per feet)', 'SL-CAB-4', 450, 280, 'PCS', 'FEET', 'ROLL', 90),
    ],
}


# ---------- Hardware (အိမ်ဆောက်ပစ္စည်းဆိုင်) ----------
HARDWARE_DATA = {
    'categories': [
        ('ကြိုးနှင့်ဝိုင်ယာ', 'Wire & Cable'),
        ('သံနှင့်ပစ္စည်း', 'Iron & Nails'),
        ('ပလပ်စတစ်ပစ္စည်း', 'Plumbing'),
    ],
    'products': [
        ('Electric Wire 1.5mm (ပေ)', 'HW-WIRE15', 350, 220, 'PCS', 'FEET', 'ROLL', 90),
        ('Electric Wire 2.5mm (ပေ)', 'HW-WIRE25', 520, 350, 'PCS', 'FEET', 'ROLL', 90),
        ('Nail 2" (ဒါဇင်)', 'HW-NAIL-2', 1200, 800, 'PCS', 'DOZEN', 'BOX', 10),
        ('PVC Pipe 4" (ပေ)', 'HW-PVC-4', 1200, 750, 'PCS', 'FEET', None, 1),
        ('Cement Bag 50kg', 'HW-CEM50', 12500, 9800, 'PCS', 'KG', None, 1),
    ],
}


# ---------- General Retail (အထွေထွေလက်လီ) ----------
GENERAL_DATA = {
    'categories': [
        ('ယေဘုယျ', 'General'),
        ('အဖျော်ရည်နှင့်စားစရာ', 'Beverages & Snacks'),
    ],
    'products': [
        ('Mineral Water 1L', 'GR-WATER-1L', 500, 280, 'PCS', None, None, 1),
        ('Biscuit Pack', 'GR-BISCUIT', 1200, 700, 'PCS', None, None, 1),
        ('Soap Bar', 'GR-SOAP', 800, 450, 'PCS', None, None, 1),
        ('Shampoo Sachet', 'GR-SHAMP', 300, 180, 'PCS', None, None, 1),
        ('Notebook A4', 'GR-NOTE-A4', 1500, 900, 'PCS', None, None, 1),
    ],
}


def get_unit_by_code(code):
    return Unit.objects.filter(code=code).first()


def run_shop_data(shop_key, data, user, main, main_wh, main_sf, branch_a_sf, stdout, style):
    """Create categories and products for one shop type; add stock via purchase/inbound."""
    prefix = {
        'pharmacy': 'PH',
        'pharmacy_clinic': 'PCL',
        'mobile': 'MB',
        'computer': 'CP',
        'solar': 'SL',
        'hardware': 'HW',
        'general': 'GR',
    }.get(shop_key, 'XX')
    cat_map = {}
    for name_my, name_en in data['categories']:
        cname = f"{name_my} ({name_en})"
        cat, _ = Category.objects.get_or_create(name=cname, defaults={'order': 0})
        cat_map[cname] = cat
    # Default category if no match
    first_cat = list(cat_map.values())[0] if cat_map else None
    created_products = []
    for i, row in enumerate(data['products']):
        name, sku, retail, cost, unit_type, base_code, purchase_code, factor = row
        sku_unique = f"{prefix}-{sku}" if len(row) >= 2 else f"{prefix}-{i+1:03d}"
        cat = first_cat
        base_u = get_unit_by_code(base_code) if base_code else None
        purchase_u = get_unit_by_code(purchase_code) if purchase_code else None
        product, created = Product.objects.get_or_create(
            sku=sku_unique,
            defaults={
                'name': name,
                'category': cat,
                'retail_price': Decimal(str(retail)),
                'cost_price': Decimal(str(cost)),
                'unit_type': unit_type or 'PCS',
                'base_unit': base_u,
                'purchase_unit': purchase_u,
                'purchase_unit_factor': Decimal(str(factor)) if factor else Decimal('1'),
            },
        )
        if not product.base_unit_id and base_u:
            product.base_unit = base_u
            product.purchase_unit = purchase_u
            product.purchase_unit_factor = Decimal(str(factor)) if factor else Decimal('1')
            product.save(update_fields=['base_unit', 'purchase_unit', 'purchase_unit_factor'])
        created_products.append((product, base_u, purchase_u, factor))
    # Add stock: 1 purchase + inbound for first product; optional transfer
    if created_products:
        prod, base_u, purchase_u, factor = created_products[0]
        qty_in = 50 if not purchase_u else (5 if purchase_u and ('ROLL' in purchase_u.code or 'BOX' in purchase_u.code) else 20)
        base_qty = int(qty_in)
        if purchase_u and prod.purchase_unit_id:
            try:
                base_qty = prod.get_purchase_to_base_quantity(purchase_u, int(qty_in))
            except Exception:
                pass
            purchase = Purchase.objects.create(outlet=main, reference=f"DEMO-{prefix}-001", created_by=user)
            PurchaseLine.objects.create(
                purchase=purchase, product=prod, purchase_unit=purchase_u,
                quantity=int(qty_in), unit_cost=prod.cost_price or 0, to_location=main_wh
            )
            InventoryMovement.objects.create(
                product=prod, from_location=None, to_location=main_wh, quantity=base_qty,
                movement_type='inbound', moved_by=user, outlet=main, notes=f"Demo {shop_key} purchase"
            )
        else:
            InventoryMovement.objects.create(
                product=prod, from_location=None, to_location=main_wh, quantity=base_qty,
                movement_type='inbound', moved_by=user, outlet=main, notes=f"Demo {shop_key} stock"
            )
        if branch_a_sf and main_wh:
            transfer_qty = min(base_qty, 10)
            InventoryMovement.objects.create(
                product=prod, from_location=main_wh, to_location=branch_a_sf, quantity=transfer_qty,
                movement_type='transfer', moved_by=user, outlet=main, notes=f"Demo {shop_key} transfer"
            )
    stdout.write(style.SUCCESS(f"  {shop_key}: categories={len(data['categories'])}, products={len(data['products'])}, stock added"))


class Command(BaseCommand):
    help = "ဆိုင်အမျိုးအစားအလိုက် demo data ထည့်ခြင်း (တစ်ဆိုင်ချင်းစီ စမ်းသပ်ရန်)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop',
            type=str,
            default='all',
            choices=SHOP_CHOICES,
            help='pharmacy|pharmacy_clinic|mobile|computer|solar|hardware|general|all',
        )
        parser.add_argument('--flush', action='store_true', help='DB flush + migrate before seed')

    def handle(self, *args, **options):
        style = self.style
        shop = options['shop']
        do_flush = options.get('flush', False)

        self.stdout.write(style.SUCCESS(f"\n=== Seed Shop Demo: {shop} ===\n"))

        if do_flush:
            self.stdout.write("Flushing DB...")
            call_command('flush', '--noinput')
            call_command('migrate', '--noinput')

        with transaction.atomic():
            user = ensure_user(self.stdout, style)
            owner = ensure_roles(self.stdout, style)
            if not user.role_obj_id:
                user.role_obj = owner
                user.save(update_fields=['role_obj'])
            main, main_wh, main_sf, branch_a, branch_a_sf = ensure_outlets(self.stdout, style)

            if shop == 'all':
                ensure_shop_settings('general', self.stdout, style)
                for key, data in [
                    ('pharmacy', PHARMACY_DATA),
                    ('pharmacy_clinic', PHARMACY_CLINIC_DATA),
                    ('mobile', MOBILE_DATA),
                    ('computer', COMPUTER_DATA),
                    ('solar', SOLAR_DATA),
                    ('hardware', HARDWARE_DATA),
                    ('general', GENERAL_DATA),
                ]:
                    seed_units_for_business_category(key if key != 'pharmacy_clinic' else 'pharmacy')
                    run_shop_data(key, data, user, main, main_wh, main_sf, branch_a_sf, self.stdout, style)
            else:
                ensure_shop_settings(shop, self.stdout, style)
                data_map = {
                    'pharmacy': PHARMACY_DATA,
                    'pharmacy_clinic': PHARMACY_CLINIC_DATA,
                    'mobile': MOBILE_DATA,
                    'computer': COMPUTER_DATA,
                    'solar': SOLAR_DATA,
                    'hardware': HARDWARE_DATA,
                    'general': GENERAL_DATA,
                }
                data = data_map.get(shop)
                if data:
                    run_shop_data(shop, data, user, main, main_wh, main_sf, branch_a_sf, self.stdout, style)

        self.stdout.write(style.SUCCESS("\n  Done. Login: admin@example.com / admin123 (သို့) 09123456789\n"))
