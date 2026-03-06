"""
Main website မတင်ရသေးချိန် (သို့) offline — customer ရဲ့ machine_id နဲ့ license.lic ထုတ်ခြင်း
Customer က ဒီ ဖိုင်ကို EXE folder ထဲ ထည့်ရင် activate ဖြစ်မယ်။

Usage:
  # Key ကို ကိုယ်တိုင် ပေးမယ် (DB မစစ်ဘူး)
  python manage.py issue_license_file --machine-id <customer_machine_id> --type on_premise_perpetual

  # DB မှာ ရှိပြီးသား key နဲ့ bind မယ် (create_license လုပ်ထားရင်)
  python manage.py issue_license_file --key WLD-XXX-YYY --machine-id <customer_machine_id>

  # Hosted annual — သက်တမ်းသတ်မှတ်မယ်
  python manage.py issue_license_file --machine-id <mid> --type hosted_annual --expires 2026-12-31
"""
import json
import secrets
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from license.models import AppLicense, LicenseType


class Command(BaseCommand):
    help = 'Offline license.lic ထုတ်ခြင်း (main website မလိုပါ)'

    def add_arguments(self, parser):
        parser.add_argument('--machine-id', type=str, required=True, help='Customer ရဲ့ machine_id')
        parser.add_argument('--key', type=str, default=None, help='License key (DB မှာ ရှိရင် သုံးမယ်)')
        parser.add_argument(
            '--type',
            type=str,
            default='on_premise_perpetual',
            choices=['on_premise_perpetual', 'hosted_annual'],
            help='License အမျိုးအစား (--key မပေးရင် သုံးမယ်)',
        )
        parser.add_argument(
            '--expires',
            type=str,
            default=None,
            help='သက်တမ်းကုန်ရက် (hosted_annual အတွက်) ISO သို့ YYYY-MM-DD',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='license.lic',
            help='ထုတ်မယ့် ဖိုင် path (default: license.lic)',
        )

    def handle(self, *args, **options):
        machine_id = options['machine_id'].strip()
        key = options['key'].strip() if options.get('key') else None
        license_type = options['type']
        expires_str = options.get('expires')
        output_path = Path(options['output'])

        expires_at = None
        if key:
            lic = AppLicense.objects.filter(license_key=key, is_active=True).first()
            if not lic:
                self.stderr.write(self.style.ERROR(f'License key မတွေ့ပါ: {key} (DB မှာ create_license လုပ်ထားပါ။)'))
                return
            if lic.is_expired:
                self.stderr.write(self.style.ERROR('License သက်တမ်းကုန်ပြီးပါပြီ။'))
                return
            license_type = lic.license_type
            expires_at = lic.expires_at
        else:
            key = f"WLD-{secrets.token_hex(8).upper()}-{secrets.token_hex(4).upper()}"
            if expires_str:
                try:
                    from datetime import datetime
                    expires_at = datetime.strptime(expires_str[:10], '%Y-%m-%d')
                    if timezone.is_naive(expires_at):
                        expires_at = timezone.make_aware(expires_at)
                except Exception:
                    self.stderr.write(self.style.WARNING('--expires ကို YYYY-MM-DD ဖြစ်အောင် ထည့်ပါ။'))

        data = {
            'license_key': key,
            'machine_id': machine_id,
            'license_type': license_type,
            'expires_at': expires_at.isoformat() if expires_at else None,
        }
        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'license.lic ထုတ်ပြီး: {output_path.resolve()}'))
        self.stdout.write(f'  Key: {key}')
        self.stdout.write(f'  Machine ID: {machine_id}')
        self.stdout.write(f'  Type: {license_type}')
        if expires_at:
            self.stdout.write(f'  Expires: {expires_at.date()}')
        self.stdout.write('')
        self.stdout.write('Customer က ဒီ ဖိုင်ကို HoBoPOS.exe ရဲ့ folder ထဲ ထည့်ပါ (သို့) app မှာ License Activate နေရာမှာ key ထည့်ပြီး server ချိတ်ထားရင် activate လုပ်လို့ရပါတယ်။')
