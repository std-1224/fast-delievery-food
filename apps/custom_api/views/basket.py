from oscar.apps.basket import signals
from oscarapi.basket import operations
from oscarapi.views import basket
from rest_framework import status
from rest_framework.response import Response


class AddProductView(basket.AddProductView):
    """
    Add a certain quantity of a product to the basket.

    POST(url, quantity)
    {
        "product_id": 209,
        "quantity": 6
    }

    If you've got some options to configure for the product to add to the
    basket, you should pass the optional ``options`` property:
    {
        "product_id": "209",
        "quantity": 6,
        "options": [{
            "option": 1,
            "value": "some value"
        }]
    }
    """

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        p_ser = self.add_product_serializer_class(
            data=request.data, context={"request": request}
        )
        if p_ser.is_valid():
            basket = operations.get_basket(request)
            product = p_ser.validated_data["product_id"]
            quantity = p_ser.validated_data["quantity"]
            options = p_ser.validated_data.get("options", [])

            basket_valid, message = self.validate(basket, product, quantity, options)
            if not basket_valid:
                return Response(
                    {"reason": message}, status=status.HTTP_406_NOT_ACCEPTABLE
                )

            basket.add_product(product, quantity=quantity, options=options)

            signals.basket_addition.send(
                sender=self, product=product, user=request.user, request=request
            )

            operations.apply_offers(request, basket)
            ser = self.serializer_class(basket, context={"request": request})
            return Response(ser.data)

        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)