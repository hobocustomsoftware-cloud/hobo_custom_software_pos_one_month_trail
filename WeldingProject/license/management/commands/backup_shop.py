"""Per-shop backup: every shop can export its own data file (self-service).

- Local export (free, always): python manage.py backup_shop --shop-id 1
  writes a timestamped JSON dump scoped to that shop (ShopSettings tenant).
- Cloud copy (paid add-on): same command with --cloud uploads the file only
  when a valid BackupAddOn exists for the shop/machine (see
  license.models.BackupAddOn). Without the add-on the command keeps the
  local file and prints how to buy it.
"""
import os
from datetime import datetime

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Export one shop's data (ShopSettings tenant) to a JSON backup file."

    def add_arguments(self, parser):
        parser.add_argument("--shop-id", type=int, default=1)
        parser.add_argument("--output-dir", type=str, default="backups")
        parser.add_argument("--cloud", action="store_true",
                            help="Also keep a cloud copy (requires backup add-on).")

    def handle(self, *args, **options):
        from core.models import ShopSettings
        try:
            shop = ShopSettings.objects.get(pk=options["shop_id"])
        except ShopSettings.DoesNotExist:
            raise CommandError(f"Shop id={options['shop_id']} not found.")

        outdir = options["output_dir"].strip() or "backups"
        os.makedirs(outdir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(outdir, f"backup_shop_{shop.pk}_{ts}.json")

        objects = [shop]
        objects += list(shop.outlets.all())
        objects += list(shop.users.all())
        objects += list(shop.backup_addons.all())
        for outlet in shop.outlets.all():
            objects += list(outlet.locations.all())
            objects += list(outlet.staff.all())

        with open(path, "w", encoding="utf-8") as f:
            f.write(serializers.serialize("json", objects, indent=1))
        self.stdout.write(self.style.SUCCESS(f"Backup written: {path}"))

        if options["cloud"]:
            from license.models import BackupAddOn
            from license.utils import get_machine_id
            machine_id = get_machine_id()
            addon = BackupAddOn.objects.filter(machine_id=machine_id, is_active=True).first()
            if not addon:
                addon = BackupAddOn.objects.filter(shop=shop, is_active=True).first()
            if not addon or not addon.is_valid:
                self.stdout.write(self.style.WARNING(
                    "No valid backup add-on: cloud copy skipped. "
                    "Activate one via POST /api/license/backup/activate/."
                ))
                return
            dest = os.environ.get("BACKUP_CLOUD_DIR", os.path.join(outdir, "cloud"))
            os.makedirs(dest, exist_ok=True)
            import shutil
            shutil.copy2(path, os.path.join(dest, os.path.basename(path)))
            self.stdout.write(self.style.SUCCESS(f"Cloud copy kept: {dest}"))
