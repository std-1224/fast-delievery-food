from django import template

from apps.catalogue.services import get_products
register = template.Library()


@register.simple_tag(takes_context=True)
def get_product(context):
    search_query = context['request'].GET.get('search', '')
    result = get_products(search_query)
    return result




