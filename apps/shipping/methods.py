from decimal import Decimal as D

from oscar.apps.shipping import methods
from oscar.core import prices

from apps.shipping.models import Postcode


class Standard(methods.Base):
    code = 'delivery'
    name = 'Delivery'
    shipping_address = None

    def __init__(self, shipping_address):
        self.shipping_address = shipping_address
        if not shipping_address:
            self.name = 'Shipping price will be calculated after you enter your address.'

    def calculate(self, basket):
        if not self.shipping_address:
            return prices.Price(currency=basket.currency, excl_tax=D("0.00"), tax=D("0.00"))

        postcode = self.shipping_address.postcode.replace(" ", "").upper()
        shipping_rate = self._get_shipping_rate(postcode)
        return prices.Price(currency=basket.currency,
                            excl_tax=shipping_rate, incl_tax=shipping_rate)

    def _get_shipping_rate(self, postcode):
        return Postcode.objects.get(code=postcode).shipping_zone.shipping_price


class SelfCollection(methods.Free):
    code = 'self-collection'
    name = 'Self Collection'
