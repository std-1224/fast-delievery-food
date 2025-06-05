from oscar.apps.shipping.models import *
from django.db import models

from settings import OSCAR_DEFAULT_CURRENCY


class ShippingZone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, help_text=OSCAR_DEFAULT_CURRENCY)

    def __str__(self):
        return self.name

class Postcode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    shipping_zone = models.ForeignKey(ShippingZone, related_name='postcodes', on_delete=models.CASCADE)

    def clean(self):
        self.code = self.code.upper()
    def __str__(self):
        return self.code