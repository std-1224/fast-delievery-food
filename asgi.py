import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from apps.order.consumers import OrderConsumer
from apps.system.permissions import XAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        XAuthMiddleware(
            URLRouter([
                path("ws/orders/", OrderConsumer.as_asgi()),
            ])
        )
    ),
})
