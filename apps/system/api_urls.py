from django.urls import path

from .views import CreateDeviceView, SetDeviceKeyView, RetrieveDestroyDeviceView, SellerInfoView, ApproveDeviceView, \
    CreateDeviceNoCameraView, UpdateFirebaseTokenView

urlpatterns = [
    path('devices/', CreateDeviceView.as_view(), name='create-device-view'),
    path('devices/no-camera/', CreateDeviceNoCameraView.as_view(), name='create-device-no-camera-view'),
    path('devices/firebase-token/', UpdateFirebaseTokenView.as_view(), name='update-firebase-token-view'),
    path('devices/<uuid:pk>/device-key/', SetDeviceKeyView.as_view(), name='set-device-key-view'),
    path('devices/<uuid:pk>/approve/', ApproveDeviceView.as_view(), name='approve-device-view'),
    path('devices/<uuid:pk>/', RetrieveDestroyDeviceView.as_view(), name='retrieve-api-key-view'),
    path('seller/info', SellerInfoView.as_view(), name='retrieve-seller-info'),
]
