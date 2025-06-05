from oscar.core.loading import get_model
from rest_framework import serializers

Order = get_model('order', 'Order')


class FilterOrderSerializer(serializers.Serializer):
    by = serializers.ChoiceField(choices=['created', 'updated'], allow_null=False, allow_blank=False)
    from_date = serializers.DateTimeField(allow_null=False)
    to_date = serializers.DateTimeField(allow_null=False)
    status = serializers.ListField(required=False,
                                   child=serializers.CharField(allow_blank=False, allow_null=False))

    def validate(self, data):
        from_date = data.get('from_date')
        to_date = data.get('to_date')

        if from_date and to_date and from_date > to_date:
            raise serializers.ValidationError("from_date cannot be greater than to_date.")

        status = data.get('status')
        if status:
            data['status'] = [s.capitalize() for s in status]
        return data

    class Meta:
        model = Order
        fields = ['by', 'from_date', 'to_date', 'status']


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.all_statuses(), required=True)

    class Meta:
        model = Order
        fields = ['status']
