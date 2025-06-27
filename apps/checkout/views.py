from urllib.parse import quote
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
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

# PayPal imports
from paypal.express.views import RedirectView as PayPalRedirectView
from paypal.express.exceptions import (
    MissingShippingAddressException,
    MissingShippingMethodException,
    EmptyBasketException,
    InvalidBasket
)
from paypal.exceptions import PayPalError

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

    Workflows:
    - Authenticated + Delivery: Direct to Shipping Address
    - Authenticated + Collection: Direct to Preview
    - Guest + Delivery: Gateway → Delivery Address
    - Guest + Collection: Gateway → Preview
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        context['delivery_type'] = delivery_type
        context['guest_checkout_form'] = GuestCheckoutForm(**self.get_form_kwargs())
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET requests - route authenticated users directly, show gateway for guests"""

        # TEMPORARY DEBUG: Show what's happening
        print("=" * 80)
        print("🔍 DEBUGGING CHECKOUT FLOW")
        print(f"🔍 User authenticated: {request.user.is_authenticated}")
        print(f"🔍 URL: {request.get_full_path()}")
        print(f"🔍 URL parameters: {dict(request.GET)}")
        print(f"🔍 Session delivery_type: {request.session.get('delivery_type')}")
        print(f"🔍 All session keys: {list(request.session.keys())}")
        print("=" * 80)

        # For authenticated users, route directly based on delivery type
        if request.user.is_authenticated:
            delivery_type = request.session.get('delivery_type')

            # ALWAYS check URL parameter and update session if provided
            url_delivery_type = request.GET.get('delivery_type')
            if url_delivery_type:
                delivery_type = url_delivery_type
                request.session['delivery_type'] = delivery_type
                print(f"✅ UPDATED delivery_type from URL parameter: {delivery_type}")
            elif not delivery_type:
                # Only set default if no session value AND no URL parameter
                delivery_type = 'delivery'
                request.session['delivery_type'] = delivery_type
                print(f"✅ Set default delivery_type: {delivery_type}")

            print(f"🎯 FINAL DECISION: delivery_type = {delivery_type}")
            print("🚀 CALLING redirect_to_next_step() method")

            # Use the existing redirect_to_next_step method which has the correct logic
            return self.redirect_to_next_step()

        # For guest users, show the gateway form
        print("👤 Guest user, showing gateway form")
        return super().get(request, *args, **kwargs)

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

        # Store additional guest info in both session and checkout session
        self.request.session['guest_phone_number'] = phone_number
        self.request.session['guest_first_name'] = first_name
        self.request.session['guest_last_name'] = last_name

        # Also store in checkout session for consistency
        self.checkout_session.set_guest_info(first_name, last_name, phone_number)
        
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
        """Redirect to appropriate next step based on delivery type and authentication"""
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        is_authenticated = self.request.user.is_authenticated

        print("=" * 80)
        print("🔍 REDIRECT_TO_NEXT_STEP DEBUG")
        print(f"🔍 delivery_type from session: '{delivery_type}'")
        print(f"🔍 delivery_type type: {type(delivery_type)}")
        print(f"🔍 is_authenticated: {is_authenticated}")
        print(f"🔍 delivery_type == 'delivery': {delivery_type == 'delivery'}")
        print(f"🔍 delivery_type == 'collection': {delivery_type == 'collection'}")
        print("=" * 80)

        if is_authenticated:
            # Authenticated users: Delivery goes to shipping address, Collection goes to preview
            if delivery_type == 'delivery':
                print("✅ DELIVERY DETECTED - GOING TO SHIPPING ADDRESS")
                redirect_url = reverse('checkout:shipping-address')
                print(f"✅ Redirect URL: {redirect_url}")
                return HttpResponseRedirect(redirect_url)
            elif delivery_type == 'collection':
                print("✅ COLLECTION DETECTED - GOING TO PREVIEW")
                self.checkout_session.use_shipping_method(NoShippingRequired().code)
                redirect_url = reverse('checkout:preview')
                print(f"✅ Redirect URL: {redirect_url}")
                return HttpResponseRedirect(redirect_url)
            else:
                print(f"🚨 UNKNOWN DELIVERY TYPE: '{delivery_type}' - DEFAULTING TO SHIPPING ADDRESS")
                redirect_url = reverse('checkout:shipping-address')
                print(f"🚨 Default Redirect URL: {redirect_url}")
                return HttpResponseRedirect(redirect_url)
        else:
            # Guest users: Different flows based on delivery type
            if delivery_type == 'delivery':
                # Guest + Delivery: Gateway -> Delivery Address -> Preview -> Payment -> Confirmation
                print("Guest user with delivery: Redirecting to shipping-address")
                return HttpResponseRedirect(reverse('checkout:shipping-address'))
            else:
                # Guest + Collection: Gateway -> Preview -> Payment -> Confirmation
                print("Guest user with collection: Redirecting to preview")
                self.checkout_session.use_shipping_method(NoShippingRequired().code)
                return HttpResponseRedirect(reverse('checkout:preview'))


class ShippingAddressView(CoreShippingAddressView):
    """
    Shipping address view - only used for delivery orders
    """
    form_class = ShippingAddressForm

    def form_valid(self, form):
        """Override to populate missing fields from gateway data before saving"""
        # Get gateway data from session
        first_name = (self.request.session.get('guest_first_name') or
                     self.checkout_session.get_guest_first_name())
        last_name = (self.request.session.get('guest_last_name') or
                    self.checkout_session.get_guest_last_name())
        phone_number = (self.request.session.get('guest_phone_number') or
                       self.checkout_session.get_guest_phone_number())

        # For authenticated users, use their profile data as fallback
        if self.request.user.is_authenticated:
            first_name = first_name or self.request.user.first_name
            last_name = last_name or self.request.user.last_name

        # Add the missing fields to the form's cleaned_data
        if first_name:
            form.cleaned_data['first_name'] = first_name
        if last_name:
            form.cleaned_data['last_name'] = last_name
        if phone_number:
            form.cleaned_data['phone_number'] = phone_number

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        # Check if delivery type is collection - if so, redirect to preview
        # This check must happen BEFORE calling super().dispatch() to avoid pre-condition checks
        delivery_type = request.session.get('delivery_type')
        print(f"ShippingAddressView.dispatch: delivery_type={delivery_type}, user_authenticated={request.user.is_authenticated}")

        # For authenticated users, if no delivery type is set, try to get from URL parameter
        if request.user.is_authenticated and not delivery_type:
            delivery_type = request.GET.get('delivery_type')
            if delivery_type:
                request.session['delivery_type'] = delivery_type
                print(f"ShippingAddressView: Set delivery_type from URL parameter: {delivery_type}")
            else:
                # If still no delivery type, redirect to checkout index to set it properly
                print("ShippingAddressView: No delivery type found, redirecting to checkout index")
                return redirect('checkout:index')

        if delivery_type == 'collection':
            print("🚨 CRITICAL: COLLECTION ORDER DETECTED IN SHIPPING ADDRESS VIEW!")
            print("🚨 REDIRECTING TO PREVIEW IMMEDIATELY - NO SHIPPING ADDRESS NEEDED!")

            # Ensure NoShippingRequired method is set for collection orders
            try:
                if not self.checkout_session.is_shipping_method_set(request.basket):
                    self.checkout_session.use_shipping_method(NoShippingRequired().code)
                    print("✅ Set NoShippingRequired method for collection order")
            except Exception as e:
                print(f"Warning: Could not set shipping method: {e}")

            messages.info(request, "Collection orders do not require a shipping address.")
            return redirect('checkout:preview')

        # If no delivery type is set, redirect to index to select delivery type
        if not delivery_type:
            messages.warning(request, "Please select a delivery type first.")
            return redirect('checkout:index')

        # For delivery orders, proceed with normal flow
        print(f"ShippingAddressView: Proceeding with delivery flow for authenticated user")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Override GET to ensure collection orders never see the shipping address form"""
        delivery_type = request.session.get('delivery_type')
        print(f"🚨 ShippingAddressView.get: delivery_type={delivery_type}")

        if delivery_type == 'collection':
            print("🚨 COLLECTION ORDER IN GET METHOD - REDIRECTING TO PREVIEW!")
            # Set no shipping required for collection
            try:
                if not self.checkout_session.is_shipping_method_set(request.basket):
                    self.checkout_session.use_shipping_method(NoShippingRequired().code)
            except Exception as e:
                print(f"Warning: Could not set shipping method: {e}")

            messages.info(request, "Collection orders go directly to preview.")
            return redirect('checkout:preview')

        # For delivery orders, proceed with normal form display
        print("✅ ShippingAddressView.get: Showing shipping address form for delivery order")
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        # Override to redirect directly to preview, skipping shipping method selection
        return reverse('checkout:preview')

    def get_skip_conditions(self, request):
        # Override to remove shipping method related skip conditions
        return [
            'check_basket_is_not_empty',
            'check_basket_is_valid',
            'check_user_email_is_captured',
        ]

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle shipping address form submission"""
        response = super().post(request, *args, **kwargs)

        # After successful address submission, set a default shipping method for delivery orders
        if hasattr(response, 'status_code') and response.status_code == 302:
            # This is a redirect, meaning the form was successful
            delivery_type = request.session.get('delivery_type', 'delivery')
            if delivery_type == 'delivery':
                # Set a default shipping method for delivery orders
                # The shipping method will be determined based on the address
                shipping_address = self.get_shipping_address(request.basket)
                if shipping_address:
                    # Get available shipping methods for this address
                    repository = Repository()
                    methods = repository.get_available_shipping_methods(
                        basket=request.basket,
                        shipping_addr=shipping_address,
                        user=request.user,
                        request=request
                    )
                    # Use the first available delivery method (not self-collection)
                    for method in methods:
                        if method.code == 'delivery':
                            self.checkout_session.use_shipping_method(method.code)
                            break

        return response


class PreviewView(CheckoutSessionMixin, generic.TemplateView):
    """
    Preview view - Shows order summary before payment

    Workflows:
    - Authenticated + Delivery: Shipping Address -> Preview -> Payment -> Confirmation
    - Authenticated + Collection: Preview -> Payment -> Confirmation
    - Guest + Delivery: Gateway -> Delivery Address -> Preview -> Payment -> Confirmation
    - Guest + Collection: Gateway -> Preview -> Payment -> Confirmation
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
            # For delivery: must have shipping address (both authenticated and guest users)
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
        
        # Add gateway/user information
        ctx['user'] = self.request.user

        # Add guest information if available (with fallbacks)
        ctx['guest_email'] = self.checkout_session.get_guest_email()
        ctx['guest_phone_number'] = (self.request.session.get('guest_phone_number') or
                                    self.checkout_session.get_guest_phone_number())
        ctx['guest_first_name'] = (self.request.session.get('guest_first_name') or
                                 self.checkout_session.get_guest_first_name())
        ctx['guest_last_name'] = (self.request.session.get('guest_last_name') or
                                self.checkout_session.get_guest_last_name())

        # Add payment method (default to cash)
        ctx['payment_method'] = 'cash'

        # Add comprehensive gateway information
        if self.request.user.is_authenticated:
            # For authenticated users
            ctx['customer_name'] = f"{self.request.user.first_name} {self.request.user.last_name}".strip()
            ctx['customer_email'] = self.request.user.email
            ctx['customer_type'] = 'Registered User'
        else:
            # For guest users (with fallbacks)
            guest_first_name = (self.request.session.get('guest_first_name') or
                              self.checkout_session.get_guest_first_name() or '')
            guest_last_name = (self.request.session.get('guest_last_name') or
                             self.checkout_session.get_guest_last_name() or '')
            ctx['customer_name'] = f"{guest_first_name} {guest_last_name}".strip()
            ctx['customer_email'] = self.checkout_session.get_guest_email()
            ctx['customer_phone'] = (self.request.session.get('guest_phone_number') or
                                   self.checkout_session.get_guest_phone_number())
            ctx['customer_type'] = 'Guest User'

        return ctx

    def get_shipping_address(self, basket=None):
        """Get shipping address from session"""
        # For collection orders, we don't need a shipping address
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'collection':
            return None

        # For delivery orders, we need to get the shipping address even if basket doesn't require shipping
        # This is because our delivery type logic overrides the basket's shipping requirement
        from oscar.core.loading import get_model
        ShippingAddress = get_model("order", "ShippingAddress")

        # Check if we have shipping address data in session
        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)

        # Check if user selected an existing address
        addr_id = self.checkout_session.shipping_user_address_id()
        if addr_id:
            try:
                UserAddress = get_model("address", "UserAddress")
                address = UserAddress._default_manager.get(pk=addr_id)
                # Copy user address data into a blank shipping address instance
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr
            except UserAddress.DoesNotExist:
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
        # Check if this is a place_order action
        if request.POST.get("action", "") == "place_order":
            # Redirect to payment-details for actual order processing
            return redirect('checkout:payment-details')

        # Otherwise, normal preview form submission
        return redirect('checkout:payment-details')


class PaymentDetailsView(CorePaymentDetailsView):
    """
    Payment details view - handles payment processing
    """

    def dispatch(self, request, *args, **kwargs):
        # Check delivery type and ensure shipping method is set for collection
        delivery_type = request.session.get('delivery_type')
        if not delivery_type:
            return redirect('checkout:index')

        if delivery_type == 'collection':
            # For collection: ensure NoShippingRequired method is set
            if not self.checkout_session.is_shipping_method_set(request.basket):
                self.checkout_session.use_shipping_method(NoShippingRequired().code)

        return super().dispatch(request, *args, **kwargs)

    def get_pre_conditions(self, request):
        # Base pre-conditions for all orders
        pre_conditions = [
            'check_basket_is_not_empty',
            'check_basket_is_valid',
            'check_user_email_is_captured',
        ]

        # Only check shipping data for delivery orders
        delivery_type = request.session.get('delivery_type', 'delivery')
        if delivery_type == 'delivery':
            pre_conditions.append('check_shipping_data_is_captured')

        # Add payment data check for preview mode
        if self.preview:
            pre_conditions.append('check_payment_data_is_captured')

        return pre_conditions

    def get_shipping_address(self, basket=None):
        """Get shipping address from session"""
        # For collection orders, we don't need a shipping address
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'collection':
            return None

        # For delivery orders, we need to get the shipping address even if basket doesn't require shipping
        # This is because our delivery type logic overrides the basket's shipping requirement
        from oscar.core.loading import get_model
        ShippingAddress = get_model("order", "ShippingAddress")

        # Check if we have shipping address data in session
        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)

        # Check if user selected an existing address
        addr_id = self.checkout_session.shipping_user_address_id()
        if addr_id:
            try:
                UserAddress = get_model("address", "UserAddress")
                address = UserAddress._default_manager.get(pk=addr_id)
                # Copy user address data into a blank shipping address instance
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr
            except UserAddress.DoesNotExist:
                return None

        return None

    def get_shipping_method(self, basket=None, shipping_address=None, **kwargs):
        """Get shipping method from session"""
        try:
            return self.checkout_session.shipping_method(basket or self.request.basket)
        except:
            from oscar.apps.shipping.methods import NoShippingRequired
            return NoShippingRequired()

    def check_shipping_data_is_captured(self, request):
        """
        Override to handle delivery type specific shipping requirements
        and ensure shipping method is set for delivery orders
        """
        delivery_type = request.session.get('delivery_type', 'delivery')

        if delivery_type == 'collection':
            # For collection orders, ensure NoShippingRequired is set
            if not self.checkout_session.is_shipping_method_set(request.basket):
                self.checkout_session.use_shipping_method(NoShippingRequired().code)
            return None

        # For delivery orders, check shipping address and method
        if not self.checkout_session.is_shipping_address_set():
            return redirect('checkout:shipping-address')

        # Ensure shipping method is set for delivery orders
        if not self.checkout_session.is_shipping_method_set(request.basket):
            shipping_address = self.get_shipping_address()
            if shipping_address:
                # Get available shipping methods for this address
                repository = Repository()
                methods = repository.get_available_shipping_methods(
                    basket=request.basket,
                    shipping_addr=shipping_address,
                    user=request.user,
                    request=request
                )
                # Use the first available delivery method (not self-collection)
                delivery_method = None
                for method in methods:
                    if method.code == 'delivery':
                        delivery_method = method
                        self.checkout_session.use_shipping_method(method.code)
                        break

                if not delivery_method:
                    # No delivery method found - create a default one
                    # This handles cases where postcode data is missing
                    from apps.shipping.methods import Standard
                    default_method = Standard(shipping_address)
                    self.checkout_session.use_shipping_method(default_method.code)
            else:
                # No shipping address, redirect to shipping address page
                return redirect('checkout:shipping-address')

        return None



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

        # Add customer email for display
        if self.request.user.is_authenticated:
            ctx['customer_email'] = self.request.user.email
        else:
            # Get guest email from checkout session
            checkout_session = CheckoutSessionData(self.request)
            ctx['customer_email'] = checkout_session.get_guest_email()

        # Add order details if available
        order_number = self.request.session.get('checkout_order_number')
        if order_number:
            try:
                ctx['order'] = Order.objects.get(number=order_number)
            except Order.DoesNotExist:
                pass

        # For testing: create realistic mock order data if no real order exists
        if not ctx.get('order') and 'test_mode' in self.request.GET:
            from decimal import Decimal
            import random

            # Create a realistic order number
            order_number = f"ORD-{random.randint(10000, 99999)}"

            # Create mock order object with realistic data based on session
            class MockOrder:
                def __init__(self, request):
                    from oscar.core.loading import get_model

                    self.number = order_number
                    # Use basket total if available, otherwise default
                    try:
                        self.total_incl_tax = request.basket.total_incl_tax or Decimal('25.99')
                    except:
                        self.total_incl_tax = Decimal('25.99')

                    # Currency
                    self.currency = 'GBP'

                    # Get guest info from session
                    self.guest_phone_number = request.session.get('guest_phone_number')
                    self.guest_email = request.session.get('guest_email')

                    # Get customer info
                    if request.user.is_authenticated:
                        self.user = request.user
                        self.guest_phone_number = None  # Authenticated users don't use guest phone
                    else:
                        self.user = None

                    # Mock shipping address for delivery orders
                    delivery_type = request.session.get('delivery_type', 'delivery')
                    if delivery_type == 'delivery':
                        # Create mock shipping address
                        class MockShippingAddress:
                            def __init__(self):
                                self.first_name = request.session.get('guest_first_name', 'John')
                                self.last_name = request.session.get('guest_last_name', 'Doe')
                                self.line1 = '123 Test Street'
                                self.line4 = 'Test City'
                                self.postcode = 'GU7 2QG'
                                self.country = 'United Kingdom'
                                self.phone_number = request.session.get('guest_phone_number')
                                self.notes = ''

                            @property
                            def active_address_fields(self):
                                fields = []
                                if self.first_name and self.last_name:
                                    fields.append(f"{self.first_name} {self.last_name}")
                                if self.line1:
                                    fields.append(self.line1)
                                if self.line4:
                                    fields.append(self.line4)
                                if self.postcode:
                                    fields.append(self.postcode)
                                if self.country:
                                    fields.append(self.country)
                                return fields

                        self.shipping_address = MockShippingAddress()
                    else:
                        self.shipping_address = None

                    # Mock billing address (same as shipping for simplicity)
                    self.billing_address = self.shipping_address

                    # Mock payment sources
                    class MockSource:
                        def __init__(self, amount, currency):
                            self.amount_allocated = amount
                            self.currency = currency
                            self.source_type = type('MockSourceType', (), {'name': 'Test Payment'})()

                    class MockSources:
                        def __init__(self, amount, currency):
                            self._sources = [MockSource(amount, currency)]

                        def all(self):
                            return self._sources

                    self.sources = MockSources(self.total_incl_tax, self.currency)

                    # Mock order lines (basket items)
                    class MockLine:
                        def __init__(self, name, quantity, price, currency):
                            # Create mock product with proper image handling
                            class MockProduct:
                                def __init__(self):
                                    self.title = name
                                    self.primary_image = None  # No image for test products

                                def get_absolute_url(self):
                                    return '#'  # Placeholder URL for test

                            self.product = MockProduct()
                            self.product_title = name  # Template uses line.product_title
                            self.quantity = quantity
                            self.line_price_before_discounts_incl_tax = price
                            self.line_price_before_discounts_excl_tax = price

                            # Mock attributes for template
                            class MockAttributes:
                                def exists(self):
                                    return False

                            self.attributes = MockAttributes()
                            self.attribute_values = []

                    class MockLines:
                        def __init__(self, total_price, currency):
                            self._lines = [MockLine('Test Product', 1, total_price, currency)]

                        def all(self):
                            return self._lines

                    self.lines = MockLines(self.total_incl_tax, self.currency)

                    # Verification hash for order tracking
                    self.verification_hash = 'test-hash-123'

                    self.is_test = True

                def __str__(self):
                    return f"Order {self.number}"

            ctx['order'] = MockOrder(self.request)
            ctx['is_test_order'] = True

            # Add customer email for test orders
            if not ctx.get('customer_email'):
                if self.request.user.is_authenticated:
                    ctx['customer_email'] = self.request.user.email
                else:
                    ctx['customer_email'] = self.request.session.get('guest_email', 'test@example.com')

        return ctx


class TestThankYouView(CheckoutSessionMixin, generic.RedirectView):
    """
    Test view to simulate order completion and redirect to thank you page
    """
    def get_redirect_url(self, *args, **kwargs):
        # Set a test order number in session
        self.request.session['checkout_order_number'] = 'TEST-12345'
        # Add test mode parameter
        return reverse('checkout:thank-you') + '?test_mode=1'


class CustomPayPalRedirectView(PayPalRedirectView):
    """
    Custom PayPal redirect view that respects delivery type for collection orders
    """

    def get_shipping_address(self, basket=None):
        """Get shipping address from session"""
        # For collection orders, we don't need a shipping address
        delivery_type = self.request.session.get('delivery_type', 'delivery')
        if delivery_type == 'collection':
            return None

        # For delivery orders, we need to get the shipping address even if basket doesn't require shipping
        # This is because our delivery type logic overrides the basket's shipping requirement
        from oscar.core.loading import get_model
        ShippingAddress = get_model("order", "ShippingAddress")

        # Check if we have shipping address data in session
        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)

        # Check if user selected an existing address
        addr_id = self.checkout_session.shipping_user_address_id()
        if addr_id:
            try:
                UserAddress = get_model("address", "UserAddress")
                address = UserAddress._default_manager.get(pk=addr_id)
                # Copy user address data into a blank shipping address instance
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr
            except UserAddress.DoesNotExist:
                return None

        return None

    def build_submission(self, **kwargs):
        """Override to handle delivery type specific requirements"""
        delivery_type = self.request.session.get('delivery_type', 'delivery')

        # For collection orders, ensure we have NoShippingRequired method
        if delivery_type == 'collection':
            if not self.checkout_session.is_shipping_method_set(self.request.basket):
                self.checkout_session.use_shipping_method(NoShippingRequired().code)

        # Call parent build_submission
        return super().build_submission(**kwargs)

    def get_redirect_url(self, **kwargs):
        """Override to handle collection delivery type"""
        # Check delivery type and prepare session data BEFORE any PayPal operations
        delivery_type = self.request.session.get('delivery_type', 'delivery')

        # Ensure proper setup based on delivery type
        if delivery_type == 'collection':
            # For collection orders, ensure NoShippingRequired is set
            self.checkout_session.use_shipping_method(NoShippingRequired().code)
        else:
            # For delivery orders, ensure shipping method is set
            if not self.checkout_session.is_shipping_method_set(self.request.basket):
                shipping_address = self.get_shipping_address(self.request.basket)
                if shipping_address:
                    # Get available shipping methods for this address
                    repository = Repository()
                    methods = repository.get_available_shipping_methods(
                        basket=self.request.basket,
                        shipping_addr=shipping_address,
                        user=self.request.user,
                        request=self.request
                    )
                    # Use the first available delivery method (not self-collection)
                    delivery_method = None
                    for method in methods:
                        if method.code == 'delivery':
                            delivery_method = method
                            self.checkout_session.use_shipping_method(method.code)
                            break

                    if not delivery_method:
                        # No delivery method found - create a default one for PayPal
                        # This handles cases where postcode data is missing
                        from apps.shipping.methods import Standard
                        default_method = Standard(shipping_address)
                        self.checkout_session.use_shipping_method(default_method.code)
                else:
                    # No shipping address, redirect to shipping address page
                    messages.error(self.request, _("Please complete your shipping address first"))
                    return reverse('checkout:shipping-address')

        # Now try to proceed with PayPal
        try:
            basket = self.build_submission()['basket']
            url = self._get_redirect_url(basket, **kwargs)

            # Transaction successfully registered with PayPal
            basket.freeze()
            return url

        except PayPalError as ppe:
            messages.error(self.request, str(ppe))
            if self.as_payment_method:
                return reverse('checkout:payment-details')
            else:
                return reverse('basket:summary')
        except InvalidBasket as e:
            messages.warning(self.request, str(e))
            return reverse('basket:summary')
        except EmptyBasketException:
            messages.error(self.request, _("Your basket is empty"))
            return reverse('basket:summary')
        except Exception as e:
            # Generic error handler - log the error and redirect appropriately
            messages.error(self.request, _("Unable to process PayPal payment. Please try again."))
            if self.as_payment_method:
                return reverse('checkout:payment-details')
            else:
                return reverse('basket:summary')