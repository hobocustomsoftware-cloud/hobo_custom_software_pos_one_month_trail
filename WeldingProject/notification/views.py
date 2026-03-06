# inventory/views.py (AdminApprovalView ၏ perform_update method အတွင်း)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from inventory.serializers import NotificationSerializer # အဆင့် ၄ မှ NotificationSerializer
from django.db import transaction
from inventory.models import Notification

def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save(...)
            
            # ... (Approved Logic) ...

            if instance.status in ['approved', 'rejected']:
                # 1. Notification Object ကို DB တွင် ဖန်တီးသည်
                notification_obj = Notification.objects.create(
                    recipient=instance.staff, 
                    message=f"Sale Request #{instance.id} has been {instance.status.upper()}.",
                    notification_type=f'sale_{instance.status}',
                    sale_transaction=instance
                )
                
                # 2. Realtime Push အတွက် Data ကို Serialized လုပ်သည်
                notification_data = NotificationSerializer(notification_obj).data
                
                # 3. Channels Layer မှတဆင့် Group သို့ ပေးပို့သည်
                channel_layer = get_channel_layer()
                staff_user_id = str(instance.staff.id)
                
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{staff_user_id}', 
                    {
                        'type': 'send_notification', # Consumer method name (send_notification)
                        'message': notification_data
                    }
                )
            
            # ... (Return Logic)
            return instance