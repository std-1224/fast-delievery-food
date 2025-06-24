from oscar.apps.address.forms import UserAddressForm as BaseUserAddressForm
from oscar.core.loading import get_model

Country = get_model("address", "Country")


class UserAddressForm(BaseUserAddressForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adjust_country_field()
        self.adjust_postcode_field()

    def adjust_country_field(self):
        countries = Country._default_manager.filter(is_shipping_country=True)

        # No need to show country dropdown if there is only one option
        if len(countries) == 1:
            self.fields.pop("country", None)
            self.instance.country = countries[0]
        else:
            self.fields["country"].queryset = countries
            self.fields["country"].empty_label = None

    def adjust_postcode_field(self):
        self.fields["postcode"].label = "Postcode"

    def clean_postcode(self):
        # Accept any postcode, no validation
        return self.cleaned_data.get('postcode')

    def clean(self):
        # Override the parent clean method to skip postcode validation
        cleaned_data = super().clean()
        # Remove any postcode validation errors
        if 'postcode' in self.errors:
            del self.errors['postcode']
        return cleaned_data

    class Meta(BaseUserAddressForm.Meta):
        fields = [
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line4",
            "postcode",
            "country",
            "phone_number",
            "notes",
        ]
