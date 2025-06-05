from django import template
from apps.catalogue.models import Category
from django.forms.models import model_to_dict

register = template.Library()

def build_tree(categories, parent_id=None, level=0):
    tree = []
    for category in categories:
        parent = category.get_parent()
        current_parent_id = parent.id if parent else None
        if current_parent_id == parent_id:
            children = build_tree(categories, parent_id=category.id, level=level+1)
            category_data = model_to_dict(category)
            category_data['url'] = category.get_absolute_url() if hasattr(category, 'get_absolute_url') else '#'
            tree.append({
                'category': category_data,
                'children': children,
                'level': level
            })
    return tree

@register.simple_tag
def category_tree():
    categories = Category.objects.filter(numchild__gt=0).all()
    return build_tree(categories)

@register.simple_tag(takes_context=True)
def sub_category_list(context):
    search_query = context['request'].GET.get('search', '')
    categories = Category.objects.filter(depth=2, numchild=0)
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    return categories