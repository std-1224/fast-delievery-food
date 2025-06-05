from rest_framework import serializers

from apps.system.models import SystemConfig, Menu, Slider, Device


class SellerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ('site_name', 'logo', 'business_logo',)


class SystemSerializer(serializers.ModelSerializer):
    favicon = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SystemConfig
        fields = "__all__"

    def get_favicon(self, obj):
        return f"/media/{obj.favicon}" if obj.favicon else ""

    def get_logo(self, obj):
        return f"/media/{obj.logo}" if obj.logo else ""


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = "__all__"


class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = "__all__"


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'name', 'app_id', 'public_key', 'is_connected')


class SetDeviceKeySerializer(serializers.Serializer):
    public_key = serializers.CharField(max_length=255, required=True)
    app_id = serializers.CharField(max_length=255, required=True)


class UpdateFirebaseTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, required=True)
    device_id = serializers.CharField(max_length=255, required=True)
