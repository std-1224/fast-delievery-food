from oscar.apps.catalogue.models import ProductImage
from oscar.apps.partner.models import StockRecord
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from apps.catalogue.models import Product, Option, AttributeOption


class StockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord
        fields = (
            "id", "partner_sku", "price_currency", "price", "num_in_stock", "num_allocated", "low_stock_threshold",
            "date_created", "date_updated", "product", "partner")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "original", "caption", "display_order", "date_created", "product")


class ProductSerializer(serializers.ModelSerializer):
    stock_record = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "structure", "is_public", "upc", "title", "slug", "description", "meta_title", "meta_description",
            "rating", "date_created", "date_updated", "is_discountable", "parent", "product_class", "attributes",
            "product_options", "recommended_products", "categories", "stock_record", "product_image")

    def get_stock_record(self, obj):
        stock_record = StockRecord.objects.filter(product=obj)
        data = StockRecordSerializer(stock_record, many=True).data
        return data

    def get_product_image(self, obj):
        product_image = ProductImage.objects.filter(product=obj)
        data = ProductImageSerializer(product_image, many=True).data
        return data


class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ("id", "option", "price", "key", "group")


class OptionSerializer(serializers.ModelSerializer):
    option_attr = SerializerMethodField()

    class Meta:
        model = Option
        fields = ("id", "name", "code", "type", "required", "help_text", "order", "option_group", "option_attr")

    def get_option_attr(self, obj):
        if obj.option_group:
            attr = AttributeOption.objects.filter(group=obj.option_group)
            data = AttributeOptionSerializer(attr, many=True).data
            return data
