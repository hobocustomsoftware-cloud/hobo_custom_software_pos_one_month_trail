"""
Export all data for a specific outlet into a SQL file and a ZIP of images.
Ready for standalone deployment on a paid customer's private server.
Usage: python manage.py export_shop <outlet_id>
"""
import io
import os
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = "Export outlet data to SQL + media ZIP for standalone deployment."

    def add_arguments(self, parser):
        parser.add_argument("outlet_id", type=int, help="Outlet ID to export")
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Directory for output files (default: current directory)",
        )

    def handle(self, *args, **options):
        outlet_id = options["outlet_id"]
        output_dir = (options.get("output_dir") or ".").strip() or "."
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"export_outlet_{outlet_id}_{ts}"

        from core.models import Outlet

        if not Outlet.objects.filter(pk=outlet_id).exists():
            self.stderr.write(self.style.ERROR(f"Outlet id={outlet_id} not found."))
            return

        os.makedirs(output_dir, exist_ok=True)
        sql_path = os.path.join(output_dir, f"{base_name}.sql")
        zip_path = os.path.join(output_dir, f"{base_name}_media.zip")
        json_path = os.path.join(output_dir, f"{base_name}.json")

        # Collect outlet-scoped data and related FKs (no duplicates)
        self.stdout.write("Collecting outlet-scoped data...")
        seen = set()  # (model_label, pk)
        def add(obj):
            if obj is None:
                return
            key = (type(obj).__module__ + "." + type(obj).__name__, obj.pk)
            if key in seen:
                return
            seen.add(key)
            objects.append(obj)

        objects = []
        media_files = set()

        # Core: Outlet, Users (primary_outlet), AuditLog
        from django.contrib.auth import get_user_model
        from core.models import Outlet as OutletModel, AuditLog

        User = get_user_model()
        for o in OutletModel.objects.filter(pk=outlet_id):
            add(o)
        for u in User.objects.filter(primary_outlet_id=outlet_id).select_related("role_obj"):
            add(u)
        for a in AuditLog.objects.filter(outlet_id=outlet_id):
            add(a)

        # Inventory: Location, SaleTransaction, Sale, InventoryMovement, SaleItem, Product (referenced)
        from inventory.models import (
            Location,
            SaleTransaction,
            Sale,
            InventoryMovement,
            SaleItem,
            Product,
        )

        loc_ids = list(Location.objects.filter(outlet_id=outlet_id).values_list("pk", flat=True))
        for loc in Location.objects.filter(outlet_id=outlet_id):
            add(loc)

        for t in SaleTransaction.objects.filter(outlet_id=outlet_id).select_related("customer", "staff", "sale_location", "payment_method"):
            add(t)
            if t.payment_proof_screenshot and hasattr(t.payment_proof_screenshot, "path"):
                try:
                    media_files.add(t.payment_proof_screenshot.path)
                except Exception:
                    pass

        for s in Sale.objects.filter(outlet_id=outlet_id):
            add(s)

        st_ids = list(SaleTransaction.objects.filter(outlet_id=outlet_id).values_list("pk", flat=True))
        for item in SaleItem.objects.filter(sale_transaction_id__in=st_ids).select_related("product"):
            add(item)
            if item.product_id and item.product.image and hasattr(item.product.image, "path"):
                try:
                    media_files.add(item.product.image.path)
                except Exception:
                    pass

        for m in InventoryMovement.objects.filter(outlet_id=outlet_id).select_related("product", "from_location", "to_location"):
            add(m)
            if m.product_id and m.product.image and hasattr(m.product.image, "path"):
                try:
                    media_files.add(m.product.image.path)
                except Exception:
                    pass

        product_ids = set()
        for m in InventoryMovement.objects.filter(outlet_id=outlet_id).values_list("product_id", flat=True):
            product_ids.add(m)
        for item in SaleItem.objects.filter(sale_transaction_id__in=st_ids).values_list("product_id", flat=True):
            if item:
                product_ids.add(item)
        for p in Product.objects.filter(pk__in=product_ids):
            add(p)
            if p.image and hasattr(p.image, "path"):
                try:
                    media_files.add(p.image.path)
                except Exception:
                    pass

        # Roles referenced by exported users
        from core.models import Role
        role_ids = {getattr(u, "role_obj_id", None) for u in User.objects.filter(primary_outlet_id=outlet_id) if getattr(u, "role_obj_id", None)}
        for r in Role.objects.filter(pk__in=role_ids):
            add(r)

        # Accounting: Expense, Transaction, ExpenseCategory
        from accounting.models import Expense, Transaction, ExpenseCategory

        expenses = list(Expense.objects.filter(outlet_id=outlet_id).select_related("category", "created_by"))
        for e in expenses:
            add(e)
        exp_ids = [e.pk for e in expenses]
        for t in Transaction.objects.filter(expense_id__in=exp_ids) | Transaction.objects.filter(sale_transaction_id__in=st_ids):
            add(t)
        cat_ids = {e.category_id for e in expenses if e.category_id}
        for c in ExpenseCategory.objects.filter(pk__in=cat_ids):
            add(c)

        # Customer referenced by sale transactions
        from customer.models import Customer
        cust_ids = list(SaleTransaction.objects.filter(outlet_id=outlet_id).exclude(customer_id=None).values_list("customer_id", flat=True))
        for c in Customer.objects.filter(pk__in=cust_ids):
            add(c)

        # PaymentMethod referenced
        from inventory.models import PaymentMethod
        pm_ids = list(SaleTransaction.objects.filter(outlet_id=outlet_id).exclude(payment_method_id=None).values_list("payment_method_id", flat=True))
        for pm in PaymentMethod.objects.filter(pk__in=pm_ids):
            add(pm)

        # 1) Write JSON fixture (loaddata-compatible)
        with open(json_path, "w", encoding="utf-8") as f:
            serializers.serialize("json", objects, indent=2, stream=f, use_natural_foreign_keys=True, use_natural_primary_keys=False)
        self.stdout.write(self.style.SUCCESS(f"Wrote {json_path}"))

        # 2) Write SQL (minimal: comments + instructions to load JSON)
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(f"-- Export outlet_id={outlet_id} at {datetime.now().isoformat()}\n")
            f.write("-- Load fixture: python manage.py loaddata " + os.path.basename(json_path) + "\n")
            f.write("-- Or use the JSON file with your import script.\n")
        self.stdout.write(self.style.SUCCESS(f"Wrote {sql_path}"))

        # 3) ZIP media files
        media_root = getattr(settings, "MEDIA_ROOT", None) or ""
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for abs_path in media_files:
                if not os.path.isfile(abs_path):
                    continue
                try:
                    rel = os.path.relpath(abs_path, media_root) if media_root else os.path.basename(abs_path)
                    zf.write(abs_path, os.path.join("media", rel))
                except Exception as e:
                    self.stderr.write(f"Skip {abs_path}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Wrote {zip_path} ({len(media_files)} files)"))

        self.stdout.write(self.style.SUCCESS(f"Done. Use {json_path} with loaddata and extract {zip_path} to MEDIA_ROOT for standalone deploy."))
