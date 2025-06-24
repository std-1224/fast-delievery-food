from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.address.abstract_models import AbstractShippingAddress, AbstractUserAddress, AbstractBillingAddress

class UserAddress(AbstractUserAddress):
    # Override the postcode field to accept any format
    postcode = models.CharField(
        _("Postcode"), max_length=255, blank=True, null=True, default="")

    def get_field_values(self, fields):
        """
        Override to customize how postcode is displayed
        """
        field_values = []
        for field in fields:
            # Title is special case
            if field == "title":
                value = self.get_title_display()
            elif field == "country":
                try:
                    value = self.country.printable_name
                except:
                    value = ""
            elif field == "salutation":
                value = self.salutation
            elif field == "postcode":
                # Custom postcode formatting - display the full address-like format
                value = self.format_postcode_display()
            else:
                value = getattr(self, field)
            field_values.append(value)
        return field_values

    def format_postcode_display(self):
        """
        Format postcode in the desired format:
        "GU7 7, Lower Eashing, Eashing, Shackleford, Guildford, Surrey, England, GU7 2QG, United Kingdom"
        """
        if not self.postcode:
            return ""

        # If the postcode already contains commas, assume it's in the desired format
        if "," in self.postcode:
            return self.postcode

        # Otherwise, just return the postcode as-is
        return self.postcode

    def ensure_postcode_is_valid_for_country(self):
        """
        Override to disable postcode validation - accept any postcode format
        """
        pass

    class Meta(AbstractUserAddress.Meta):
        pass

class ShippingAddress(AbstractShippingAddress):
    # Override the postcode field to make it required with a default value
    postcode = models.CharField(
        _("Postcode"), max_length=255, blank=False, null=False, default="")

    def get_field_values(self, fields):
        """
        Override to customize how postcode is displayed
        """
        field_values = []
        for field in fields:
            # Title is special case
            if field == "title":
                value = self.get_title_display()
            elif field == "country":
                try:
                    value = self.country.printable_name
                except:
                    value = ""
            elif field == "salutation":
                value = self.salutation
            elif field == "postcode":
                # Custom postcode formatting - display the full address-like format
                value = self.format_postcode_display()
            else:
                value = getattr(self, field)
            field_values.append(value)
        return field_values

    def format_postcode_display(self):
        """
        Format postcode in the desired format:
        "GU7 7, Lower Eashing, Eashing, Shackleford, Guildford, Surrey, England, GU7 2QG, United Kingdom"
        """
        if not self.postcode:
            return ""

        # If the postcode already contains commas, assume it's in the desired format
        if "," in self.postcode:
            return self.postcode

        # Otherwise, just return the postcode as-is
        return self.postcode

    def ensure_postcode_is_valid_for_country(self):
        """
        Override to disable postcode validation - accept any postcode format
        """
        pass

    class Meta(AbstractShippingAddress.Meta):
        # You can keep the original Meta options or add your own
        pass

class BillingAddress(AbstractBillingAddress):
    # Override the postcode field to accept any format
    postcode = models.CharField(
        _("Postcode"), max_length=255, blank=True, null=True, default="")

    def get_field_values(self, fields):
        """
        Override to customize how postcode is displayed
        """
        field_values = []
        for field in fields:
            # Title is special case
            if field == "title":
                value = self.get_title_display()
            elif field == "country":
                try:
                    value = self.country.printable_name
                except:
                    value = ""
            elif field == "salutation":
                value = self.salutation
            elif field == "postcode":
                # Custom postcode formatting - display the full address-like format
                value = self.format_postcode_display()
            else:
                value = getattr(self, field)
            field_values.append(value)
        return field_values

    def format_postcode_display(self):
        """
        Format postcode in the desired format:
        "GU7 7, Lower Eashing, Eashing, Shackleford, Guildford, Surrey, England, GU7 2QG, United Kingdom"
        """
        if not self.postcode:
            return ""

        # If the postcode already contains commas, assume it's in the desired format
        if "," in self.postcode:
            return self.postcode

        # Otherwise, just return the postcode as-is
        return self.postcode

    def ensure_postcode_is_valid_for_country(self):
        """
        Override to disable postcode validation - accept any postcode format
        """
        pass

    class Meta(AbstractBillingAddress.Meta):
        pass

# Import the Country model from Oscar
from oscar.apps.address.models import Country
