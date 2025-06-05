import firebase_admin
from firebase_admin import credentials, messaging

from apps.system.services import get_core_config


class FirebaseService:
    def __init__(self):
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            core_config = get_core_config()
            if core_config.firebase_service_account:
                print(core_config.firebase_service_account.path)
                cred = credentials.Certificate(core_config.firebase_service_account.path)
                firebase_admin.initialize_app(cred)

    def send_notification(self, device_key, title, body, data=None):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_key,
            data=data or {}
        )

        # Send the message
        try:
            response = messaging.send(message)
            print(f'Successfully sent message: {response}')
        except Exception as e:
            print(f'Error sending message: {e}')

    def multicast_notification(self, device_keys, title="", body="", data=None):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=device_keys,
            data=data or {}
        )
        try:
            response = messaging.send_each_for_multicast(message)
            print(f'Successfully sent message: {response}')
            print(f'Count of messages sent: {response.success_count}')
        except Exception as e:
            print(f'Error sending message: {e}')
