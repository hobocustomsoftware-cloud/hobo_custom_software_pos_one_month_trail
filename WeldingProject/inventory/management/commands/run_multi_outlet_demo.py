"""
Single-Tenancy Multi-Outlet Demo. Run AFTER: python manage.py flush --noinput
Step 2: Create 1 Main Warehouse + 2 Retail Outlets (Branch A, Branch B).
Step 3: Inventory actions per shop type.
Step 4: Print summary table | Product | Location | Stock (Base Unit) | Unit Cost |

Usage:
  python manage.py flush --noinput
  python manage.py run_multi_outlet_demo --shop pharmacy
  # Wait for user 'Next', then:
  python manage.py run_multi_outlet_demo --shop mobile
  ...
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet
from inventory.models import (
    Unit, Product, Category, Location, InventoryMovement,
    Purchase, PurchaseLine,
)

User = get_user_model()


def ensure_user(stdout, style):
    """Create admin user (required after flush)."""
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
    )
    if created or not user.check_password('admin123'):
        user.set_password('admin123')
        user.save()
        stdout.write(style.SUCCESS("  Created/updated user: admin / admin123"))
    return user


def setup_outlets(stdout, style):
    """
    Step 2: Create 1 Main Warehouse (Main outlet) + 2 Retail Outlets (Branch A, Branch B).
    Each Outlet gets Warehouse + Shopfloor via signal.
    Returns: (main_outlet, main_wh, main_sf, branch_a_outlet, branch_a_sf, branch_b_outlet, branch_b_sf)
    """
    main = Outlet.objects.filter(code='MAIN').first()
    if not main:
        main = Outlet.objects.create(
            name="Main Warehouse",
            code="MAIN",
            is_main_branch=True,
        )
    main_wh = main.get_warehouse_location()
    main_sf = main.get_shopfloor_location()
    if not main_wh or not main_sf:
        raise RuntimeError("Main outlet missing warehouse or shopfloor.")

    branch_a = Outlet.objects.filter(code='BRANCH_A').first()
    if not branch_a:
        branch_a = Outlet.objects.create(name="Branch A", code="BRANCH_A", is_main_branch=False)
    branch_a_sf = branch_a.get_shopfloor_location()
    branch_a_wh = branch_a.get_warehouse_location()

    branch_b = Outlet.objects.filter(code='BRANCH_B').first()
    if not branch_b:
        branch_b = Outlet.objects.create(name="Branch B", code="BRANCH_B", is_main_branch=False)
    branch_b_sf = branch_b.get_shopfloor_location()
    branch_b_wh = branch_b.get_warehouse_location()

    stdout.write(style.SUCCESS("  Outlets: Main (Warehouse + Shopfloor), Branch A, Branch B"))
    return main, main_wh, main_sf, branch_a, branch_a_wh, branch_a_sf, branch_b, branch_b_wh, branch_b_sf


def print_summary_table(stdout, style, products, locations):
    """Step 4: Print | Product | Location | Stock (Base Unit) | Unit Cost |"""
    def base_name(p):
        return (p.base_unit.name_en if getattr(p, 'base_unit', None) else None) or "Unit"

    rows = []
    for product in products:
        for loc in locations:
            try:
                stock = product.get_stock_by_location(loc)
            except Exception:
                stock = 0
            if stock is None:
                stock = 0
            try:
                has_stock = float(stock) != 0
            except (TypeError, ValueError):
                has_stock = stock != 0
            if has_stock:
                unit_cost = product.cost_price or 0
                u = base_name(product)
                rows.append((product.name, loc.name, stock, unit_cost, u))

    if not rows:
        stdout.write(style.WARNING("  No stock rows to display."))
        return

    col_product = max(len("Product"), max(len(str(r[0])) for r in rows))
    col_location = max(len("Location"), max(len(str(r[1])) for r in rows))
    col_stock = max(len("Stock (Base Unit)"), max(len(str(r[2]) + " " + str(r[4])) for r in rows))
    col_cost = max(len("Unit Cost"), max(len(str(r[3])) for r in rows))

    h = f"| {'Product'.ljust(col_product)} | {'Location'.ljust(col_location)} | {'Stock (Base Unit)'.ljust(col_stock)} | {'Unit Cost'.ljust(col_cost)} |"
    sep = "|-" + "-" * col_product + "-|-" + "-" * col_location + "-|-" + "-" * col_stock + "-|-" + "-" * col_cost + "-|"
    stdout.write("")
    stdout.write(style.SUCCESS("  " + h))
    stdout.write("  " + sep)
    for r in rows:
        stock_display = f"{r[2]} {r[4]}"
        line = f"| {(r[0] or '').ljust(col_product)} | {(r[1] or '').ljust(col_location)} | {stock_display.ljust(col_stock)} | {str(r[3]).ljust(col_cost)} |"
        stdout.write("  " + line)
    stdout.write("")


def run_pharmacy(stdout, style, user, main_wh, main_sf, branch_a_sf):
    """Pharmacy (ဆေးဆိုင်): Amoxicillin — Buy 10 Boxes (1 Box = 10 Strips) to Warehouse, Transfer 2 Boxes to Branch A."""
    Unit.objects.update_or_create(code='STRIP', defaults={'name_my': 'ကတ်', 'name_en': 'Strip', 'category': 'count', 'order': 1})
    Unit.objects.update_or_create(code='BOX', defaults={'name_my': 'ဗူး/ဘူး', 'name_en': 'Box', 'category': 'packaging', 'order': 2})
    strip_unit = Unit.objects.get(code='STRIP')
    box_unit = Unit.objects.get(code='BOX')

    cat, _ = Category.objects.get_or_create(name="Pharmacy (ဆေးဆိုင်)", defaults={'order': 0})
    product, _ = Product.objects.get_or_create(
        sku="AMOX-001",
        defaults={
            'name': 'Amoxicillin',
            'category': cat,
            'retail_price': Decimal('120'),
            'cost_price': Decimal('0'),
            'unit_type': 'PCS',
            'base_unit': strip_unit,
            'purchase_unit': box_unit,
            'purchase_unit_factor': Decimal('10'),
        },
    )
    if not product.base_unit_id:
        product.base_unit = strip_unit
        product.purchase_unit = box_unit
        product.purchase_unit_factor = Decimal('10')
        product.save(update_fields=['base_unit', 'purchase_unit', 'purchase_unit_factor'])

    # Buy 10 Boxes to Main Warehouse = 100 Strips
    main_outlet = main_wh.outlet
    purchase = Purchase.objects.create(outlet=main_outlet, reference="PH-001", created_by=user)
    PurchaseLine.objects.create(
        purchase=purchase,
        product=product,
        purchase_unit=box_unit,
        quantity=Decimal('10'),
        unit_cost=Decimal('5000'),
        to_location=main_wh,
    )
    base_qty = product.get_purchase_to_base_quantity(box_unit, 10)
    cost_per_base = product.cost_per_base_unit(Decimal('5000'), box_unit)
    InventoryMovement.objects.create(
        product=product,
        from_location=None,
        to_location=main_wh,
        quantity=base_qty,
        movement_type='inbound',
        moved_by=user,
        outlet=main_outlet,
        notes="Purchase: 10 Boxes = 100 Strips",
    )
    product.cost_price = cost_per_base
    product.save(update_fields=['cost_price'])

    # Transfer 2 Boxes (20 Strips) to Branch A
    transfer_qty = product.get_purchase_to_base_quantity(box_unit, 2)
    InventoryMovement.objects.create(
        product=product,
        from_location=main_wh,
        to_location=branch_a_sf,
        quantity=transfer_qty,
        movement_type='transfer',
        moved_by=user,
        outlet=main_outlet,
        notes="Transfer 2 Boxes to Branch A",
    )

    locations = [main_wh, main_sf, branch_a_sf]
    return [product], locations


class Command(BaseCommand):
    help = "Multi-Outlet Demo: run after flush. --shop pharmacy | mobile | electrical | solar"

    def add_arguments(self, parser):
        parser.add_argument('--shop', type=str, default='pharmacy', choices=['pharmacy', 'mobile', 'electrical', 'solar'])

    def handle(self, *args, **options):
        style = self.style
        shop = (options.get('shop') or 'pharmacy').lower()
        self.stdout.write(style.SUCCESS("\n=== Single-Tenancy Multi-Outlet Demo ===\n"))
        self.stdout.write(style.SUCCESS("  Step 1: (You should have run: python manage.py flush --noinput)\n"))
        self.stdout.write(style.SUCCESS("  Step 2: Setup — 1 Main Warehouse + 2 Retail Outlets (Branch A, Branch B)\n"))

        user = ensure_user(self.stdout, style)
        main, main_wh, main_sf, branch_a, branch_a_wh, branch_a_sf, branch_b, branch_b_wh, branch_b_sf = setup_outlets(self.stdout, style)

        self.stdout.write(style.SUCCESS("\n  Step 3: Inventory Action — Shop type: {}\n".format(shop)))

        products = []
        locations = []

        if shop == 'pharmacy':
            self.stdout.write(style.SUCCESS("  Pharmacy (ဆေးဆိုင်): Buy 10 Boxes Amoxicillin (1 Box=10 Strips) to Warehouse. Transfer 2 Boxes to Branch A.\n"))
            with transaction.atomic():
                products, locations = run_pharmacy(self.stdout, style, user, main_wh, main_sf, branch_a_sf)
        elif shop == 'mobile':
            self.stdout.write(style.WARNING("  Mobile Shop (ဖုန်းဆိုင်): Not implemented in this step. Run after 'Next'."))
            return
        elif shop == 'electrical':
            self.stdout.write(style.WARNING("  Electrical (လျှပ်စစ်): Not implemented in this step."))
            return
        elif shop == 'solar':
            self.stdout.write(style.WARNING("  Solar (ဆိုလာ): Not implemented in this step."))
            return

        self.stdout.write(style.SUCCESS("  Step 4: Verification — Summary table\n"))
        print_summary_table(self.stdout, style, products, locations)
        self.stdout.write(style.SUCCESS("\n  Done. Say 'Next' to run Mobile Shop scenario.\n"))
