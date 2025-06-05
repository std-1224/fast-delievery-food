import base64
import json
import random
import string
from datetime import datetime, timezone, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from django.core.management.base import BaseCommand

from apps.system.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        device_name = "Test Device 1"

        # random app_id
        characters = string.ascii_letters + string.digits
        app_id = ''.join(random.choice(characters) for _ in range(32))

        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        public_key_hex = public_key_bytes.hex()

        Device.objects.create(name=device_name, public_key=public_key_hex, app_id=app_id, is_connected=True)
        payload = {
            "device_name": device_name,
            "id": app_id,
            "valid": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace('+00:00', 'Z'),
        }

        # Sign the payload
        payload_bytes = json.dumps(payload).encode('utf-8')
        base64_payload = base64.b64encode(payload_bytes)

        signature = private_key.sign(base64_payload).hex()
        print(f'{base64_payload.decode()}.{signature}')
