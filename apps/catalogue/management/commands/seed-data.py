from django.core.management.base import BaseCommand, CommandError
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.catalogue.models import AttributeOptionGroup
from oscar.apps.partner.models import StockRecord
from apps.catalogue.models import AttributeOption, ProductClass, Product, Option, Category

class Command(BaseCommand):
    def handle(self, *args, **options):
        salad = AttributeOptionGroup.objects.create(name='Salad')
        sauce = AttributeOptionGroup.objects.create(name='Sauce')
        drink = AttributeOptionGroup.objects.create(name='Drink')
        extra = AttributeOptionGroup.objects.create(name='Extras')
        extra2 = AttributeOptionGroup.objects.create(name='Extras2')
        
        
        AttributeOption.objects.create(group=salad, option='Salad 1')
        AttributeOption.objects.create(group=salad, option='Salad 2')
        AttributeOption.objects.create(group=salad, option='Salad 3')
        AttributeOption.objects.create(group=salad, option='Salad 4')
        
        AttributeOption.objects.create(group=sauce, option='BBQ Sauce')
        AttributeOption.objects.create(group=sauce, option='Honey Mustard')
        AttributeOption.objects.create(group=sauce, option='Garlic Sauce')
        AttributeOption.objects.create(group=sauce, option='Chilli Sauce')

        AttributeOption.objects.create(group=drink, option='Coke', price=1)
        AttributeOption.objects.create(group=drink, option='Pepsi', price=1.1)
        AttributeOption.objects.create(group=drink, option='Fanta', price=1.2)
        AttributeOption.objects.create(group=drink, option='Sprite', price=1.3)

        AttributeOption.objects.create(group=extra, option='Cheese', price=1)
        AttributeOption.objects.create(group=extra, option='Bacon', price=1.1)
        AttributeOption.objects.create(group=extra, option='Egg', price=1.2)
        AttributeOption.objects.create(group=extra, option='Onion Rings', price=1.3)
        AttributeOption.objects.create(group=extra, option='Fries', price=1.4)
        AttributeOption.objects.create(group=extra, option='Bread', price=1.5)
        AttributeOption.objects.create(group=extra, option='Chips', price=1.6)
        AttributeOption.objects.create(group=extra, option='Mash', price=1.7)
        AttributeOption.objects.create(group=extra, option='Gravy', price=1.8)
        AttributeOption.objects.create(group=extra, option='Corn', price=1.9)
        
        
        AttributeOption.objects.create(group=extra2, option='Cheese', price=1)
        AttributeOption.objects.create(group=extra2, option='Bacon', price=1.1)
        AttributeOption.objects.create(group=extra2, option='Egg', price=1.2)
        AttributeOption.objects.create(group=extra2, option='Onion Rings', price=1.3)
        AttributeOption.objects.create(group=extra2, option='Fries', price=1.4)
        AttributeOption.objects.create(group=extra2, option='Bread', price=1.5)
        AttributeOption.objects.create(group=extra2, option='Chips', price=1.6)
        AttributeOption.objects.create(group=extra2, option='Mash', price=1.7)

        salad_option = Option.objects.create(name='Salad', option_group=salad, required=True, type=Option.SELECT)
        sauce_option = Option.objects.create(name='Sauce', option_group=sauce, required=True, type=Option.CHECKBOX)
        drink_option = Option.objects.create(name='Drink', option_group=drink, required=True, type=Option.CHECKBOX)
        extra_option = Option.objects.create(name='Extras', option_group=extra, required=False, type=Option.MULTI_SELECT)
        extra2_option = Option.objects.create(name='Extras', option_group=extra2, required=False, type=Option.RADIO)
        text_option = Option.objects.create(name='Text type', required=False, type=Option.TEXT)
        integer_option = Option.objects.create(name='Integer type', required=False, type=Option.INTEGER)
        float_option = Option.objects.create(name='Float type', required=False, type=Option.FLOAT)
        boolean_option = Option.objects.create(name='Boolean type', required=False, type=Option.BOOLEAN)
        date_option = Option.objects.create(name='Date type', required=False, type=Option.DATE)
        
        fast_food = ProductClass.objects.create(name='Fast Food', track_stock=False)
        fast_food.options.set([salad_option, sauce_option, drink_option, extra_option, extra2_option, text_option, integer_option, float_option, boolean_option, date_option])
        categories = [create_from_breadcrumbs(f'Category {i}') for i in range(20)]
        
        products = []
        stock_records = []
        for i in range(20):
            product = Product(
                title='Product' + str(i),
                product_class=fast_food,
            )
            products.append(product)
            stock_records.append(StockRecord(partner_id=1, product=product, partner_sku='sku' + str(i), price=100 + i))
            
        [product.save() for product in products]
        [stock_record.save() for stock_record in stock_records]
        for i in range(len(products)):
            products[i].categories.set([categories[i % len(categories)]])
            

                
        
        