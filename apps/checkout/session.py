from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from oscar.apps.checkout import exceptions
from oscar.apps.checkout.session import CheckoutSessionMixin as CoreCheckoutSessionMixin
from oscar.core.loading import get_class

CheckoutSessionData = get_class("checkout.utils", "CheckoutSessionData")


class CheckoutSessionMixin(CoreCheckoutSessionMixin):

    @property
    def checkout_session(self):
        """
        Return the checkout session manager
        """
        if not hasattr(self, '_checkout_session'):
            self._checkout_session = CheckoutSessionData(self.request)
        return self._checkout_session

    @checkout_session.setter
    def checkout_session(self, value):
        """
        Allow setting the checkout session
        """
        self._checkout_session = value
    def check_user_email_is_captured(self, request):
        # For authenticated users, email is already captured from their account
        if request.user.is_authenticated:
            return None

        # For guest users, check if email is captured
        if (
                not self.checkout_session.get_guest_email()
                and not self.checkout_session.get_guest_phone_number()
        ):
            # Return a redirect response instead of raising an exception
            # This allows the PreviewView.dispatch() method to handle it properly
            return redirect('checkout:index')

        return None

    def build_submission(self, **kwargs):
        submission = super().build_submission(**kwargs)
        user = submission["user"]
        if (
                not user.is_authenticated
                and "guest_phone_number" not in submission["order_kwargs"]
        ):
            phone_number = self.checkout_session.get_guest_phone_number()
            first_name = self.checkout_session.get_guest_first_name()
            last_name = self.checkout_session.get_guest_last_name()
            submission["order_kwargs"]["guest_phone_number"] = phone_number
            submission["order_kwargs"]["guest_first_name"] = first_name
            submission["order_kwargs"]["guest_last_name"] = last_name
        return submission
