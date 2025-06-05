from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from oscar.apps.checkout import exceptions
from oscar.apps.checkout.session import CheckoutSessionMixin as CoreCheckoutSessionMixin


class CheckoutSessionMixin(CoreCheckoutSessionMixin):
    def check_user_email_is_captured(self, request):
        if (
                not request.user.is_authenticated
                and not self.checkout_session.get_guest_email()
                and not self.checkout_session.get_guest_phone_number()
        ):
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:index"),
                message=_("Please either sign in or enter your email address"),
            )

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
