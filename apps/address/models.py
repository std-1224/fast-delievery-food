from oscar.apps.address.models import * 
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.address.abstract_models import AbstractShippingAddress

class ShippingAddress(AbstractShippingAddress):
    # Override the postcode field to change its max_length
    # The original AbstractShippingAddress defines postcode with a default max_length
    # Redefining it here allows us to set a different max_length.
    postcode = models.CharField(
        _("Postcode"), max_length=256, blank=True, null=True)

    # You can add other custom fields or methods here if needed

    class Meta(AbstractShippingAddress.Meta):
        # You can keep the original Meta options or add your own
        pass

# You may need to keep other model imports from the original oscar.apps.address.models
# if you are using them elsewhere in your project, or override those models too.
# For example, if you use DefaultAddress:
# from oscar.apps.address.abstract_models import AbstractDefaultAddress
# class DefaultAddress(AbstractDefaultAddress):
#     pass

# If you had other local models in this file before, include them here as well. 
