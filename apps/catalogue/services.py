from apps.catalogue.models import Product


def get_products(title):
    return Product.objects.filter(title__icontains=title)
