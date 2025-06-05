from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from oscar.apps.order.abstract_models import AbstractOrder, AbstractLine

from settings import PAYMENT_EVENT_SETTLED


class Order(AbstractOrder):
    guest_first_name = models.CharField(_("first name"), max_length=150, blank=True)
    guest_last_name = models.CharField(_("last name"), max_length=150, blank=True)
    guest_phone_number = models.CharField(_("Guest phone number"), blank=True, max_length=50)

    created = models.DateTimeField(_("created"), auto_now_add=True)
    updated = models.DateTimeField(_("updated"), auto_now=True)

    @property
    def is_anonymous(self):
        return self.user is None and (bool(self.guest_email) or bool(self.guest_phone_number))

    @property
    def is_paid(self):
        paid_event_type, _ = PaymentEventType.objects.get_or_create(name=PAYMENT_EVENT_SETTLED)
        paid_amount = sum(
            event.amount for event in self.payment_events.filter(event_type=paid_event_type)
        )

        # Compare with order total
        return paid_amount >= self.total_incl_tax


class Line(AbstractLine):
    @property
    def product_title(self):
        return smart_str(self.product)

    @property
    def attribute_values(self):
        values = self.attributes.values_list("value", flat=True)
        flat_values = []
        for value in values:
            if isinstance(value, list):
                for v in value:
                    flat_values.append(v)
            else:
                flat_values.append(value)
        return flat_values


from oscar.apps.order.models import *
