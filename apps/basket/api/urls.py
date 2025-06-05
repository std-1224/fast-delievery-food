from django.urls import path

from apps.basket.api import views

urlpatterns = [
    path("basket-add/", views.CustomBasketAddView.as_view(), name="add basket"),
]