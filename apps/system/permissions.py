import base64
import json
from datetime import timezone, datetime

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from apps.system.exceptions import TokenExpiredException
from apps.system.models import Device


class IsAuthenticatedByXAuth(BasePermission):
    """
    Custom permission to allow access only to authenticated users based on the X-Auth header.
    This method follows the approach used in the old system written in PHP.
    We should reuse this method to ensure compatibility between the new system and the existing mobile app.
    """

    def has_permission(self, request, view):
        x_auth_token = request.headers.get('X-Auth')

        if not x_auth_token:
            raise AuthenticationFailed('X-Auth header is missing.')

        try:
            request.device = self.verify_access_token(x_auth_token)
            return True
        except TokenExpiredException as e:
            raise AuthenticationFailed(str(e))
        except InvalidSignature:
            raise AuthenticationFailed('Invalid signature.')
        except Exception:
            raise AuthenticationFailed('Invalid X-Auth token.')

    @staticmethod
    def verify_access_token(token: str):
        # Split the token into payload and signature parts
        encoded_payload, signature = token.split('.')

        # Decode the Base64-encoded payload
        payload_bytes = base64.b64decode(encoded_payload)

        # Parse the payload (assuming it is in JSON format)
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Check token expiration
        valid_until = payload.get('valid')
        if valid_until:
            expiration_date = datetime.fromisoformat(valid_until[:-1]).replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expiration_date:
                raise TokenExpiredException('Token has expired.')

        app_id = payload.get('id')
        device = Device.objects.get(app_id=app_id, is_connected=True)
        signature_bytes = bytes.fromhex(signature)

        #  Convert the hexadecimal public key to bytes
        public_key_bytes = bytes.fromhex(device.public_key)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

        # Verify the signature (signature is applied on the encoded payload)
        public_key.verify(signature_bytes, encoded_payload.encode('utf-8'))
        return payload


@database_sync_to_async
def verify_token(token_key):
    try:
        device = IsAuthenticatedByXAuth.verify_access_token(token_key)
        return device
    except TokenExpiredException as e:
        raise AuthenticationFailed(str(e))
    except InvalidSignature:
        raise AuthenticationFailed('Invalid signature.')
    except Exception as e:
        raise AuthenticationFailed('Invalid X-Auth token.')


class XAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        token = None
        if "headers" in scope:
            token = dict(scope["headers"]).get(b'x-auth', None)
        scope['user'] = AnonymousUser() if token is None else await verify_token(token.decode('utf-8'))
        return await super().__call__(scope, receive, send)
