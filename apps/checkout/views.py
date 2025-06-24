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
from oscar.apps.checkout.views import (
    PaymentDetailsView as CorePaymentDetailsView,
    IndexView as CoreIndexView,
    ShippingAddressView as CoreShippingAddressView
)
from oscar.apps.shipping.methods import NoShippingRequired
from oscar.core.loading import get_model, get_class, get_classes
from django.http import HttpResponseRedirect

from settings import (
    PAYMENT_METHOD_CASH, PAYMENT_METHOD_CARD, STRIPE_PUBLISH_KEY, 
    STRIPE_TOKEN, OSCAR_DEFAULT_CURRENCY, PAYMENT_EVENT_SETTLED, STRIPE_EMAIL
)
from .facade import StripeFacade
from .forms import StripeTokenForm, GuestCheckoutForm

Repository = get_class("shipping.repository", "Repository")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
CheckoutSessionData = get_class("checkout.utils", "CheckoutSessionData")
ShippingAddressForm, ShippingMethodForm, GatewayForm = get_classes(
    "checkout.forms", ["ShippingAddressForm", "ShippingMethodForm", "GatewayForm"]
)

Order = get_model("order", "Order")
SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')

# Introduct youself
class IndexView(CoreIndexView):
    """
    Gateway view - handles delivery type selection and user authentication
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        context['delivery_type'] = delivery_type
        context['guest_checkout_form'] = GuestCheckoutForm(**self.get_form_kwargs())
        return context

    def get_form_kwargs(self):
        kwargs = FormMixin.get_form_kwargs(self)
        phone_number = self.checkout_session.get_guest_phone_number()
        email = self.checkout_session.get_guest_email()
        
        initial = {}
        if email:
            initial["username"] = email
        if phone_number:
            initial["phone_number"] = phone_number
            
        if initial:
            kwargs["initial"] = initial

        return kwargs

    def post(self, request, *args, **kwargs):
        # Store delivery type from form
        delivery_type = request.POST.get('delivery_type', 'delivery')
        request.session['delivery_type'] = delivery_type
        
        # Handle guest checkout form
        if request.POST.get('phone_number'):
            form = GuestCheckoutForm(request.POST)
            if form.is_valid():
                return self.handle_guest_checkout(form)
        else:
            # Handle regular login/register form
            form = GatewayForm(**self.get_form_kwargs())
            if form.is_valid():
                return self.handle_user_checkout(form)
        
        # If form is invalid, re-render with errors
        return self.form_invalid(form)

    def handle_guest_checkout(self, form):
        """Handle guest checkout submission"""
        # Store guest information in session

        print("Handling guest checkout")
        email = form.cleaned_data["email"]
        phone_number = form.cleaned_data["phone_number"]
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        
        self.checkout_session.set_guest_email(email)
        
        # Store additional guest info in session
        self.request.session['guest_phone_number'] = phone_number
        self.request.session['guest_first_name'] = first_name
        self.request.session['guest_last_name'] = last_name
        
        signals.start_checkout.send_robust(sender=self, request=self.request, email=email)
        
        return self.redirect_to_next_step()

    def handle_user_checkout(self, form):
        """Handle registered user checkout"""
        print("Handling user checkout")
        user = form.get_user()
        if user:
            login(self.request, user)
        
        signals.start_checkout.send_robust(sender=self, request=self.request)
        
        return self.redirect_to_next_step()

    # it judeg the deliveryType and skip the step by DeliveryType

    def redirect_to_next_step(self):
        """Redirect to appropriate next step based on delivery type"""
        print("Redirecting to next step")
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'delivery':
            # Delivery: Gateway -> Shipping Address -> Preview -> Payment -> Confirmation
            return HttpResponseRedirect(reverse('checkout:shipping-address'))
        else:
            # Collection: Gateway -> Preview -> Payment -> Confirmation
            # Set no shipping required for collection
            self.checkout_session.use_shipping_method(NoShippingRequired().code)
            return HttpResponseRedirect(reverse('checkout:preview'))


class ShippingAddressView(CoreShippingAddressView):
    """
    Shipping address view - only used for delivery orders
    """
    form_class = ShippingAddressForm

    def get_success_url(self):
        return HttpResponseRedirect(reverse('checkout:preview'))

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PreviewView(CheckoutSessionMixin, generic.TemplateView):
    """
    Preview view - Step 2 for collection, Step 3 for delivery
    Shows order summary before payment
    """
    template_name = 'oscar/checkout/preview.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check basic pre-conditions
        for pre_condition in self.get_pre_conditions(request):
            response = getattr(self, pre_condition)(request)
            if response:
                return response

        # Check delivery type specific requirements
        delivery_type = request.session.get('delivery_type')
        if not delivery_type:
            return redirect('checkout:index')

        if delivery_type == 'delivery':
            # For delivery: must have shipping address
            if not self.checkout_session.is_shipping_address_set():
                return redirect('checkout:shipping-address')
        elif delivery_type == 'collection':
            # For collection: ensure no shipping method is set
            if not self.checkout_session.is_shipping_method_set(request.basket):
                self.checkout_session.use_shipping_method(NoShippingRequired().code)

        return super().dispatch(request, *args, **kwargs)

    def get_pre_conditions(self, request):
        return [
            'check_basket_is_not_empty',
            'check_basket_is_valid',
            'check_user_email_is_captured',
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        ctx['delivery_type'] = delivery_type
        
        # Add order summary context
        ctx['basket'] = self.request.basket
        # Calculate order total
        shipping_method = self.get_shipping_method()
        shipping_charge = shipping_method.calculate(self.request.basket)
        ctx['order_total'] = {
            'excl_tax': self.request.basket.total_excl_tax + shipping_charge.excl_tax,
            'incl_tax': self.request.basket.total_incl_tax + shipping_charge.incl_tax,
        }
        
        # Only include shipping address for delivery
        if delivery_type == 'delivery':
            ctx['shipping_address'] = self.get_shipping_address()
        
        ctx['shipping_method'] = self.get_shipping_method()
        
        # Add guest information if available
        ctx['guest_email'] = self.checkout_session.get_guest_email()
        ctx['guest_phone_number'] = self.request.session.get('guest_phone_number')
        ctx['guest_first_name'] = self.request.session.get('guest_first_name')
        ctx['guest_last_name'] = self.request.session.get('guest_last_name')
        
        return ctx

    def get_shipping_address(self, basket=None):
        """Get shipping address from session"""
        # For collection orders, we don't need a shipping address
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'collection':
            return None
        return None

    def get_shipping_method(self, basket=None, shipping_address=None, **kwargs):
        """Get shipping method from session"""
        try:
            return self.checkout_session.shipping_method(basket or self.request.basket)
        except:
            from oscar.apps.shipping.methods import NoShippingRequired
            return NoShippingRequired()

    def post(self, request, *args, **kwargs):
        """Handle form submission to proceed to payment"""
        return redirect('checkout:payment-details')


class PaymentDetailsView(CorePaymentDetailsView):
    """
    Payment details view - handles payment processing
    """
    preview = True

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # Check basic pre-conditions
        for pre_condition in self.get_pre_conditions(request):
            response = getattr(self, pre_condition)(request)
            if response:
                return response

        # Check delivery type specific requirements
        delivery_type = request.session.get('delivery_type')
        if not delivery_type:
            return redirect('checkout:index')

        if delivery_type == 'delivery':
            # For delivery: must have shipping address
            if not self.checkout_session.is_shipping_address_set():
                return redirect('checkout:shipping-address')
        elif delivery_type == 'collection':
            # For collection: ensure no shipping method is set
            if not self.checkout_session.is_shipping_method_set(request.basket):
                self.checkout_session.use_shipping_method(NoShippingRequired().code)

        return super().dispatch(request, *args, **kwargs)

    def get_pre_conditions(self, request):
        return [
            'check_basket_is_not_empty',
            'check_basket_is_valid',
            'check_user_email_is_captured',
        ]

    def get_shipping_address(self, basket=None):
        """Get shipping address from session"""
        # For collection orders, we don't need a shipping address
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'collection':
            return None
        return None

    def get_shipping_method(self, basket=None, shipping_address=None, **kwargs):
        """Get shipping method from session"""
        try:
            return self.checkout_session.shipping_method(basket or self.request.basket)
        except:
            from oscar.apps.shipping.methods import NoShippingRequired
            return NoShippingRequired()

    def post(self, request, *args, **kwargs):
        if request.POST.get("action", "") == "place_order":
            return super().post(request, *args, **kwargs)
        return self.render_payment_details(request, *args, **kwargs)

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
        """Handle payment based on selected method"""
        payment_method = self.request.POST['payment_method']
        
        if payment_method == PAYMENT_METHOD_CARD:
            # Process card payment via Stripe
            stripe_ref = StripeFacade().charge(
                order_number,
                total,
                card=self.request.POST[STRIPE_TOKEN],
                description=self.payment_description(order_number, total, **kwargs),
                metadata=self.payment_metadata(order_number, total, **kwargs)
            )

            source_type, _ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_CARD)
            source = Source(
                source_type=source_type,
                currency=OSCAR_DEFAULT_CURRENCY,
                amount_allocated=total.incl_tax,
                amount_debited=total.incl_tax,
                reference=self.request.POST[STRIPE_TOKEN]
            )
            self.add_payment_source(source)
            self.add_payment_event(PAYMENT_EVENT_SETTLED, total.incl_tax, stripe_ref)
        else:
            # Process cash payment
            source_type, _ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_CASH)
            source = Source(
                source_type=source_type,
                currency=OSCAR_DEFAULT_CURRENCY,
                amount_allocated=total.incl_tax,
                amount_debited=total.incl_tax
            )
            self.add_payment_source(source)
            self.add_payment_event("Pending", total.incl_tax)

    def payment_description(self, order_number, total, **kwargs):
        return self.request.POST.get(STRIPE_EMAIL, '')

    def payment_metadata(self, order_number, total, **kwargs):
        return {'order_number': order_number}

    def get_success_url(self):
        return reverse('checkout:thank-you')


class ThankYouView(CheckoutSessionMixin, generic.TemplateView):
    """
    Thank you view - order confirmation
    """
    template_name = 'oscar/checkout/thank_you.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['delivery_type'] = self.request.session.get('delivery_type', 'delivery')
        # Add order details if available
        order_number = self.request.session.get('checkout_order_number')
        if order_number:
            try:
                ctx['order'] = Order.objects.get(number=order_number)
            except Order.DoesNotExist:
                pass
        return ctx