from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormMixin
from oscar.apps.checkout import signals
from oscar.apps.checkout.views import (PaymentDetailsView as CorePaymentDetailsView,
                                       IndexView as CoreIndexView,
                                       ShippingAddressView as CoreShippingAddressView)
from oscar.apps.shipping.methods import NoShippingRequired
from oscar.core.loading import get_model, get_class, get_classes

from settings import PAYMENT_METHOD_CASH, PAYMENT_METHOD_CARD, STRIPE_PUBLISH_KEY, STRIPE_TOKEN, OSCAR_DEFAULT_CURRENCY, \
    PAYMENT_EVENT_SETTLED, STRIPE_EMAIL
from .facade import StripeFacade
from .forms import StripeTokenForm, GuestCheckoutForm

Repository = get_class("shipping.repository", "Repository")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
ShippingAddressForm, ShippingMethodForm, GatewayForm = get_classes(
    "checkout.forms", ["ShippingAddressForm", "ShippingMethodForm", "GatewayForm"]
)

Order = get_model("order", "Order")

SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')


class IndexView(CoreIndexView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get delivery type from session
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        context['delivery_type'] = delivery_type
        context['guest_checkout_form'] = GuestCheckoutForm(**self.get_form_kwargs())
        return context

    def get_form_kwargs(self):
        kwargs = FormMixin.get_form_kwargs(self)
        phone_number = self.checkout_session.get_guest_phone_number()
        email = self.checkout_session.get_guest_email()
        if email:
            kwargs["initial"] = {
                "username": email,
            }

        if phone_number:
            kwargs["initial"] = {
                "phone_number": phone_number,
            }

        return kwargs

    def form_valid(self, form):
        self.checkout_session.set_guest_email("")

        if form.is_guest_checkout():
            email = form.cleaned_data["email"]
            self.checkout_session.set_guest_email(email)

            # We raise a signal to indicate that the user has entered the
            # checkout process by specifying an email address.
            signals.start_checkout.send_robust(
                sender=self, request=self.request, email=email
            )

            messages.info(
                self.request,
                _(
                    "Create your account and then you will be redirected "
                    "back to the checkout process"
                ),
            )
            # success_url is set below based on order type
            self.success_url = None # Set to None here as it will be determined by logic below

        else:
            user = form.get_user()
            login(self.request, user)

            # We raise a signal to indicate that the user has entered the
            # checkout process.
            signals.start_checkout.send_robust(sender=self, request=self.request)

        # Get delivery type from session
        delivery_type = self.request.session.get('delivery_type', 'delivery')

        if delivery_type == 'delivery':
            # For delivery orders, go to shipping address first
            self.success_url = reverse("checkout:shipping-address")
        else:
            # For collection orders, skip shipping address and go directly to preview
            self.success_url = reverse("checkout:preview")

        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('phone_number', None):
            form = GuestCheckoutForm(**self.get_form_kwargs())
        else:
            form = GatewayForm(**self.get_form_kwargs())

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PaymentDetailsView(CorePaymentDetailsView):

    preview = True

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentDetailsView, self).dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        if request.POST.get("action", "") == "place_order":
            return super().post(request, *args, **kwargs)
        return super().render_payment_details(request, *args, **kwargs)
    

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['delivery_type'] = self.request.session.get('delivery_type', 'delivery')
        
        if self.preview:
            ctx['stripe_token_form'] = StripeTokenForm(self.request.POST)
            ctx['order_total_incl_tax_cents'] = (
                    ctx['order_total'].incl_tax * 100
            ).to_integral_value()
            ctx['payment_method'] = self.request.POST.get('payment_method')
        else:
            ctx['stripe_publish_key'] = STRIPE_PUBLISH_KEY

        return ctx

    def handle_payment(self, order_number, total, **kwargs):
        payment_method = self.request.POST['payment_method']
        if payment_method == PAYMENT_METHOD_CARD:
            stripe_ref = StripeFacade().charge(
                order_number,
                total,
                card=self.request.POST[STRIPE_TOKEN],
                description=self.payment_description(order_number, total, **kwargs),
                metadata=self.payment_metadata(order_number, total, **kwargs))

            source_type, __ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_CARD)
            source = Source(
                source_type=source_type,
                currency=OSCAR_DEFAULT_CURRENCY,
                amount_allocated=total.incl_tax,
                amount_debited=total.incl_tax,
                reference=self.request.POST[STRIPE_TOKEN])
            self.add_payment_source(source)

            self.add_payment_event(PAYMENT_EVENT_SETTLED, total.incl_tax, stripe_ref)
        else:
            source_type, __ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_CASH)
            source = Source(
                source_type=source_type,
                currency=OSCAR_DEFAULT_CURRENCY,
                amount_allocated=total.incl_tax,
                amount_debited=total.incl_tax)
            self.add_payment_source(source)
            self.add_payment_event("Pending", total.incl_tax)

    def payment_description(self, order_number, total, **kwargs):
        return self.request.POST[STRIPE_EMAIL]

    def payment_metadata(self, order_number, total, **kwargs):
        return {'order_number': order_number}


# pylint: disable=attribute-defined-outside-init
class ShippingMethodView(CheckoutSessionMixin, generic.FormView):
    """
    View for allowing a user to choose a shipping method.

    Shipping methods are largely domain-specific and so this view
    will commonly need to be subclassed and customised.

    The default behaviour is to load all the available shipping methods
    using the shipping Repository.  If there is only 1, then it is
    automatically selected.  Otherwise, a page is rendered where
    the user can choose the appropriate one.
    """

    template_name = "oscar/checkout/shipping_methods.html"
    form_class = ShippingMethodForm
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
    ]
    success_url = reverse_lazy("checkout:preview")

    def post(self, request, *args, **kwargs):
        self._methods = self.get_available_shipping_methods()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # These skip and pre conditions can't easily be factored out into the
        # normal pre-conditions as they do more than run a test and then raise
        # an exception on failure.

        # Check that shipping is required at all
        if not request.basket.is_shipping_required():
            # No shipping required - we store a special code to indicate so.
            self.checkout_session.use_shipping_method(NoShippingRequired().code)
            return self.get_success_response()

        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            messages.error(request, _("Please choose a shipping address"))
            return redirect("checkout:shipping-address")

        # Save shipping methods as instance var as we need them both here
        # and when setting the context vars.
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 0:
            # No shipping methods available for given address
            messages.warning(
                request,
                _(
                    "Shipping is unavailable for your chosen address - please "
                    "choose another"
                ),
            )
            return redirect("checkout:shipping-address")

        # Must be more than one available shipping method, we present them to
        # the user to make a choice.
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["methods"] = self._methods
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["methods"] = self._methods
        return kwargs

    def get_available_shipping_methods(self):
        """
        Returns all applicable shipping method objects for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address (so we pass all these things to the
        # repository).  I haven't come across a scenario that doesn't fit this
        # system.
        return Repository().get_shipping_methods(
            basket=self.request.basket,
            user=self.request.user,
            shipping_addr=self.get_shipping_address(self.request.basket),
            request=self.request,
        )

    def form_valid(self, form):
        # Save the code for the chosen shipping method in the session
        # and continue to the next step.
        self.checkout_session.use_shipping_method(form.cleaned_data["method_code"])
        return self.get_success_response()

    def form_invalid(self, form):
        messages.error(
            self.request, _("Your submitted dispatch method is not permitted")
        )
        return super().form_invalid(form)

    def get_success_response(self):
        return redirect(self.get_success_url())


class ShippingAddressView(CoreShippingAddressView):
    def get(self, request, *args, **kwargs):
        # Check if this is a collection order
        if request.session.get('delivery_type') == 'collection':
            return redirect('checkout:preview')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Check if this is a collection order
        if request.session.get('delivery_type') == 'collection':
            return redirect('checkout:preview')
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('checkout:preview')


class PreviewView(CheckoutSessionMixin, generic.TemplateView):
    template_name = 'oscar/checkout/preview.html'
    pre_conditions = [
        'check_basket_is_not_empty',
        'check_basket_is_valid',
        'check_user_email_is_captured',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['delivery_type'] = self.request.session.get('delivery_type', 'delivery')
        return ctx

    def get_success_url(self):
        return reverse('checkout:payment-details')

class PaymentMethodView(CheckoutSessionMixin, generic.TemplateView):
    template_name = 'oscar/checkout/payment_method.html'
    pre_conditions = [
        'check_basket_is_not_empty',
        'check_basket_is_valid',
        'check_user_email_is_captured',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['delivery_type'] = self.request.session.get('delivery_type', 'delivery')
        return ctx

    def get_success_url(self):
        return reverse('checkout:payment-details')


class ThankYouView(CheckoutSessionMixin, generic.TemplateView):
    template_name = 'oscar/checkout/thank_you.html'
    pre_conditions = [
        'check_basket_is_not_empty',
        'check_basket_is_valid',
        'check_user_email_is_captured',
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order_number'] = self.checkout_session.get_order_number()
        ctx['delivery_type'] = self.request.session.get('delivery_type', 'delivery')
        return ctx
