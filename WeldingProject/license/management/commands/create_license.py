"""
License key ဖန်တီးခြင်း
Usage: python manage.py create_license --type on_premise_perpetual
       python manage.py create_license --type hosted_annual --years 1
"""
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from license.models import AppLicense, LicenseType


class Command(BaseCommand):
    help = 'License key ဖန်တီးခြင်း'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='on_premise_perpetual',
            choices=['on_premise_perpetual', 'hosted_annual', 'trial'],
            help='License အမျိုးအစား',
        )
        parser.add_argument(
            '--years',
            type=int,
            default=1,
            help='Hosted annual အတွက် နှစ်အရေအတွက်',
        )

    def handle(self, *args, **options):
        lic_type = options['type']
        years = options['years']

        # Unique license key ထုတ်ခြင်း
        key = f"WLD-{secrets.token_hex(8).upper()}-{secrets.token_hex(4).upper()}"

        expires_at = None
        if lic_type == LicenseType.HOSTED_ANNUAL:
            expires_at = timezone.now() + timedelta(days=365 * years)

        lic = AppLicense.objects.create(
            license_type=lic_type,
            license_key=key,
            expires_at=expires_at,
            is_active=True,
        )

        self.stdout.write(self.style.SUCCESS('License created successfully.'))
        self.stdout.write(f'  Key: {key}')
        self.stdout.write(f'  Type: {lic_type}')
        if expires_at:
            self.stdout.write(f'  Expires: {expires_at.date()}')
