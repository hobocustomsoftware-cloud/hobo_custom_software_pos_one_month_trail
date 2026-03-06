"""
Django signals for inventory models.
Handles auto-sync of DYNAMIC_USD product prices when exchange rate changes.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
from datetime import timedelta

from .models import GlobalSetting, ExchangeRateLog
from .services import sync_prices_on_rate_change

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=GlobalSetting)
def track_rate_change(sender, instance, **kwargs):
    """Store old rate before save to detect changes."""
    if instance.key == 'usd_exchange_rate':
        try:
            old_instance = GlobalSetting.objects.get(pk=instance.pk)
            instance._old_rate = old_instance.get_active_usd_rate
            instance._old_is_auto_sync = old_instance.is_auto_sync
        except GlobalSetting.DoesNotExist:
            instance._old_rate = None
            instance._old_is_auto_sync = None


@receiver(post_save, sender=GlobalSetting)
def auto_sync_prices_on_rate_change(sender, instance, created, **kwargs):
    """
    Auto-sync DYNAMIC_USD product prices when exchange rate changes.
    Triggers when:
    - is_auto_sync changes
    - manual_usd_rate changes (when is_auto_sync=False)
    - value_decimal changes (legacy support)
    """
    if instance.key != 'usd_exchange_rate':
        return
    
    old_rate = getattr(instance, '_old_rate', None)
    old_is_auto_sync = getattr(instance, '_old_is_auto_sync', None)
    new_rate = instance.get_active_usd_rate
    
    # Check if rate actually changed
    rate_changed = False
    if old_rate is None and new_rate is not None:
        rate_changed = True
    elif old_rate is not None and new_rate is not None:
        if abs(float(old_rate) - float(new_rate)) > Decimal('0.01'):  # More than 0.01 MMK difference
            rate_changed = True
    
    # Check if sync mode changed
    sync_mode_changed = (old_is_auto_sync != instance.is_auto_sync)
    
    if rate_changed or sync_mode_changed:
        if new_rate:
            try:
                with transaction.atomic():
                    updated_count = sync_prices_on_rate_change(new_rate, round_base=100)
                    logger.info(
                        f'Auto-synced {updated_count} DYNAMIC_USD product prices. '
                        f'Rate: {old_rate} → {new_rate}, Mode: {"AUTO" if instance.is_auto_sync else "MANUAL"}'
                    )
            except Exception as e:
                logger.error(f'Failed to auto-sync prices: {e}', exc_info=True)


@receiver(post_save, sender=ExchangeRateLog)
def auto_sync_on_scraped_rate(sender, instance, created, **kwargs):
    """
    Auto-sync prices when a new scraped rate is saved (if auto-sync is enabled).
    Also checks for >1% fluctuation and sends Price Risk Alert.
    """
    if instance.currency != 'USD':
        return
    
    # Only trigger if this is a scraped/CBM rate and auto-sync is enabled
    if instance.source not in ['CBM', 'Scraped']:
        return
    
    gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
    if not gs or not gs.is_auto_sync:
        return
    
    # Check if this is the latest rate for today
    from django.utils import timezone
    today = timezone.now().date()
    latest = ExchangeRateLog.objects.filter(
        currency='USD',
        date=today,
        source__in=['CBM', 'Scraped']
    ).order_by('-id').first()
    
    if latest and latest.id == instance.id:
        # This is the latest scraped rate, trigger sync
        try:
            with transaction.atomic():
                updated_count = sync_prices_on_rate_change(instance.rate, round_base=100)
                logger.info(
                    f'Auto-synced {updated_count} DYNAMIC_USD product prices from scraped rate: {instance.rate}'
                )
                
                # AI Price Risk Alert: Check for >1% fluctuation compared to previous day
                yesterday = today - timedelta(days=1)
                previous_rate = ExchangeRateLog.objects.filter(
                    currency='USD',
                    date=yesterday,
                    source__in=['CBM', 'Scraped']
                ).order_by('-id').first()
                
                if previous_rate:
                    rate_change_percent = abs(
                        (float(instance.rate) - float(previous_rate.rate)) / float(previous_rate.rate) * 100
                    )
                    if rate_change_percent > 1.0:
                        _create_price_risk_alert(instance.rate, previous_rate.rate, rate_change_percent)
        except Exception as e:
            logger.error(f'Failed to auto-sync prices from scraped rate: {e}', exc_info=True)


def _create_price_risk_alert(new_rate, old_rate, change_percent):
    """Create Price Risk Alert notification for Owner when rate fluctuates >1%."""
    from inventory.models import Notification
    from core.models import User, Role
    from django.utils import timezone
    
    owner_role = Role.objects.filter(name__iexact='owner').first()
    if not owner_role:
        return
    
    owners = User.objects.filter(role_obj=owner_role)
    if not owners.exists():
        return
    
    trend = 'increased' if new_rate > old_rate else 'decreased'
    trend_icon = '⚠️' if change_percent > 2.0 else '📊'
    
    message = (
        f"{trend_icon} Price Risk Alert: USD rate {trend} by {change_percent:.2f}% "
        f"({old_rate:,.2f} → {new_rate:,.2f} MMK). "
        f"Consider reviewing manual rate override to maintain profit margins."
    )
    
    for owner in owners:
        Notification.objects.create(
            recipient=owner,
            notification_type='price_risk_alert',
            message=message,
            is_read=False,
        )
    
    logger.warning(
        f'Price Risk Alert sent to {owners.count()} owner(s): {change_percent:.2f}% rate change detected'
    )
