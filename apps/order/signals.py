from threading import Thread

from django.dispatch import receiver
from oscar.apps.order.signals import order_status_changed, order_placed

from apps.order.services import send_order_status_changed_notification, send_order_placed_notification


@receiver(order_status_changed)
def order_status_changed(sender, order, old_status, new_status, **kwargs):
    Thread(target=send_order_status_changed_notification, args=(order, old_status, new_status)).start()


@receiver(order_placed)
def order_placed(sender, order, **kwargs):
    Thread(target=send_order_placed_notification, args=(order,)).start()
