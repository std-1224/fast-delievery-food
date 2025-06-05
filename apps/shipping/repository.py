from oscar.apps.shipping import repository
from . import methods
from .models import Postcode


class Repository(repository.Repository):

    def get_available_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        shipping_methods = [methods.SelfCollection()]
        if not shipping_addr:
            return shipping_methods
        postcode = shipping_addr.postcode.replace(" ", "").upper()
        shipping_rate = self._get_shipping_rate(postcode)
        if shipping_rate is not None:
            shipping_methods.append(methods.Standard(shipping_addr))
        return shipping_methods

    def _get_shipping_rate(self, postcode):
      try:
        return Postcode.objects.get(code=postcode).shipping_zone.shipping_price
      except Postcode.DoesNotExist:
        return None