import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WeldingProject.settings')
django.setup() # ဒါကို အပေါ်ဆုံးမှာ ထည့်ပေးထားပါ

from channels.routing import ProtocolTypeRouter, URLRouter
from notification.middleware import JWTAuthMiddleware
from notification.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})