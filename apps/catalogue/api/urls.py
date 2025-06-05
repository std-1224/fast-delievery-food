from django.urls import path
from django.views.generic import TemplateView

from apps.catalogue.api import views

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list product"),
    path("detail/", views.ProductDetailView.as_view(), name="product detail"),
    path("option/", views.OptionListView.as_view(), name="product option"),
]