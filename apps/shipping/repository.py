from oscar.apps.shipping import repository
from . import methods
from .models import Postcode


class Repository(repository.Repository):

    def get_available_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        shipping_methods = [methods.SelfCollection()]
        if not shipping_addr:
            return shipping_methods

        # Extract actual postcode from full address string if needed
        postcode = self._extract_postcode(shipping_addr.postcode)
        shipping_rate = self._get_shipping_rate(postcode)
        if shipping_rate is not None:
            shipping_methods.append(methods.Standard(shipping_addr))
        return shipping_methods

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