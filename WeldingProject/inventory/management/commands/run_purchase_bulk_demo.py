"""
Demo: Bulk buy with purchase unit → stock in base unit.
Scenario: Buy 5 Bags of Dried Chili (1 Bag = 30 Viss) at 15,000 MMK/Bag.
Expected: Stock +150 Viss, unit cost 500 MMK/Viss.
Usage: python manage.py run_purchase_bulk_demo
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet
from inventory.models import Unit, Product, Category, Location, Purchase, PurchaseLine

User = get_user_model()


class Command(BaseCommand):
    help = "Demo: 5 Bags Dried Chili → 150 Viss stock, unit cost 500 MMK/Viss"

    def handle(self, *args, **options):
        style = self.style
        self.stdout.write(style.SUCCESS("\n=== Purchase Bulk Demo: Dried Chili (Bags → Viss) ===\n"))

        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if not user.check_password('admin123'):
            user.set_password('admin123')
            user.save()

        # Units: Viss (base), Bag (packaging) — no global conversion; product-level factor
        Unit.objects.update_or_create(
            code='VISS',
            defaults={'name_my': 'ပိဿာ', 'name_en': 'Viss', 'category': 'mass', 'order': 1},
        )
        Unit.objects.update_or_create(
            code='BAG',
            defaults={'name_my': 'အိတ်', 'name_en': 'Bag', 'category': 'packaging', 'order': 2},
        )
        viss = Unit.objects.get(code='VISS')
        bag_unit = Unit.objects.get(code='BAG')

        with transaction.atomic():
            outlet = Outlet.objects.filter(code='GROCERY').first()
            if not outlet:
                outlet = Outlet.objects.create(
                    name="ငရုပ်သီးဆိုင် (Grocery)",
                    is_main_branch=True,
                    code="GROCERY",
                )
            wh = outlet.get_warehouse_location()
            if not wh:
                raise RuntimeError("Outlet warehouse location not found. Run migrations and ensure Outlet creates locations.")
            retail = outlet.get_shopfloor_location() or wh

            cat, _ = Category.objects.get_or_create(name="Chili", defaults={'order': 0})
            product, created = Product.objects.get_or_create(
                sku="CHILI-001",
                defaults={
                    'name': "Dried Chili (ငရုပ်သီးခြောက်)",
                    'category': cat,
                    'retail_price': Decimal("600"),
                    'cost_price': Decimal("0"),
                    'unit_type': 'PCS',
                    'base_unit': viss,
                    'purchase_unit': bag_unit,
                    'purchase_unit_factor': Decimal("30"),
                },
            )
            if not created:
                product.base_unit = viss
                product.purchase_unit = bag_unit
                product.purchase_unit_factor = Decimal("30")
                product.save(update_fields=['base_unit', 'purchase_unit', 'purchase_unit_factor'])

            try:
                stock_before = product.get_stock_by_location(wh) or 0
            except Exception:
                stock_before = 0

            # Create purchase: 5 Bags @ 15,000 MMK → 150 Viss, cost 500/Viss
            purchase = Purchase.objects.create(
                outlet=outlet,
                reference="DEMO-001",
                created_by=user,
            )
            line = PurchaseLine.objects.create(
                purchase=purchase,
                product=product,
                purchase_unit=bag_unit,
                quantity=Decimal("5"),
                unit_cost=Decimal("15000"),
                to_location=wh,
            )
            base_qty = line.quantity_in_base_unit()
            cost_per_base = line.cost_per_base_unit()

            # Create inbound movement (normally done by PurchaseCreateView; we replicate for demo)
            from inventory.models import InventoryMovement
            InventoryMovement.objects.create(
                product=product,
                from_location=None,
                to_location=wh,
                quantity=base_qty,
                movement_type='inbound',
                moved_by=user,
                outlet=outlet,
                notes=f"Purchase #{purchase.id}: 5 Bags = {base_qty} Viss",
            )
            product.cost_price = cost_per_base
            product.save(update_fields=['cost_price'])

            stock_after = product.get_stock_by_location(wh)

        self.stdout.write(style.SUCCESS(f"  Product: {product.name}"))
        self.stdout.write(style.SUCCESS(f"  Base unit: {viss.name_my} ({viss.name_en})"))
        self.stdout.write(style.SUCCESS(f"  Purchase unit: {bag_unit.name_my} ({bag_unit.name_en}), 1 {bag_unit.name_en} = {product.purchase_unit_factor} {viss.name_en}"))
        self.stdout.write(style.SUCCESS(f"  Purchase: 5 Bags @ 15,000 MMK/Bag"))
        self.stdout.write(style.SUCCESS(f"  Quantity in base: {base_qty} {viss.name_en}"))
        self.stdout.write(style.SUCCESS(f"  Unit cost (per {viss.name_en}): {cost_per_base} MMK"))
        self.stdout.write(style.SUCCESS(f"  Stock at warehouse before: {stock_before}"))
        self.stdout.write(style.SUCCESS(f"  Stock at warehouse after:  {stock_after}"))
        if int(stock_after or 0) == 150 and float(cost_per_base) == 500:
            self.stdout.write(style.SUCCESS("\n  ✓ Scenario passed: 150 Viss in stock, 500 MMK per Viss.\n"))
        else:
            self.stdout.write(style.WARNING(f"\n  Check: expected 150 Viss and 500 MMK/Viss; got {stock_after} and {cost_per_base}\n"))
