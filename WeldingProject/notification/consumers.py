# notifications/consumers.py (notifications app folder ထဲတွင် ဖန်တီးပါ)

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        # User သည် Authenticated ဖြစ်မှသာ ဆက်လက်လုပ်ဆောင်ပါ
        if self.user.is_anonymous:
            await self.close()
            return
            
        self.user_id = str(self.scope["user"].id)
        # Group name ကို user_id ဖြင့် သီးခြားခွဲခြားသည် (notifications_1, notifications_2,...)
        self.notification_group_name = f'notifications_{self.user_id}'

        # Group သို့ join ဝင်ပါ
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Group မှ ထွက်ပါ
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    # Group မှ မက်ဆေ့ချ်လက်ခံသောအခါ Frontend သို့ ပေးပို့ရန်
    async def send_notification(self, event):
        message = event['message']
        
        # JSON format ဖြင့် Frontend သို့ ပို့ပါ
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': message
        }))