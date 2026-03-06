"""
Fetch daily exchange rates from CBM API and store in ExchangeRateLog.
Also supports web scraping as fallback.
Run: python manage.py fetch_exchange_rates
Scheduled: Daily at 10:00 AM via Celery or cron
"""
import json
import requests
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from inventory.models import ExchangeRateLog, GlobalSetting
from inventory.scraper_service import scrape_cbm_usd_rate, Notification
from core.models import User, Role


class Command(BaseCommand):
    help = 'Fetch exchange rates from CBM API (USD, THB, SGD) and store in ExchangeRateLog'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if rate already exists for today',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode: print rates without saving',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Fetching exchange rates from CBM API...'))
        
        today = timezone.now().date()
        force = options.get('force', False)
        test_mode = options.get('test', False)

        # Check if rates already exist for today
        if not force and not test_mode:
            existing = ExchangeRateLog.objects.filter(date=today).exists()
            if existing:
                self.stdout.write(self.style.WARNING(f'Rates already exist for {today}. Use --force to update.'))
                return

        # Try API first, then fallback to web scraping
        api_success = False
        try:
            # Fetch from CBM API
            response = requests.get(
                'https://forex.cbm.gov.mm/api/latest',
                timeout=10,
                headers={'User-Agent': 'HoBo-POS/1.0'}
            )
            response.raise_for_status()
            data = response.json()
            api_success = True
            self.stdout.write(self.style.SUCCESS('✓ Successfully fetched data from CBM API'))

            # Parse rates (CBM API structure may vary, adjust as needed)
            rates = {}
            
            # CBM API structure: {"rates": {"USD": {"rate": "2,100.00"}, "THB": {...}}}
            # Or: {"USD": "2,100.00", "THB": "50.00"}
            rates_data = {}
            
            if 'rates' in data:
                # Structure: {"rates": {"USD": {...}, "THB": {...}}}
                rates_data = data.get('rates', {})
            elif isinstance(data, dict):
                # Check if top-level keys are currencies
                for key in ['USD', 'THB', 'SGD']:
                    if key in data:
                        rates_data[key] = data[key]
                # If not found, try nested structure
                if not rates_data:
                    rates_data = data

            # Extract USD, THB, SGD rates
            currencies_to_fetch = ['USD', 'THB', 'SGD']
            
            for currency in currencies_to_fetch:
                rate_value = None
                
                # Try different field names and structures
                if currency in rates_data:
                    currency_data = rates_data[currency]
                    if isinstance(currency_data, dict):
                        # Try common field names
                        rate_value = (
                            currency_data.get('rate') or
                            currency_data.get('value') or
                            currency_data.get('mmk') or
                            currency_data.get('amount') or
                            currency_data.get('buy') or
                            currency_data.get('sell')
                        )
                        # If still None, try first numeric value
                        if rate_value is None:
                            for v in currency_data.values():
                                if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(',', '').replace('.', '').isdigit()):
                                    rate_value = v
                                    break
                    elif isinstance(currency_data, (int, float, str)):
                        rate_value = currency_data
                
                # If not found, try case-insensitive search
                if rate_value is None:
                    for key in rates_data.keys():
                        if currency.upper() in str(key).upper():
                            val = rates_data[key]
                            if isinstance(val, dict):
                                rate_value = val.get('rate') or val.get('value') or val.get('mmk')
                            elif isinstance(val, (int, float, str)):
                                rate_value = val
                            break

                if rate_value is None:
                    self.stdout.write(self.style.WARNING(f'⚠ {currency} rate not found in API response'))
                    # Use fallback: last recorded rate
                    rate_value = self._get_fallback_rate(currency)
                    if rate_value:
                        self.stdout.write(self.style.WARNING(f'  Using fallback rate: {rate_value}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  No fallback rate available for {currency}'))
                        continue

                # Clean and convert rate
                try:
                    # Handle string rates like "2,100.00"
                    if isinstance(rate_value, str):
                        rate_value = rate_value.replace(',', '').strip()
                    rate_decimal = Decimal(str(rate_value))
                    
                    # Apply manual adjustments if configured
                    final_rate = self._apply_manual_adjustments(currency, rate_decimal)
                    
                    if test_mode:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  {currency}: {rate_decimal} → {final_rate} MMK '
                                f'(source: {"Manual" if final_rate != rate_decimal else "CBM"})'
                            )
                        )
                    else:
                        # Save to ExchangeRateLog
                        with transaction.atomic():
                            log, created = ExchangeRateLog.objects.update_or_create(
                                date=today,
                                currency=currency,
                                defaults={
                                    'rate': final_rate,
                                    'source': 'Manual' if final_rate != rate_decimal else 'CBM',
                                }
                            )
                            
                            # Update GlobalSetting for USD (for backward compatibility)
                            if currency == 'USD':
                                old_rate = None
                                gs, _ = GlobalSetting.objects.get_or_create(
                                    key='usd_exchange_rate',
                                    defaults={'value_decimal': final_rate}
                                )
                                if gs.value_decimal:
                                    old_rate = gs.value_decimal
                                
                                rate_changed = gs.value_decimal != final_rate
                                
                                if rate_changed:
                                    gs.value_decimal = final_rate
                                    gs.save(update_fields=['value_decimal'])
                                    
                                    # Auto-sync DYNAMIC_USD product prices
                                    if not test_mode:
                                        from .services import sync_all_prices
                                        updated_count = sync_all_prices(final_rate, round_base=100)
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f'  ✓ Synced {updated_count} DYNAMIC_USD product prices'
                                            )
                                        )
                                    
                                    # AI Insight: Check for >1% change and notify Owner
                                    if old_rate and not test_mode:
                                        rate_change_percent = abs((float(final_rate) - float(old_rate)) / float(old_rate)) * 100
                                        if rate_change_percent > 1.0:
                                            self._create_rate_change_notification(
                                                currency,
                                                float(old_rate),
                                                float(final_rate),
                                                rate_change_percent
                                            )
                            
                            action = 'Created' if created else 'Updated'
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ {action} {currency}: {final_rate} MMK'
                                )
                            )

                except (InvalidOperation, ValueError) as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Invalid rate value for {currency}: {rate_value} ({e})')
                    )
                    # Try fallback
                    fallback = self._get_fallback_rate(currency)
                    if fallback:
                        self.stdout.write(self.style.WARNING(f'  Using fallback: {fallback}'))
                        if not test_mode:
                            ExchangeRateLog.objects.update_or_create(
                                date=today,
                                currency=currency,
                                defaults={'rate': fallback, 'source': 'Fallback'}
                            )

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.WARNING(f'⚠ CBM API failed: {e}. Trying web scraping...'))
            api_success = False
        
        # If API failed, try web scraping for USD
        scraped_rate = None
        if not api_success:
            scraped_rate = scrape_cbm_usd_rate()
            if scraped_rate:
                self.stdout.write(self.style.SUCCESS(f'✓ Successfully scraped USD rate: {scraped_rate} MMK'))
                if not test_mode:
                    with transaction.atomic():
                        log, created = ExchangeRateLog.objects.update_or_create(
                            date=today,
                            currency='USD',
                            defaults={
                                'rate': scraped_rate,
                                'source': 'Scraped',
                            }
                        )
                        # Update GlobalSetting (create if missing) so Sidebar shows rate
                        gs, _ = GlobalSetting.objects.get_or_create(
                            key='usd_exchange_rate',
                            defaults={'value_decimal': scraped_rate, 'is_auto_sync': True}
                        )
                        if gs.is_auto_sync is not False:
                            gs.value_decimal = scraped_rate
                            gs.save(update_fields=['value_decimal'])
                        # Auto-sync DYNAMIC_USD product prices when rate is updated via scraping
                        from inventory.services import sync_all_prices
                        updated_count = sync_all_prices(scraped_rate, round_base=100)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Synced {updated_count} DYNAMIC_USD product prices'
                            )
                        )
                        action = 'Created' if created else 'Updated'
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ {action} USD (scraped): {scraped_rate} MMK'
                            )
                        )
                else:
                    self.stdout.write(self.style.SUCCESS(f'  USD (scraped): {scraped_rate} MMK'))
                # Mark USD as processed
                currencies_to_fetch = [c for c in currencies_to_fetch if c != 'USD']
        
        if not api_success and not scraped_rate:
            self.stdout.write(self.style.ERROR('✗ Both API and scraping failed. Using fallback rates...'))
            # Fallback: use last recorded rates
            for currency in currencies_to_fetch:
                fallback_rate = self._get_fallback_rate(currency)
                if fallback_rate:
                    if test_mode:
                        self.stdout.write(self.style.WARNING(f'  {currency} (fallback): {fallback_rate} MMK'))
                    else:
                        ExchangeRateLog.objects.update_or_create(
                            date=today,
                            currency=currency,
                            defaults={'rate': fallback_rate, 'source': 'Fallback'}
                        )
                        # For USD, also update GlobalSetting and sync prices
                        if currency == 'USD':
                            from .models import GlobalSetting
                            from .services import sync_all_prices
                            gs, _ = GlobalSetting.objects.get_or_create(
                                key='usd_exchange_rate',
                                defaults={'value_decimal': fallback_rate}
                            )
                            if gs.value_decimal != fallback_rate:
                                gs.value_decimal = fallback_rate
                                gs.save(update_fields=['value_decimal'])
                            # Sync prices even with fallback rate
                            updated_count = sync_all_prices(fallback_rate, round_base=100)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Saved {currency} (fallback): {fallback_rate} MMK, synced {updated_count} prices'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Saved {currency} (fallback): {fallback_rate} MMK')
                            )
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ No fallback rate available for {currency}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Unexpected error: {e}'))
            raise

    def _get_fallback_rate(self, currency):
        """Get last recorded rate from ExchangeRateLog or GlobalSetting (for USD)"""
        # Try ExchangeRateLog first
        last_log = ExchangeRateLog.objects.filter(currency=currency).order_by('-date').first()
        if last_log:
            return last_log.rate
        
        # For USD, try GlobalSetting
        if currency == 'USD':
            gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
            if gs and gs.value_decimal:
                return gs.value_decimal
        
        return None

    def _apply_manual_adjustments(self, currency, base_rate):
        """Apply manual adjustments (Market Premium % or Manual Fixed Rate)"""
        # Get GlobalSetting for this currency
        key = f'{currency.lower()}_exchange_rate'
        gs = GlobalSetting.objects.filter(key=key).first()
        
        # If not found, try generic 'usd_exchange_rate' for USD
        if not gs and currency == 'USD':
            gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
        
        if not gs:
            return base_rate
        
        # Check for manual fixed rate (highest priority)
        if gs.manual_fixed_rate is not None:
            return gs.manual_fixed_rate
        
        # Apply market premium percentage
        if gs.market_premium_percentage is not None:
            premium = float(gs.market_premium_percentage) / 100
            return Decimal(str(float(base_rate) * (1 + premium)))
        
        return base_rate

    def _create_rate_change_notification(self, currency, old_rate, new_rate, change_percent):
        """Create notification for Owner when rate changes >1%"""
        from inventory.models import Notification
        from core.models import User, Role
        
        # Find Owner role users
        owner_role = Role.objects.filter(name__iexact='owner').first()
        if not owner_role:
            return
        
        owners = User.objects.filter(role_obj=owner_role)
        if not owners.exists():
            return
        
        # Determine trend
        trend = 'increased' if new_rate > old_rate else 'decreased'
        trend_icon = '📈' if new_rate > old_rate else '📉'
        
        message = (
            f"{trend_icon} {currency} Exchange Rate {trend} by {change_percent:.2f}%: "
            f"{old_rate:,.2f} → {new_rate:,.2f} MMK. "
            f"DYNAMIC_USD product prices have been auto-synced. "
            f"Consider reviewing pricing strategy."
        )
        
        # Create notification for each owner
        for owner in owners:
            Notification.objects.create(
                recipient=owner,
                notification_type='rate_change',
                message=message,
                is_read=False,
            )
        
        self.stdout.write(
            self.style.WARNING(
                f'  ⚠ Rate change >1% detected. Notification sent to {owners.count()} owner(s).'
            )
        )
