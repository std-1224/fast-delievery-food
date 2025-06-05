# pylint: disable=unbalanced-tuple-unpacking

from drf_spectacular.utils import extend_schema, OpenApiParameter
from oscar.apps.order.exceptions import InvalidOrderStatus
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes, get_api_class
from rest_framework import generics, status
from rest_framework.response import Response

from apps.custom_api.serializers.serializers import UpdateOrderStatusSerializer, FilterOrderSerializer
from apps.system.permissions import IsAuthenticatedByXAuth
from settings import ORDER_STATUSES_LOWER

APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
Order = get_model("order", "Order")
OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")

(
    AdminOrderSerializer,
    AdminOrderLineSerializer,
    AdminOrderLineAttributeSerializer,
) = get_api_classes(  # noqa
    "serializers.admin.order",
    [
        "AdminOrderSerializer",
        "AdminOrderLineSerializer",
        "AdminOrderLineAttributeSerializer",
    ],
)


class OrderAdminList(generics.ListAPIView):
    serializer_class = AdminOrderSerializer
    queryset = Order.objects.get_queryset()
    permission_classes = (APIAdminPermission | IsAuthenticatedByXAuth,)

    def get_queryset(self):
        status_query = self.request.query_params.get("status", "")
        query_params = {
            "from_date": self.request.query_params.get("from"),
            "to_date": self.request.query_params.get("to"),
            "by": self.request.query_params.get("by"),
            "status": status_query.split(",") if status_query else []
        }
        serializer = FilterOrderSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        from_date = serializer.validated_data.get("from_date")
        to_date = serializer.validated_data.get("to_date")
        by = serializer.validated_data.get("by")
        status = serializer.validated_data.get("status")

        condition = {
            f"{by}__range": (from_date, to_date)
        }

        if status:
            condition.update({'status__in': status})

        return super().get_queryset().filter(**condition)

    @extend_schema(
        parameters=[
            OpenApiParameter("from", str,
                             description="Start date for the range filter in ISO format.",
                             required=True),
            OpenApiParameter("to", str,
                             description="End date for the range filter in ISO format",
                             required=True),
            OpenApiParameter('by', str, required=True, enum=['created', 'updated']),
            OpenApiParameter('status', str,
                             many=True,
                             explode=False,
                             description="Filter by order status (case-insensitive)",
                             required=False, enum=ORDER_STATUSES_LOWER),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderAdminDetail(generics.RetrieveDestroyAPIView):
    serializer_class = AdminOrderSerializer
    queryset = Order.objects.get_queryset()
    permission_classes = (APIAdminPermission | IsAuthenticatedByXAuth,)


class OrderLineAdminList(generics.ListAPIView):
    serializer_class = AdminOrderLineSerializer
    queryset = OrderLine.objects.get_queryset()
    permission_classes = (APIAdminPermission | IsAuthenticatedByXAuth,)

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        return super().get_queryset().filter(order_id=pk)


class OrderLineAdminDetail(generics.RetrieveDestroyAPIView):
    serializer_class = AdminOrderLineSerializer
    queryset = OrderLine.objects.get_queryset()
    permission_classes = (APIAdminPermission | IsAuthenticatedByXAuth,)


class OrderLineAttributeAdminDetail(generics.RetrieveDestroyAPIView):
    serializer_class = AdminOrderLineAttributeSerializer
    queryset = OrderLineAttribute.objects.get_queryset()
    permission_classes = (APIAdminPermission | IsAuthenticatedByXAuth,)


class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    permission_classes = [APIAdminPermission | IsAuthenticatedByXAuth]
    serializer_class = UpdateOrderStatusSerializer

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_status = serializer.validated_data["status"]
            order.set_status(new_status)
        except InvalidOrderStatus as ex:
            return Response(
                {"message": str(ex)}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer_context = self.get_serializer_context()
        result = AdminOrderSerializer(order, context=serializer_context).data
        return Response(result, status=status.HTTP_200_OK)


class AllowedOrderStatusView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    permission_classes = [APIAdminPermission | IsAuthenticatedByXAuth]

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        return Response(order.available_statuses())


class OrderIdsAdminList(OrderAdminList):

    @extend_schema(
        parameters=[
            OpenApiParameter("from", str,
                             description="Start date for the range filter in ISO format.",
                             required=True),
            OpenApiParameter("to", str,
                             description="End date for the range filter in ISO format",
                             required=True),
            OpenApiParameter('by', str, required=True, enum=['created', 'updated']),
            OpenApiParameter('status', str,
                             many=True,
                             explode=False,
                             description="Filter by order status (case-insensitive)",
                             required=False, enum=ORDER_STATUSES_LOWER),
        ],
        responses={200: {"type": "integer"}},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response(queryset.values_list("id", flat=True))


class TestConnectionView(generics.GenericAPIView):
    permission_classes = [APIAdminPermission | IsAuthenticatedByXAuth]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Connection successful"}, status=status.HTTP_200_OK)
