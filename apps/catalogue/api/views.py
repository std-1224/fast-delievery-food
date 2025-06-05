from oscar.apps.catalogue.models import ProductImage
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from apps.catalogue.models import Product, Option
from apps.catalogue.serializers import ProductSerializer, OptionSerializer


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Default page size


class ProductListView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related().all()
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = Product.objects.select_related().all()
        search = self.request.query_params.get('search', '')
        print(f"Search param: '{search}'")
        if search:
            queryset = queryset.filter(title__icontains=search)
        print(f"Products count: {queryset.count()}")
        return queryset

    def get(self, request, *args, **kwargs):
        self.pagination_class.page_size = int(
            self.request.query_params.get("limit", 10)
        )
        return self.list(request, *args, **kwargs)


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductSerializer

    def get_object(self):
        params = self.request.query_params
        return Product.objects.get(id=(params["id"]))


class OptionListView(ListAPIView):
    serializer_class = OptionSerializer
    queryset = Option.objects.all()
