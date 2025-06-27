from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from oscar.apps.checkout.forms import GatewayForm as BaseGatewayForm, ShippingAddressForm as BaseShippingAddressForm
from oscar.core.loading import get_model

Country = get_model("address", "Country")


class ShippingAddressForm(BaseShippingAddressForm):
    postcode = forms.CharField(
        label=_("Postcode"),
        max_length=255,
        required=True,
        help_text=_("Please enter your postcode.")
    )

    def __init__(self, *args, **kwargs):
        # Get delivery type from kwargs if provided
        delivery_type = kwargs.pop('delivery_type', 'delivery')
        super().__init__(*args, **kwargs)
        self.adjust_country_field()

        # Explicitly remove redundant fields that are already collected in Gateway
        fields_to_remove = ['first_name', 'last_name', 'phone_number']
        for field_name in fields_to_remove:
            if field_name in self.fields:
                del self.fields[field_name]

        # For delivery orders, remove notes field (will be on preview page)
        if delivery_type == 'delivery' and 'notes' in self.fields:
            del self.fields['notes']

    def adjust_country_field(self):
        """Adjust country field based on available shipping countries"""
        countries = Country._default_manager.filter(is_shipping_country=True)

        # No need to show country dropdown if there is only one option
        if len(countries) == 1:
            self.fields.pop("country", None)
            self.instance.country = countries[0]
        else:
            self.fields["country"].queryset = countries
            self.fields["country"].empty_label = None

    def clean_postcode(self):
        # Accept any postcode, no validation
        return self.cleaned_data.get('postcode')

    def clean(self):
        # Override the parent clean method to skip postcode validation
        cleaned_data = super().clean()
        # Remove any postcode validation errors
        if 'postcode' in self.errors:
            del self.errors['postcode']
        return cleaned_data

    class Meta(BaseShippingAddressForm.Meta):
        fields = [
            "line1",
            "line2",
            "line4",
            "postcode",
            "country",
            "notes",
        ]


class PaymentMethodForm(forms.Form):
    """
    Extra form for the custom payment method.
    """
    payment_method = forms.ChoiceField(
        label=_("Select a payment method"),
        choices=settings.PAYMENT_METHODS,
        widget=forms.RadioSelect()
    )


def get_payment_method_display(payment_method):
    return dict(settings.PAYMENT_METHODS).get(payment_method)


class DeliveryInstructionsForm(forms.Form):
    """
    Form for delivery/collection instructions on the preview page
    """
    delivery_instructions = forms.CharField(
        label=_("Special Instructions"),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Any special instructions for your order (optional)'),
            'class': 'form-control'
        }),
        required=False,
        help_text=_("Optional: Add any special instructions for your order")
    )


class StripeTokenForm(forms.Form):
    stripeEmail = forms.EmailField(widget=forms.HiddenInput())
    stripeToken = forms.CharField(widget=forms.HiddenInput())


class GatewayForm(BaseGatewayForm):
    username = forms.EmailField(label=_("My email address is"))
    NEW, EXISTING = "new", "existing"
    CHOICES = (
        (
            NEW,
            _(
                "I am a new customer and want to create an account "
                "before checking out"
            ),
        ),
        (EXISTING, _("I am a returning customer, and my password is")),
    )
    options = forms.ChoiceField(
        widget=forms.widgets.RadioSelect, choices=CHOICES, initial=NEW
    )


class GuestCheckoutForm(forms.Form):
    phone_number = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(label=_("First name"), max_length=150, required=True)
    last_name = forms.CharField(label=_("Last name"), max_length=150, required=True)
    email = forms.EmailField(label=_("Email address"), required=True)

    def is_guest_checkout(self):
        return True

    def get_user(self):
        return None
