from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class
from rest_framework import serializers

from settings import PAYMENT_METHOD_CASH

OrderSerializer = get_api_class("serializers.checkout", "OrderSerializer")
AdminUserSerializer = get_api_class("serializers.admin.user", "AdminUserSerializer")
ProductSerializer = get_api_class("serializers.product", "ProductSerializer")
LineAttributeSerializer = get_api_class("serializers.basket", "LineAttributeSerializer")
Line = get_model("order", "Line")


class OrderLineSerializer(serializers.ModelSerializer):
    # Product info
    categories = serializers.SerializerMethodField(read_only=True)
    # Price
    price_currency = serializers.CharField(source="order.currency", max_length=12)
    price_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_excl_tax"
    )
    price_incl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_incl_tax"
    )
    price_incl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_before_discounts_incl_tax"
    )
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_before_discounts_excl_tax"
    )
    # Attributes
    attributes = LineAttributeSerializer(
        many=True, required=False, read_only=True
    )

    def get_categories(self, obj):
        if obj.product is None:
            return []
        return list(obj.product.categories.all().values_list("name", flat=True))

    class Meta:
        model = Line
        fields = (
            "id",
            "quantity",
            "categories",
            "attributes",
            "title",
            "upc",
            "partner_sku",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
            "price_incl_tax_excl_discounts",
            "price_excl_tax_excl_discounts",
        )


class AdminOrderSerializer(OrderSerializer):
    owner = AdminUserSerializer(read_only=True, source="user")
    lines = OrderLineSerializer(many=True, read_only=True)
    payment_method = serializers.SerializerMethodField(read_only=True)
    receiving_datetime = serializers.DateTimeField(source="date_placed", read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ("is_paid", "payment_method", "receiving_datetime")

    def get_payment_method(self, obj):
        payment_source = obj.sources.first()
        if payment_source is None:
            return PAYMENT_METHOD_CASH
        return payment_source.source_type.name
