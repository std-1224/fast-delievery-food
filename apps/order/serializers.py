from oscarapi.utils.loading import get_api_class

AdminOrderSerializer = get_api_class("serializers.admin.order", "AdminOrderSerializer")


class OrderPlacedSerializer(AdminOrderSerializer):
    class Meta(AdminOrderSerializer.Meta):
        fields = (
            "id",
            "number",
            "status",
            "email",
            "total_incl_tax",
            "currency",
            "shipping_address",
            "shipping_method",
            "shipping_code",
            "payment_method",
            "date_placed",
            "updated",
            "created",
            "payment_method",
            "receiving_datetime",
            "is_paid",
        )
