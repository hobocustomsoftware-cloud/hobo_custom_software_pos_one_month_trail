"""
Single-Tenancy Demo: run three scenarios (Grocery, Hardware, Pharmacy) one by one.
After each scenario, prints Login URL and credentials for manual UI check.
RAM: Run with one worker if needed; demo uses minimal in-DB data.
Usage: python manage.py run_single_tenancy_demo [--scenario 1|2|3] [--no-pause]
From host: scripts/run_single_tenancy_demo.bat  or  docker exec -it compose-backend-1 python manage.py run_single_tenancy_demo
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet
from inventory.models import (
    Unit, Product, Category, Location, InventoryMovement,
    SaleTransaction, SaleItem, Sale,
)

User = get_user_model()

LOGIN_URL = "http://localhost"
LOGIN_URL_8000 = "http://localhost:8000"
CREDS = "admin / admin123"


def ensure_superuser():
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        user.set_password('admin123')
        user.save()
    return user


def wipe_scenario_data():
    """Remove outlets (cascade to locations), movements, sales, products, categories. Keep User and Unit."""
    with transaction.atomic():
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        InventoryMovement.objects.all().delete()
        SaleTransaction.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Location.objects.all().delete()
        Outlet.objects.all().delete()


def seed_units_grocery():
    """Viss, Tical (1 Viss = 100 Tical)."""
    for code, name_my, name_en in [('VISS', 'ပိဿာ', 'Viss'), ('TICAL', 'ကျပ်သား', 'Tical')]:
        Unit.objects.update_or_create(code=code, defaults={'name_my': name_my, 'name_en': name_en, 'category': 'mass', 'order': 1 if code == 'VISS' else 2})
    viss = Unit.objects.get(code='VISS')
    tical = Unit.objects.get(code='TICAL')
    tical.base_unit = viss
    tical.factor_to_base = Decimal('0.01')
    tical.save(update_fields=['base_unit', 'factor_to_base'])


def seed_units_hardware():
    """Feet, Inch, Bag (အိတ်)."""
    units = [('FEET', 'ပေ', 'Feet', 'length'), ('INCH', 'လက်မ', 'Inch', 'length'), ('BAG', 'အိတ်', 'Bag', 'packaging')]
    for i, (code, name_my, name_en, cat) in enumerate(units, 1):
        Unit.objects.update_or_create(code=code, defaults={'name_my': name_my, 'name_en': name_en, 'category': cat, 'order': i})


def seed_units_pharmacy():
    """Strip (ကတ်), Tablet (လုံး), Bottle (ဗူး)."""
    units = [('STRIP', 'ကတ်', 'Strip', 'count'), ('TABLET', 'လုံး', 'Tablet', 'count'), ('BOTTLE', 'ဗူး', 'Bottle', 'volume')]
    for i, (code, name_my, name_en, cat) in enumerate(units, 1):
        Unit.objects.update_or_create(code=code, defaults={'name_my': name_my, 'name_en': name_en, 'category': cat, 'order': i})


def scenario_1_grocery(stdout, style):
    """Grocery/Chili: 1 Warehouse, 1 Retail. Add 100 Viss Dried Chili, Transfer 20 Viss, Sell 50 Tical."""
    stdout.write(style.SUCCESS("\n=== SCENARIO 1: Grocery/Chili (ငရုပ်သီးဆိုင်) ===\n"))
    user = ensure_superuser()
    seed_units_grocery()

    with transaction.atomic():
        outlet = Outlet.objects.create(name="ငရုပ်သီးဆိုင် (Grocery Shop)", is_main_branch=True, code="GROCERY")
        wh = outlet.get_warehouse_location()
        retail = outlet.get_shopfloor_location()
        if not wh or not retail:
            raise RuntimeError("Outlet locations not created")

        cat = Category.objects.create(name="Chili / ငရုတ်သီး", order=0)
        # Stock in tical (integer): 100 viss = 10000 tical, 20 viss = 2000 tical, sell 50 tical
        product = Product.objects.create(
            name="Dried Chili (ငရုပ်သီးခြောက်)",
            sku="CHILI-001",
            category=cat,
            retail_price=Decimal("500"),
            cost_price=Decimal("400"),
            unit_type="PCS",
        )
        # Add 100 Viss = 10000 tical to warehouse
        InventoryMovement.objects.create(
            product=product, quantity=10000, movement_type='inbound',
            to_location=wh, outlet=outlet, moved_by=user, notes="Initial 100 Viss"
        )
        # Transfer 20 Viss = 2000 tical to retail
        InventoryMovement.objects.create(
            product=product, quantity=2000, movement_type='transfer',
            from_location=wh, to_location=retail, outlet=outlet, moved_by=user, notes="Transfer 20 Viss"
        )
        # Sell 50 Tical from retail
        txn = SaleTransaction.objects.create(
            staff=user, sale_location=retail, outlet=outlet,
            total_amount=Decimal("25000"), status='approved', payment_status='paid'
        )
        SaleItem.objects.create(sale_transaction=txn, product=product, quantity=50, unit_price=Decimal("500"), subtotal=Decimal("25000"))
        InventoryMovement.objects.create(
            product=product, quantity=50, movement_type='outbound',
            from_location=retail, sale_transaction=txn, outlet=outlet, moved_by=user
        )

    wh_qty = product.get_stock_by_location(wh)
    retail_qty = product.get_stock_by_location(retail)
    stdout.write(style.SUCCESS(f"Warehouse remaining: {wh_qty} tical (= {wh_qty/100:.1f} Viss)"))
    stdout.write(style.SUCCESS(f"Retail remaining: {retail_qty} tical (= {retail_qty/100:.1f} Viss)"))


def scenario_2_hardware(stdout, style):
    """Hardware: 500 Bags Cement, sell 50; 1000 Feet Wire, sell 120."""
    stdout.write(style.SUCCESS("\n=== SCENARIO 2: Hardware (အိမ်ဆောက်ပစ္စည်းဆိုင်) ===\n"))
    wipe_scenario_data()
    user = ensure_superuser()
    seed_units_hardware()

    with transaction.atomic():
        outlet = Outlet.objects.create(name="Hardware Shop", is_main_branch=True, code="HARDWARE")
        wh = outlet.get_warehouse_location()
        retail = outlet.get_shopfloor_location()

        cat = Category.objects.create(name="Building Materials", order=0)
        cement = Product.objects.create(name="Cement (သံမဏိ)", sku="CEM-001", category=cat, retail_price=Decimal("8500"), cost_price=Decimal("7500"), unit_type="PKG")
        wire = Product.objects.create(name="Electric Wire (ကြိုး)", sku="WIRE-001", category=cat, retail_price=Decimal("150"), cost_price=Decimal("120"), unit_type="PCS")

        InventoryMovement.objects.create(product=cement, quantity=500, movement_type='inbound', to_location=wh, outlet=outlet, moved_by=user, notes="500 Bags")
        InventoryMovement.objects.create(product=wire, quantity=1000, movement_type='inbound', to_location=wh, outlet=outlet, moved_by=user, notes="1000 Feet")
        # Transfer to retail for sale
        InventoryMovement.objects.create(product=cement, quantity=500, movement_type='transfer', from_location=wh, to_location=retail, outlet=outlet, moved_by=user)
        InventoryMovement.objects.create(product=wire, quantity=1000, movement_type='transfer', from_location=wh, to_location=retail, outlet=outlet, moved_by=user)

        txn = SaleTransaction.objects.create(staff=user, sale_location=retail, outlet=outlet, total_amount=Decimal("443000"), status='approved', payment_status='paid')
        SaleItem.objects.create(sale_transaction=txn, product=cement, quantity=50, unit_price=Decimal("8500"), subtotal=Decimal("425000"))
        SaleItem.objects.create(sale_transaction=txn, product=wire, quantity=120, unit_price=Decimal("150"), subtotal=Decimal("18000"))
        InventoryMovement.objects.create(product=cement, quantity=50, movement_type='outbound', from_location=retail, sale_transaction=txn, outlet=outlet, moved_by=user)
        InventoryMovement.objects.create(product=wire, quantity=120, movement_type='outbound', from_location=retail, sale_transaction=txn, outlet=outlet, moved_by=user)

    stdout.write(style.SUCCESS(f"Cement balance: {cement.get_stock_by_location(retail)} Bags"))
    stdout.write(style.SUCCESS(f"Wire balance: {wire.get_stock_by_location(retail)} Feet"))
    stdout.write(style.SUCCESS("Sales: 50 Bags Cement + 120 Feet Wire = 443,000 MMK"))


def scenario_3_pharmacy(stdout, style):
    """Pharmacy: 100 Strips Paracetamol (1 strip=10 tablets). Sell 5 Tablets."""
    stdout.write(style.SUCCESS("\n=== SCENARIO 3: Pharmacy (ဆေးဆိုင်/ဆေးခန်း) ===\n"))
    wipe_scenario_data()
    user = ensure_superuser()
    seed_units_pharmacy()

    with transaction.atomic():
        outlet = Outlet.objects.create(name="Pharmacy", is_main_branch=True, code="PHARMA")
        wh = outlet.get_warehouse_location()
        retail = outlet.get_shopfloor_location()

        cat = Category.objects.create(name="Medicine", order=0)
        # Store in tablets (integer): 100 strips = 1000 tablets
        para = Product.objects.create(name="Paracetamol (ပါရာစီတမော)", sku="PARA-001", category=cat, retail_price=Decimal("50"), cost_price=Decimal("30"), unit_type="PCS")
        InventoryMovement.objects.create(product=para, quantity=1000, movement_type='inbound', to_location=wh, outlet=outlet, moved_by=user, notes="100 Strips (1000 tablets)")
        InventoryMovement.objects.create(product=para, quantity=1000, movement_type='transfer', from_location=wh, to_location=retail, outlet=outlet, moved_by=user)
        txn = SaleTransaction.objects.create(staff=user, sale_location=retail, outlet=outlet, total_amount=Decimal("250"), status='approved', payment_status='paid')
        SaleItem.objects.create(sale_transaction=txn, product=para, quantity=5, unit_price=Decimal("50"), subtotal=Decimal("250"))
        InventoryMovement.objects.create(product=para, quantity=5, movement_type='outbound', from_location=retail, sale_transaction=txn, outlet=outlet, moved_by=user)

    remaining = para.get_stock_by_location(retail)
    stdout.write(style.SUCCESS(f"Remaining: {remaining} tablets = {remaining/10:.1f} strips (99 strips + 5 tablets)"))


def print_credentials(stdout, style, scenario_num):
    stdout.write(style.SUCCESS("\n--- Login & URL ---"))
    stdout.write(style.WARNING(f"  URL: {LOGIN_URL}  or  {LOGIN_URL_8000}"))
    stdout.write(style.WARNING(f"  Login: {CREDS}"))
    stdout.write(style.SUCCESS("---\n"))


class Command(BaseCommand):
    help = "Run Single-Tenancy Demo: Scenario 1 (Grocery), 2 (Hardware), 3 (Pharmacy). Pause after each for UI check."

    def add_arguments(self, parser):
        parser.add_argument('--scenario', type=int, choices=[1, 2, 3], help='Run only this scenario')
        parser.add_argument('--no-pause', action='store_true', help='Do not pause between scenarios')

    def handle(self, *args, **options):
        style = self.style
        only = options.get('scenario')
        no_pause = options.get('no_pause', False)

        if only is None or only == 1:
            scenario_1_grocery(self.stdout, style)
            print_credentials(self.stdout, style, 1)
            if not no_pause and (only is None):
                input("Press Enter to continue to Scenario 2 (Hardware)...")

        if only is None or only == 2:
            scenario_2_hardware(self.stdout, style)
            print_credentials(self.stdout, style, 2)
            if not no_pause and (only is None):
                input("Press Enter to continue to Scenario 3 (Pharmacy)...")

        if only is None or only == 3:
            scenario_3_pharmacy(self.stdout, style)
            print_credentials(self.stdout, style, 3)

        self.stdout.write(style.SUCCESS("\nDemo complete."))
