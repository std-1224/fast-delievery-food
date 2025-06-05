from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from oscar.apps.checkout.forms import GatewayForm as BaseGatewayForm, ShippingAddressForm as BaseShippingAddressForm


class ShippingAddressForm(BaseShippingAddressForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adjust_country_field()
        self.adjust_postcode_field()

    def adjust_postcode_field(self):
        self.fields["postcode"].label = "Postcode"

    class Meta(BaseShippingAddressForm.Meta):
        fields = [
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line4",
            "postcode",
            "country",
            "phone_number",
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
