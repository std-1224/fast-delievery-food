from oscar.apps.basket.views import BasketAddView
from rest_framework.generics import ListAPIView


from apps.basket.models import Basket, Line


class CustomBasketAddView(BasketAddView):
    pass
