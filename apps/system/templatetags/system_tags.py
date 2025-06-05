from django import template

from apps.system.serializers import SystemSerializer, MenuSerializer, SliderSerializer
from apps.system.services import get_system_config, get_menu_config, get_sliders

register = template.Library()


@register.simple_tag
def get_system():
    return SystemSerializer(get_system_config()).data


@register.simple_tag
def get_menu():
    return MenuSerializer(get_menu_config(), many=True).data


@register.simple_tag
def get_slider():
    slider_data = SliderSerializer(get_sliders(), many=True).data
    return list(enumerate(slider_data, start=0))
