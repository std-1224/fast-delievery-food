from oscarapi.views import product
from oscar.core.loading import get_model
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

class CustomLimitOffsetPagination(PageNumberPagination):
    page_size_query_param = 'limit'

Category = get_model('catalogue', 'Category')

class ProductList(product.ProductList):
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        qs = super().get_queryset()
        structure = self.request.query_params.get("structure")
        category_id = self.request.query_params.get("category_id")
        search = self.request.query_params.get("search", "")

        print(f"Search param: '{search}'")
        print(f"Category ID: '{category_id}'")
        print(f"query.params: {self.request.query_params}")
        filters = {}

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                descendants = category.get_descendants()
                category_ids = [category.id] + list(descendants.values_list('id', flat=True))
                filters['categories__id__in'] = category_ids
            except Category.DoesNotExist:
                return qs.none()
        else:
            categories = Category.objects.filter(depth=1, numchild__gt=0).all()
            category_ids = list(categories.values_list('id', flat=True))
            filters['categories__id__in'] = category_ids

        if structure:
            filters['structure'] = structure

        qs = qs.filter(**filters).distinct()

        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return qs