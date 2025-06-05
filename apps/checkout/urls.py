 # apps/checkout/urls.py
from django.urls import path, re_path
from oscar.core.application import Application
# Import views from your local app, where we will override them
from apps.checkout import views

class CheckoutApplication(Application):
    name = 'checkout'
    # Reference the views from your local app
    index_view = views.IndexView
    shipping_address_view = views.ShippingAddressView
    # shipping_method_view is removed
    payment_method_view = views.PaymentMethodView
    payment_details_view = views.PaymentDetailsView
    preview_view = views.PreviewView
    thankyou_view = views.ThankYouView

    def get_urls(self):
        urls = [
            # Determine if the user is creating a new account, or using an
            # existing account or proceeding as a guest.
            path('', self.index_view.as_view(), name='index'),

            # Shipping address (only for delivery)
            path('shipping-address/', self.shipping_address_view.as_view(), name='shipping-address'),

            # Shipping method - REMOVED

            # Payment method (after preview)
            path('payment-method/', self.payment_method_view.as_view(), name='payment-method'),

            # Order preview (after information or shipping address)
            path('preview/', self.preview_view.as_view(), name='preview'),

            # Payment details
            path('payment-details/', self.payment_details_view.as_view(), name='payment-details'),

            # Thank you
            re_path(r'thank-you/(?P<order_number>[\w-]+)/$',
                    self.thankyou_view.as_view(), name='thank-you'),
        ]
        return urls

application = CheckoutApplication()
