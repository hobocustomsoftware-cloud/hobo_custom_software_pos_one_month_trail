"""
Celery tasks for background jobs (Exchange Rate Fetching, etc.)
Requires: celery, redis
Install: pip install celery redis
"""
from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task(name='inventory.fetch_exchange_rates_daily')
def fetch_exchange_rates_daily():
    """
    Daily task to fetch exchange rates from CBM API.
    Scheduled to run at 10:00 AM daily.
    """
    try:
        logger.info('Starting daily exchange rate fetch...')
        call_command('fetch_exchange_rates')
        logger.info('Exchange rate fetch completed successfully')
        return {'status': 'success', 'message': 'Exchange rates fetched successfully'}
    except Exception as e:
        logger.error(f'Exchange rate fetch failed: {e}', exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(name='inventory.fetch_exchange_rates_now')
def fetch_exchange_rates_now():
    """
    Manual trigger for exchange rate fetch (can be called from admin or API).
    """
    return fetch_exchange_rates_daily()
