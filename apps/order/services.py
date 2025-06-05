import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from oscarapi.utils.loading import get_api_class

from apps.core.firebase import FirebaseService
from apps.order.constants import OrderWebsocketEvent
from apps.order.consumers import ORDER_UPDATES_GROUP
from apps.order.serializers import OrderPlacedSerializer
from apps.system.models import Device

AdminOrderSerializer = get_api_class("serializers.admin.order", "AdminOrderSerializer")
logger = logging.getLogger(__name__)


def send_order_websocket_event(order, event_type: OrderWebsocketEvent):
    logging.info('send_order_changed_websocket_event')

    data = AdminOrderSerializer(order, context={'request': None}).data

    channel_layer = get_channel_layer()
    event = {
        'type': 'send_order_event',
        'message': {
            'event': event_type.value,
            'data': data
        }
    }

    logging.info(event)
    async_to_sync(channel_layer.group_send)(ORDER_UPDATES_GROUP, event)


def send_order_status_changed_notification(order, old_status, new_status):
    send_order_websocket_event(order, OrderWebsocketEvent.UPDATED)
    firebase_service = FirebaseService()
    device_keys = Device.objects.filter(firebase_token__isnull=False).exclude(firebase_token__exact='').values_list(
        'firebase_token', flat=True)

    if not device_keys:
        return

    data = {
        "orderId": order.pk,
        "status": new_status,
        "prevStatus": old_status,
        "timestamp": order.updated.timestamp()
    }

    firebase_service.multicast_notification(
        device_keys=list(device_keys),
        title="Order status changed",
        body=f"#{order.number} status changed from {old_status} to {new_status}",
        data={
            "orderUpdate": json.dumps(data),
        }
    )


def send_order_placed_notification(order):
    send_order_websocket_event(order, OrderWebsocketEvent.CREATED)
    firebase_service = FirebaseService()
    device_keys = Device.objects.filter(firebase_token__isnull=False).exclude(firebase_token__exact='').values_list(
        'firebase_token', flat=True)

    if not device_keys:
        return

    data = OrderPlacedSerializer(order, context={'request': None}).data
    firebase_service.multicast_notification(
        device_keys=list(device_keys),
        title="New order placed",
        body=f"#{order.number} has been placed",
        data={
            "order": json.dumps(data),
        }
    )
