"""
Celery Beat schedule configuration for periodic tasks.
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'fetch-exchange-rates-daily': {
        'task': 'inventory.fetch_exchange_rates_daily',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10:00 AM
        'options': {'timezone': 'Asia/Yangon'},
    },
}
