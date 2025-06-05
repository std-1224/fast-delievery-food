import base64
import json
import logging
from io import BytesIO

import qrcode
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.system.models import Device
from apps.system.permissions import IsAuthenticatedByXAuth
from apps.system.serializers import DeviceSerializer, \
    SetDeviceKeySerializer, UpdateFirebaseTokenSerializer, SellerInfoSerializer
from apps.system.services import get_system_config

logger = logging.getLogger(__name__)


class ScheduleConfigView(TemplateView):
    template_name = 'system/schedule.html'

    extra_context = {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "period_types": ["Collection", "Delivery", "Open", "Ordering", ]
    }


class LinkDeviceView(TemplateView):
    template_name = 'system/link-device.html'

    extra_context = {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "period_types": ["Collection", "Delivery", "Open", "Ordering", ]
    }


class CreateDeviceView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Device.objects.filter(is_connected=True)
    serializer_class = DeviceSerializer

    def create(self, request, *args, **kwargs):
        device = Device.objects.create()
        system_config = get_system_config()
        domain = request.META.get('HTTP_ORIGIN')
        ws_endpoint = domain.replace('http', 'ws')
        data = {
            "domain": domain,
            "seller_name": system_config.site_name,
            "connect_endpoint": f"{domain}/api/devices/{device.id}/device-key/",
            "websocket_endpoint": f"{ws_endpoint}/ws/orders/",
        }

        logger.info(f"Create device with data: {data}")
        json_data = json.dumps(data)

        img = qrcode.make(data=json_data, version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,
                          border=4)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Return the API key and base64 QR code
        return Response({
            'id': device.id,
            'qr_code_base64': f'data:image/png;base64,{img_base64}'
        })


class CreateDeviceNoCameraView(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DeviceSerializer

    def perform_create(self, serializer):
        app_id = serializer.validated_data['app_id']
        exists = Device.objects.filter(app_id=app_id, is_connected=True).exists()
        if exists:
            raise ValidationError("Device with this appId already connected", code="device_already_connected")

        serializer.validated_data['is_connected'] = True
        serializer.save()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class SetDeviceKeyView(generics.UpdateAPIView):
    queryset = Device.objects.filter(is_connected=False,
                                     public_key__isnull=True,
                                     app_id__isnull=True,
                                     name__isnull=True)
    serializer_class = SetDeviceKeySerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = self.get_object()
        device.public_key = serializer.validated_data['public_key']
        device.app_id = serializer.validated_data['app_id']
        device.name = request.META['HTTP_USER_AGENT'] or 'Unknown'
        device.save()

        return Response()


class RetrieveDestroyDeviceView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer


class ApproveDeviceView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Device.objects.filter(is_connected=False)
    serializer_class = DeviceSerializer

    def update(self, request, *args, **kwargs):
        device = self.get_object()
        device.is_connected = True
        device.save()

        # Remove all other devices that have the same app_id
        Device.objects.filter(app_id=device.app_id).exclude(id=device.id).delete()

        return Response()


class SellerInfoView(APIView):
    permission_classes = [IsAdminUser | IsAuthenticatedByXAuth]

    def get(self, request):
        setting = SellerInfoSerializer(get_system_config(), context={'request': request})
        return Response(setting.data)


class UpdateFirebaseTokenView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser | IsAuthenticatedByXAuth]
    serializer_class = UpdateFirebaseTokenSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id = serializer.validated_data['device_id']
        if request.device.get('id') != device_id:
            raise ValidationError("device_id in payload is not match with device id in auth token")
        instance = get_object_or_404(Device, app_id=device_id)
        instance.firebase_token = serializer.validated_data['token']
        instance.save()

        return Response()
