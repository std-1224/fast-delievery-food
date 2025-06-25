from oscar.apps.shipping.models import *
from django.db import models

from settings import OSCAR_DEFAULT_CURRENCY


class ShippingZone(models.Model):
    name = models.CharField(max_length=255, unique=True)
    shipping_price = models.DecimalField(max_digits=255, decimal_places=100, help_text=OSCAR_DEFAULT_CURRENCY)

    def __str__(self):
        return self.name

class Postcode(models.Model):
    code = models.CharField(max_length=255)  # Allow any text, not unique
    shipping_zone = models.ForeignKey(ShippingZone, related_name='postcodes', on_delete=models.CASCADE)

    def __str__(self):
        return self.code