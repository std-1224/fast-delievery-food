from django.urls import path

from apps.custom_api.views.admin.order import OrderStatusUpdateView, AllowedOrderStatusView, OrderIdsAdminList, \
    TestConnectionView
from apps.custom_api.views.location_views import PostcodeAutocompleteView

urlpatterns = [
    path('admin/orders/list-ids/', OrderIdsAdminList.as_view(), name='order-ids-list'),
    path('admin/orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('admin/orders/<int:pk>/allowed-statuses/', AllowedOrderStatusView.as_view(), name='allowed-order-statuses'),
    path('admin/orders/ping/', TestConnectionView.as_view(), name='test-connection'),
    path('postcode-autocomplete/', PostcodeAutocompleteView.as_view(), name='postcode-autocomplete'),
]
