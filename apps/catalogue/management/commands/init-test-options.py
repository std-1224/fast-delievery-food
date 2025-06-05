from django.core.management.base import BaseCommand, CommandError
from oscar.apps.catalogue.models import AttributeOptionGroup
from apps.catalogue.models import AttributeOption

class Command(BaseCommand):
    def handle(self, *args, **options):
        sugar = AttributeOptionGroup.objects.create(name='Sugar1')
        ice = AttributeOptionGroup.objects.create(name='Ice1')
        
        
        AttributeOption.objects.create(group=sugar, option='No sugar')
        AttributeOption.objects.create(group=sugar, option='50%')
        AttributeOption.objects.create(group=sugar, option='75%')
        AttributeOption.objects.create(group=sugar, option='100%')
        
        AttributeOption.objects.create(group=ice, option='No ice')
        AttributeOption.objects.create(group=ice, option='Cubed')
        AttributeOption.objects.create(group=ice, option='Crushed')
        AttributeOption.objects.create(group=ice, option='Shaved')
        
        