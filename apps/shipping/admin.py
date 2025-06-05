from django.contrib import admin
from django import forms

from .models import ShippingZone, Postcode

class ShippingZoneForm(forms.ModelForm):
    postcodes = forms.CharField(widget=forms.Textarea, help_text="Enter postcodes separated by commas.")

    class Meta:
        model = ShippingZone
        fields = ['name', 'shipping_price', 'postcodes']

    def __init__(self, *args, **kwargs):
        super(ShippingZoneForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            postcodes = Postcode.objects.filter(shipping_zone=self.instance)
            self.fields['postcodes'].initial = ', '.join([postcode.code for postcode in postcodes])

class ShippingZoneAdmin(admin.ModelAdmin):
    form = ShippingZoneForm

    def save_model(self, request, obj, form, change):
        # Save the ShippingZone instance
        obj.save()

        # Handle postcodes
        postcodes = form.cleaned_data['postcodes']
        postcode_list = [code.replace(" ", "").upper() for code in postcodes.split(',') if code.replace(" ", "")]

        # Fetch existing postcodes related to the shipping zone
        current_postcodes = set(Postcode.objects.filter(shipping_zone=obj).values_list('code', flat=True))
        incoming_postcodes = set(postcode_list)

        # Postcodes to add to the current shipping zone
        postcodes_to_update = incoming_postcodes - current_postcodes
        postcodes_to_remove = current_postcodes - incoming_postcodes

        # Update or create postcodes and move them to the new zone if needed
        Postcode.objects.filter(code__in=postcodes_to_update).update(shipping_zone=obj)

        # Delete postcodes that are no longer associated with the shipping zone
        Postcode.objects.filter(code__in=postcodes_to_remove, shipping_zone=obj).delete()

        # Create new postcodes for codes that do not exist at all
        existing_postcodes = set(Postcode.objects.filter(code__in=postcode_list).values_list('code', flat=True))
        postcodes_to_create = incoming_postcodes - existing_postcodes
        new_postcodes = [Postcode(code=code, shipping_zone=obj) for code in postcodes_to_create]
        Postcode.objects.bulk_create(new_postcodes)

admin.site.register(ShippingZone, ShippingZoneAdmin)
admin.site.register(Postcode)