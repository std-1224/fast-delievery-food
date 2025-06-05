import json

import requests
from django.core.management import BaseCommand

from settings import WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_TOKEN


class Command(BaseCommand):
    def handle(self, *args, **options):
        # send_mail(
        #     "Subject here",
        #     "Here is the message.",
        #     OSCAR_FROM_EMAIL,
        #     ["user1_nyaff@mailinator.com"],
        #     fail_silently=False,
        # )
        message = {
            "messaging_product": "whatsapp",
            "to": '+84969442975',
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
                                "text": f"100290"
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
                                "text": 'en/accounts/order-status/100290/100290:EoTl5MqWpmcDsYVdKu2DBT5hjWS2p5tJJgXUqnjLUI0/'
                            }
                        ]
                    }
                ]
            }
        }
        response = requests.post(f'https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages',
                                 data=json.dumps(message),
                                 headers={
                                     'Authorization': f'Bearer {WHATSAPP_TOKEN}',
                                     'Content-Type': 'application/json',
                                 })
