from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

ORDER_UPDATES_GROUP = "order_updates"


class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"] or isinstance(self.scope["user"], AnonymousUser):
            await self.close()
        await self.channel_layer.group_add(ORDER_UPDATES_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(ORDER_UPDATES_GROUP, self.channel_name)

    async def send_order_event(self, event):
        await self.send_json({
            'message': event['message']
        })
