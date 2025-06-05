import distutils
from decimal import Decimal as D

from import_export import resources
from import_export.admin import ImportMixin
from import_export.fields import Field
from import_export.widgets import CharWidget, BooleanWidget
from oscar.apps.catalogue.admin import *
from oscar.apps.catalogue.categories import create_from_breadcrumbs

from apps.catalogue.import_widgets import RequiredCharWidget, PositiveDecimalWidget

Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")

admin.site.unregister(AttributeOptionGroup)
admin.site.unregister(Product)


class ProductResource(resources.ModelResource):
    product_type = Field(attribute='product_type', column_name='Product Type',
                         widget=RequiredCharWidget(allow_blank=False), )
    upc = Field(attribute='upc', column_name='UPC', widget=RequiredCharWidget())
    category = Field(attribute='category', column_name='Category', widget=RequiredCharWidget(allow_blank=False))
    category_description = Field(attribute='category_description', column_name='Category Description',
                                 widget=CharWidget())
    title = Field(attribute='title', column_name='Title', widget=RequiredCharWidget(allow_blank=False))
    description = Field(attribute='description', column_name='Description', widget=CharWidget())
    partner_name = Field(attribute='partner_name', column_name='Partner Name',
                         widget=RequiredCharWidget(allow_blank=False))
    partner_sku = Field(attribute='partner_sku', column_name='Partner SKU',
                        widget=RequiredCharWidget(allow_blank=False))
    price = Field(attribute='price', column_name='Price', widget=PositiveDecimalWidget())

    # Options
    option_group = Field(attribute='option_group', column_name='Option Group', widget=CharWidget())
    option = Field(attribute='option', column_name='Option', widget=CharWidget())
    allow_multiple = Field(attribute='allow_multiple', column_name='Allow Multiple', widget=BooleanWidget())
    option_required = Field(attribute='option_required', column_name='Option Required', widget=BooleanWidget())

    option_price = Field(attribute='option_price', column_name='Option Price',
                         widget=PositiveDecimalWidget(allow_blank=True))

    def before_save_instance(self, instance, row, **kwargs):
        product_type = row["Product Type"]
        product_class, _ = ProductClass.objects.get_or_create(name=product_type, track_stock=False)
        instance.product_class = product_class

    def after_save_instance(self, instance, row, **kwargs):
        category = row["Category"]
        category_description = row["Category Description"]
        partner_name = row["Partner Name"]
        partner_sku = row["Partner SKU"]
        price = row["Price"]

        option_group = row["Option Group"]
        option = row["Option"]
        option_price = row["Option Price"] or 0
        allow_multiple = bool(distutils.util.strtobool(row["Allow Multiple"])) if row["Allow Multiple"] else False
        option_required = bool(distutils.util.strtobool(row["Option Required"])) if row["Option Required"] else False

        if option_group and option:
            option_group_obj, _ = AttributeOptionGroup.objects.get_or_create(name=option_group)
            attribute_option_obj, _ = AttributeOption.objects.get_or_create(group=option_group_obj, option=option)
            attribute_option_obj.price = option_price
            attribute_option_obj.save()

            option_obj, _ = Option.objects.get_or_create(name=option_group, option_group=option_group_obj)
            option_obj.required = option_required
            option_obj.type = Option.CHECKBOX if allow_multiple else Option.RADIO
            option_obj.save()
            instance.product_options.add(option_obj)

        cat = create_from_breadcrumbs(category)
        cat.description = category_description
        cat.save()

        ProductCategory.objects.update_or_create(product=instance, category=cat)

        partner, _ = Partner.objects.get_or_create(name=partner_name)
        try:
            stock = StockRecord.objects.get(partner_sku=partner_sku)
        except StockRecord.DoesNotExist:
            stock = StockRecord()

        stock.product = instance
        stock.partner = partner
        stock.partner_sku = partner_sku
        stock.price = D(price)
        stock.save()

    class Meta:
        model = Product
        skip_diff = True

        import_id_fields = ('upc',)
        fields = (
            'product_type', 'category', 'upc', 'title', 'description', 'partner_name',
            'partner sku', 'price',
            'option_group', 'option', 'option_price', 'allow_multiple', 'option_required')


class ProductImportAdmin(ImportMixin, ProductAdmin):
    resource_classes = [ProductResource]


class AttributeOptionCustomInline(admin.TabularInline):
    model = AttributeOption
    readonly_fields = ["key"]


class AttributeOptionGroupCustomAdmin(admin.ModelAdmin):
    list_display = ("name", "option_summary")
    inlines = [
        AttributeOptionCustomInline,
    ]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        for formset in formsets:
            for form in formset:
                # Here you get each instance of the inline model.
                # You can now perform custom save operations.
                if form.instance and form.is_valid():
                    option = form.instance
                    # Custom logic here.
                    # For example, you can modify a field:
                    # book.title = book.title.upper()
                    # option.save()


admin.site.register(AttributeOptionGroup, AttributeOptionGroupCustomAdmin)

admin.site.register(Product, ProductImportAdmin)
