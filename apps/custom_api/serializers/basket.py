from oscar.core.loading import get_model
from oscarapi.serializers import basket
from rest_framework import serializers

from apps.custom_api.serializers.product import ProductSerializer, StockRecordSerializer

LineAttribute = get_model("basket", "LineAttribute")


class LineAttributeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='option.name')
    is_multi_option = serializers.BooleanField(source='option.is_multi_option')

    class Meta:
        model = LineAttribute
        fields = ('name', 'value', 'is_multi_option')


class BasketLineSerializer(basket.BasketLineSerializer):
    product = ProductSerializer(fields=('id', 'title', 'upc', 'primary_image'))
    stockrecord = StockRecordSerializer()
    attributes = LineAttributeSerializer(
        many=True, required=False, read_only=True
    )


class BasketSerializer(basket.BasketSerializer):
    lines = BasketLineSerializer(many=True)
