from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from core.models import User

@database_sync_to_async
def get_user(token_key):
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        # အပြောင်းအလဲ- select_related('role_obj') ထည့်လိုက်ခြင်းဖြင့် Role data ပါ တစ်ခါတည်းပါလာမည်
        return User.objects.select_related('role_obj').get(id=user_id)
    except Exception:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # WebSocket URL မှ token=xxx ကို ရှာခြင်း
        query_string = scope.get('query_string', b'').decode()
        token_key = None
        
        # URL parameters များကို ပိုမိုတိကျစွာ parse လုပ်ခြင်း
        if 'token=' in query_string:
            # ဥပမာ- ?token=abc&other=123 ဖြစ်နေလျှင် split လုပ်ရန်
            params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
            token_key = params.get('token')
        
        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()
            
        return await self.inner(scope, receive, send)