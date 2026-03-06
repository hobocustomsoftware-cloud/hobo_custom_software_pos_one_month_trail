"""
Signals for Installation module
- Auto-create Installation Job (ticket) when Sale is approved and contains Solar/Machine bundle or installation product
- Installation No. (INST-YYMMDD-0001) က model save() မှာ အလိုအလျောက် ထုတ်ပြီးသား
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from inventory.models import SaleTransaction, SaleItem
from .models import InstallationJob


@receiver(post_save, sender=SaleTransaction)
def create_installation_job_on_sale(sender, instance, created, **kwargs):
    """
    အလိုအလျောက် Installation ticket ဖန်တီးမှု:
    - Sale approved ဖြစ်ပြီး ထို sale မှာ Solar/Machine bundle သို့မဟုတ် တပ်ဆင်လိုသော ပစ္စည်းပါရင်
    - ထို sale အတွက် Installation Job တစ်ခု မရှိရင် ဖန်တီးမယ်
    - installation_no (INST-YYMMDD-0001) က model save() မှာ အလိုအလျောက် ထုတ်ပါတယ်
    """
    if instance.status != 'approved':
        return
    if InstallationJob.objects.filter(sale_transaction=instance).exists():
        return

    sale_items = SaleItem.objects.filter(sale_transaction=instance)
    requires_installation = False

    for sale_item in sale_items:
        product = sale_item.product
        bundle_items = getattr(product, 'bundle_items', None)
        if bundle_items and bundle_items.exists():
            for bundle_item in bundle_items.all():
                bundle = getattr(bundle_item, 'bundle', None)
                if bundle and getattr(bundle, 'bundle_type', None) in ['Solar', 'Machine']:
                    requires_installation = True
                    break
        if product.name and any(k in (product.name or '').lower() for k in ['solar', 'inverter', 'battery', 'panel', 'machine']):
            requires_installation = True

    if not requires_installation:
        return

    customer = getattr(instance, 'customer', None)
    default_address = (customer.address if customer and getattr(customer, 'address', None) else None) or 'လိပ်စာ ထည့်သွင်းရန်'
    default_date = (timezone.now() + timedelta(days=3)).date()

    try:
        InstallationJob.objects.create(
            sale_transaction=instance,
            customer=customer,
            installation_address=default_address,
            installation_date=default_date,
            created_by=None,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('Auto-create installation job failed for sale %s: %s', instance.id, e)


from .models import InstallationStatusHistory


@receiver(post_save, sender='installation.InstallationJob')
def create_status_history(sender, instance, created, **kwargs):
    """
    Auto-create status history when installation job is created
    """
    if created:
        InstallationStatusHistory.objects.create(
            installation_job=instance,
            old_status='',
            new_status='pending',
            updated_by=instance.created_by
        )
