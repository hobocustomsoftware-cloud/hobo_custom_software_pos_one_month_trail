"""
E2E Shop Setup: Reset DB, migrate, seed units + outlets for a shop type, then run Purchase + Transfer.
Used by E2E automation to prepare data before taking screenshots.
Usage: python manage.py e2e_shop_setup --shop pharmacy|mobile|electrical|solar
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet
from inventory.models import (
    Unit, Product, Category, Location, InventoryMovement,
    Purchase, PurchaseLine,
)

User = get_user_model()


def ensure_user(stdout, style):
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
    )
    if created or not user.check_password('admin123'):
        user.set_password('admin123')
        user.save()
    stdout.write(style.SUCCESS("  User: admin / admin123"))
    return user


def ensure_outlets(stdout, style):
    main = Outlet.objects.filter(code='MAIN').first()
    if not main:
        main = Outlet.objects.create(name="Main Warehouse", code="MAIN", is_main_branch=True)
    branch_a = Outlet.objects.filter(code='BRANCH_A').first()
    if not branch_a:
        branch_a = Outlet.objects.create(name="Branch A", code="BRANCH_A", is_main_branch=False)
    main_wh = main.get_warehouse_location()
    branch_a_sf = branch_a.get_shopfloor_location()
    if not main_wh or not branch_a_sf:
        raise RuntimeError("Outlet locations not created.")
    stdout.write(style.SUCCESS("  Outlets: Main, Branch A"))
    return main, main_wh, branch_a_sf, branch_a


def run_pharmacy(stdout, style, user):
    Unit.objects.update_or_create(code='STRIP', defaults={'name_my': 'ကတ်', 'name_en': 'Strip', 'category': 'count', 'order': 1})
    Unit.objects.update_or_create(code='BOX', defaults={'name_my': 'ဗူး/ဘူး', 'name_en': 'Box', 'category': 'packaging', 'order': 2})
    strip_u = Unit.objects.get(code='STRIP')
    box_u = Unit.objects.get(code='BOX')
    main, main_wh, branch_a_sf, _ = ensure_outlets(stdout, style)
    cat, _ = Category.objects.get_or_create(name="Pharmacy (ဆေးဆိုင်)", defaults={'order': 0})
    product, _ = Product.objects.get_or_create(
        sku="AMOX-E2E",
        defaults={
            'name': 'Amoxicillin',
            'category': cat,
            'retail_price': Decimal('120'),
            'cost_price': Decimal('0'),
            'unit_type': 'PCS',
            'base_unit': strip_u,
            'purchase_unit': box_u,
            'purchase_unit_factor': Decimal('10'),
        },
    )
    if not product.base_unit_id:
        product.base_unit, product.purchase_unit, product.purchase_unit_factor = strip_u, box_u, Decimal('10')
        product.save(update_fields=['base_unit', 'purchase_unit', 'purchase_unit_factor'])
    # Purchase 5 Boxes to Main
    purchase = Purchase.objects.create(outlet=main, reference="E2E-PH", created_by=user)
    PurchaseLine.objects.create(purchase=purchase, product=product, purchase_unit=box_u, quantity=Decimal('5'), unit_cost=Decimal('5000'), to_location=main_wh)
    base_qty = product.get_purchase_to_base_quantity(box_u, 5)
    cost_per_base = product.cost_per_base_unit(Decimal('5000'), box_u)
    InventoryMovement.objects.create(product=product, from_location=None, to_location=main_wh, quantity=base_qty, movement_type='inbound', moved_by=user, outlet=main, notes="E2E Purchase")
    product.cost_price = cost_per_base
    product.save(update_fields=['cost_price'])
    # Transfer 2 Boxes to Branch A
    transfer_qty = product.get_purchase_to_base_quantity(box_u, 2)
    InventoryMovement.objects.create(product=product, from_location=main_wh, to_location=branch_a_sf, quantity=transfer_qty, movement_type='transfer', moved_by=user, outlet=main, notes="E2E Transfer")
    stdout.write(style.SUCCESS("  Pharmacy: Amoxicillin 5 Boxes purchase, 2 Boxes transfer to Branch A"))


def run_mobile(stdout, style, user):
    Unit.objects.update_or_create(code='PCS', defaults={'name_my': 'တစ်လုံး', 'name_en': 'Pieces', 'category': 'count', 'order': 1})
    main, main_wh, branch_a_sf, _ = ensure_outlets(stdout, style)
    cat, _ = Category.objects.get_or_create(name="Mobile (ဖုန်းဆိုင်)", defaults={'order': 0})
    product, _ = Product.objects.get_or_create(
        sku="IPHONE15-E2E",
        defaults={
            'name': 'iPhone 15',
            'category': cat,
            'retail_price': Decimal('1500000'),
            'cost_price': Decimal('0'),
            'unit_type': 'PCS',
        },
    )
    # Purchase 10 units
    InventoryMovement.objects.create(product=product, from_location=None, to_location=main_wh, quantity=10, movement_type='inbound', moved_by=user, outlet=main, notes="E2E Purchase")
    # Transfer 3 to Branch A
    InventoryMovement.objects.create(product=product, from_location=main_wh, to_location=branch_a_sf, quantity=3, movement_type='transfer', moved_by=user, outlet=main, notes="E2E Transfer")
    stdout.write(style.SUCCESS("  Mobile: iPhone 15 x10 purchase, x3 transfer to Branch A"))


def run_electrical(stdout, style, user):
    Unit.objects.update_or_create(code='FEET', defaults={'name_my': 'ပေ', 'name_en': 'Feet', 'category': 'length', 'order': 1})
    Unit.objects.update_or_create(code='ROLL', defaults={'name_my': 'ခွေ', 'name_en': 'Roll', 'category': 'packaging', 'order': 2})
    feet_u = Unit.objects.get(code='FEET')
    roll_u = Unit.objects.get(code='ROLL')
    main, main_wh, branch_a_sf, _ = ensure_outlets(stdout, style)
    cat, _ = Category.objects.get_or_create(name="Electrical (လျှပ်စစ်)", defaults={'order': 0})
    product, _ = Product.objects.get_or_create(
        sku="WIRE-E2E",
        defaults={
            'name': 'Electric Wire',
            'category': cat,
            'retail_price': Decimal('150'),
            'cost_price': Decimal('0'),
            'unit_type': 'PCS',
            'base_unit': feet_u,
            'purchase_unit': roll_u,
            'purchase_unit_factor': Decimal('90'),
        },
    )
    if not product.base_unit_id:
        product.base_unit, product.purchase_unit, product.purchase_unit_factor = feet_u, roll_u, Decimal('90')
        product.save(update_fields=['base_unit', 'purchase_unit', 'purchase_unit_factor'])
    # Purchase 5 Rolls = 450 Feet
    purchase = Purchase.objects.create(outlet=main, reference="E2E-EL", created_by=user)
    PurchaseLine.objects.create(purchase=purchase, product=product, purchase_unit=roll_u, quantity=Decimal('5'), unit_cost=Decimal('12000'), to_location=main_wh)
    base_qty = product.get_purchase_to_base_quantity(roll_u, 5)
    cost_per_base = product.cost_per_base_unit(Decimal('12000'), roll_u)
    InventoryMovement.objects.create(product=product, from_location=None, to_location=main_wh, quantity=base_qty, movement_type='inbound', moved_by=user, outlet=main, notes="E2E Purchase")
    product.cost_price = cost_per_base
    product.save(update_fields=['cost_price'])
    # Transfer 1 Roll (90 Feet) to Branch A
    transfer_qty = product.get_purchase_to_base_quantity(roll_u, 1)
    InventoryMovement.objects.create(product=product, from_location=main_wh, to_location=branch_a_sf, quantity=transfer_qty, movement_type='transfer', moved_by=user, outlet=main, notes="E2E Transfer")
    stdout.write(style.SUCCESS("  Electrical: 5 Rolls Electric Wire purchase, 1 Roll transfer to Branch A"))


def run_solar(stdout, style, user):
    Unit.objects.update_or_create(code='PCS', defaults={'name_my': 'တစ်လုံး', 'name_en': 'Pieces', 'category': 'count', 'order': 1})
    main, main_wh, branch_a_sf, branch_a = ensure_outlets(stdout, style)
    branch_b = Outlet.objects.filter(code='BRANCH_B').first()
    if not branch_b:
        branch_b = Outlet.objects.create(name="Branch B", code="BRANCH_B", is_main_branch=False)
    branch_b_sf = branch_b.get_shopfloor_location()
    cat, _ = Category.objects.get_or_create(name="Solar (ဆိုလာ)", defaults={'order': 0})
    product, _ = Product.objects.get_or_create(
        sku="SOLAR-E2E",
        defaults={
            'name': 'Solar Panel',
            'category': cat,
            'retail_price': Decimal('85000'),
            'cost_price': Decimal('0'),
            'unit_type': 'PCS',
        },
    )
    # Purchase 20 to Main
    InventoryMovement.objects.create(product=product, from_location=None, to_location=main_wh, quantity=20, movement_type='inbound', moved_by=user, outlet=main, notes="E2E Purchase")
    # Transfer 5 to Branch B
    if branch_b_sf:
        InventoryMovement.objects.create(product=product, from_location=main_wh, to_location=branch_b_sf, quantity=5, movement_type='transfer', moved_by=user, outlet=main, notes="E2E Transfer")
    stdout.write(style.SUCCESS("  Solar: 20 Solar Panels purchase, 5 transfer to Branch B"))


class Command(BaseCommand):
    help = "E2E: Reset DB, migrate, setup shop (pharmacy|mobile|electrical|solar), run Purchase + Transfer"

    def add_arguments(self, parser):
        parser.add_argument('--shop', type=str, default='pharmacy', choices=['pharmacy', 'mobile', 'electrical', 'solar'])
        parser.add_argument('--no-flush', action='store_true')
        parser.add_argument('--no-migrate', action='store_true')

    def handle(self, *args, **options):
        style = self.style
        shop = options['shop']
        self.stdout.write(style.SUCCESS(f"\n=== E2E Shop Setup: {shop} ===\n"))

        if not options.get('no_flush'):
            call_command('flush', '--noinput')
        if not options.get('no_migrate'):
            call_command('migrate', '--noinput')

        with transaction.atomic():
            user = ensure_user(self.stdout, style)
            from core.models import Role
            Role.objects.get_or_create(name='Owner', defaults={'description': 'Full access'})
            owner = Role.objects.get(name='Owner')
            if not user.role_obj_id:
                user.role_obj = owner
                user.save(update_fields=['role_obj'])
            ensure_outlets(self.stdout, style)
            if shop == 'pharmacy':
                run_pharmacy(self.stdout, style, user)
            elif shop == 'mobile':
                run_mobile(self.stdout, style, user)
            elif shop == 'electrical':
                run_electrical(self.stdout, style, user)
            elif shop == 'solar':
                run_solar(self.stdout, style, user)

        self.stdout.write(style.SUCCESS("\n  Setup complete.\n"))
