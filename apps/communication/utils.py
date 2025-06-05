import json

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from oscar.apps.communication.utils import Dispatcher as BaseDispatcher

from apps.system.services import get_core_config
from settings import WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID


class Dispatcher(BaseDispatcher):
    def dispatch_anonymous_messages(self, email, messages, attachments=None):
        dispatched_messages = {}
        if email:
            dispatched_messages["email"] = (
                self.send_email_messages(email, messages, attachments=attachments),
                None,
            )
        return dispatched_messages

    def dispatch_anonymous_whatsapp_messages(self, phone_number, messages, order):
        dispatched_messages = {}
        path = reverse(
            "customer:anon-order",
            kwargs={
                "order_number": order.number,
                "hash": order.verification_hash(),
            },
        )
        if phone_number:
            message = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": "order_confirmed_1",
                    "language": {
                        "code": "en_US"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": f"{order.number}"
                                }
                            ]
                        },
                        {
                            "type": "button",
                            "sub_type": "url",
                            "index": "0",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": str(path[1:])
                                }
                            ]
                        }
                    ]
                }
            }
            dispatched_messages["whatsapp"] = (
                self.send_whatsapp_message(message),
                None,
            )
        return dispatched_messages

    def send_whatsapp_message(self, message):
        response = requests.post(f'https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages',
                                 data=json.dumps(message),
                                 headers={
                                     'Authorization': f'Bearer {WHATSAPP_TOKEN}',
                                     'Content-Type': 'application/json',
                                 })
        return 'message'

    def send_email_messages_to_admin(self, order):
        """
        Send email to recipient, HTML attachment optional.
        """

        admin_emails = get_core_config().notification_admin_emails
        if not admin_emails:
            return

        admin_emails = admin_emails.split(',')
        # Prepare email content
        subject = 'New Order Placed'
        ctx = {
            "static_base_url": getattr(settings, "OSCAR_STATIC_BASE_URL", None),
            "order": order,
            "lines": order.lines.all(),
        }

        html_message = render_to_string('email/order_notification.html', ctx)
        plain_message = strip_tags(html_message)

        # Send email
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.OSCAR_FROM_EMAIL,
            admin_emails,
        )
        email.attach_alternative(html_message, "text/html")

        self.logger.info("Sending email to %s", admin_emails)

        if self.mail_connection:
            self.mail_connection.send_messages([email])
        else:
            email.send()
        return email
