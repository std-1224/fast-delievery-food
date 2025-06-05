from oscar.apps.partner.models import StockRecord
from oscar.core.loading import get_class
from oscarapi.serializers import product
from oscarapi.serializers.product import ProductImage
from rest_framework import serializers

from apps.catalogue.models import Product, Option, AttributeOption, AttributeOptionGroup

Selector = get_class("partner.strategy", "Selector")


class StockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord
        fields = (
            "id", "partner_sku", "price_currency", "price", "num_in_stock", "num_allocated",
            "date_created", "date_updated", "product")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "original", "caption", "display_order")


class AttributeOptionSerializer(product.OscarModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ('id', 'option', 'price', 'key')


class AttributeOptionGroupSerializer(product.OscarModelSerializer):
    options = AttributeOptionSerializer(many=True)

    class Meta:
        model = AttributeOptionGroup
        fields = ('name', 'options', 'id')


class OptionSerializer(product.OscarModelSerializer):
    option_group = AttributeOptionGroupSerializer()

    class Meta:
        model = Option
        fields = ('name', 'code', 'required', 'type', 'order', 'help_text', 'id', 'option_group')


class ChildProductSerializer(product.ProductSerializer):
    "Serializer for child products"
    stockrecords = StockRecordSerializer(many=True)
    options = OptionSerializer(many=True, required=False)
    # the below fields can be filled from the parent product if enabled.
    images = ProductImageSerializer(many=True, required=False, source="parent.images")
    description = serializers.CharField(source="parent.description")

    class Meta:
        model = Product
        fields = (
            "id", "structure", "is_public", "upc", "title", "slug", "description", "meta_title", "meta_description",
            "rating", "date_created", "date_updated", "is_discountable", "product_class", "attributes",
            "options", "recommended_products", "categories", 'stockrecords', 'availability')


class ProductLinkSerializer(product.ProductLinkSerializer):
    stockrecords = StockRecordSerializer(many=True)
    primary_image = ProductImageSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "structure", "is_public", "upc", "title", "slug", "description", "meta_title", "meta_description",
            "rating", "date_created", "date_updated", "is_discountable", "product_class", "attributes",
            "categories", 'stockrecords', 'primary_image')


class ProductSerializer(product.ProductSerializer):
    stockrecords = StockRecordSerializer(many=True)
    options = OptionSerializer(many=True, required=False)
    primary_image = ProductImageSerializer(read_only=True)
    children = ChildProductSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id", "structure", "is_public", "upc", "title", "slug", "description", "meta_title", "meta_description",
            "rating", "date_created", "date_updated", "is_discountable", "parent", "product_class", "attributes",
            "options", "recommended_products", "categories", 'stockrecords', 'availability', 'primary_image',
            'children')


class OptionValueSerializer(serializers.Serializer):
    option = serializers.PrimaryKeyRelatedField(queryset=Option.objects)
    value = serializers.JSONField()


class AddProductSerializer(serializers.Serializer):
    """
    Serializes and validates an add to basket request.
    """

    quantity = serializers.IntegerField(required=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects, required=True)
    options = OptionValueSerializer(many=True, required=False)
