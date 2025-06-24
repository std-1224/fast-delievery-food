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

        # Extract actual postcode from full address string if needed
        postcode = self._extract_postcode(self.shipping_address.postcode)
        shipping_rate = self._get_shipping_rate(postcode)
        return prices.Price(currency=basket.currency,
                            excl_tax=shipping_rate, incl_tax=shipping_rate)

    def _extract_postcode(self, postcode_field):
        """
        Extract actual postcode from potentially long address string
        """
        if not postcode_field:
            return ""

        # If it contains commas, it's likely a full address - try to extract the actual postcode
        if "," in postcode_field:
            # Look for UK postcode pattern at the end
            import re
            # UK postcode pattern: letters/numbers followed by space and letters/numbers
            uk_postcode_pattern = r'[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}'
            match = re.search(uk_postcode_pattern, postcode_field.upper())
            if match:
                return match.group().replace(" ", "").upper()

            # If no UK postcode found, try to get the first part before the first comma
            first_part = postcode_field.split(",")[0].strip()
            return first_part.replace(" ", "").upper()

        # Otherwise, treat as regular postcode
        return postcode_field.replace(" ", "").upper()

    def _get_shipping_rate(self, postcode):
        try:
            return Postcode.objects.get(code=postcode).shipping_zone.shipping_price
        except Postcode.DoesNotExist:
            return None


class SelfCollection(methods.Free):
    code = 'self-collection'
    name = 'Self Collection'
