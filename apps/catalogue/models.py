from django.db import models

from django.utils.translation import gettext_lazy as _
from oscar.apps.catalogue.abstract_models import AbstractAttributeOption, AbstractOption, AbstractCategory

from apps.system.services import get_system_config


class AttributeOption(AbstractAttributeOption):
    price = models.DecimalField(
        _("Price"), decimal_places=2, max_digits=12, blank=True, default=0
    )
    key = models.CharField(max_length=300, default='', blank=True)

    def save(self, *args, **kwargs):
        config = get_system_config()
        self.key = f"{self.option} {config.currency}{str(self.price)}"
        super(AttributeOption, self).save(*args, **kwargs)

    def __str__(self):
        return self.option

class Option(AbstractOption):
    def get_choices(self):
        if self.option_group:
            choices = [
                (opt.key, opt.key) for opt in self.option_group.options.all()
            ]
        else:
            choices = []

        if not self.required:
            choices = self.add_empty_choice(choices)

        return choices

class Category(AbstractCategory):
    price_range = models.CharField(max_length=100, blank=True, null=True)

from oscar.apps.catalogue.models import *
