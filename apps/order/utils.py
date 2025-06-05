import logging

from oscar.apps.order.utils import OrderDispatcher as BaseOrderDispatcher, CommunicationEventType

logger = logging.getLogger(__name__)


class OrderDispatcher(BaseOrderDispatcher):
    def dispatch_order_messages(
            self, order, messages, event_code, attachments=None, **kwargs
    ):
        """
        Dispatch order-related messages to the customer.
        """
        self.dispatcher.logger.info(
            "Order #%s - sending %s messages", order.number, event_code
        )
        dispatched_messages = None
        try:
            if order.is_anonymous:
                email = kwargs.get("email_address", order.guest_email)
                phone_number = kwargs.get("phone_number", order.guest_phone_number)
                if phone_number:
                    dispatched_messages = self.dispatcher.dispatch_anonymous_whatsapp_messages(phone_number, messages,
                                                                                               order)
                else:
                    dispatched_messages = self.dispatcher.dispatch_anonymous_messages(
                        email, messages, attachments
                    )
            else:
                dispatched_messages = self.dispatcher.dispatch_user_messages(
                    order.user, messages, attachments
                )

            self.dispatcher.send_email_messages_to_admin(order)
        except Exception as ex:
            logger.error(ex)

        try:
            event_type = CommunicationEventType.objects.get(code=event_code)
        except CommunicationEventType.DoesNotExist:
            event_type = None

        self.create_communication_event(order, event_type, dispatched_messages)
