from django.urls import path
from oscar.apps.checkout.apps import CheckoutConfig
from . import views

app_name = 'checkout'

urlpatterns = [
    # Gateway - First step for all orders
    path('', views.IndexView.as_view(), name='index'),

    # Shipping address - Only for delivery orders
    path('shipping-address/', views.ShippingAddressView.as_view(), name='shipping-address'),

    # Preview - Order summary (both collection and delivery)
    path('preview/', views.PreviewView.as_view(), name='preview'),

    # Payment details - Payment processing
    path('payment-details/', views.PaymentDetailsView.as_view(), name='payment-details'),

    # Custom PayPal payment - respects delivery type
    path('paypal/payment/', views.CustomPayPalRedirectView.as_view(as_payment_method=True),
         name='custom-paypal-direct-payment'),

    # Test thank you - For testing without payment
    path('test-thank-you/', views.TestThankYouView.as_view(), name='test-thank-you'),

    # Thank you - Order confirmation
    path('thank-you/', views.ThankYouView.as_view(), name='thank-you'),
]