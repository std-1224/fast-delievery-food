from oscar.apps.checkout.utils import CheckoutSessionData as CoreCheckoutSessionData


class CheckoutSessionData(CoreCheckoutSessionData):
    def set_guest_info(self, first_name, last_name, phone_number):
        self._set("guest", "first_name", first_name)
        self._set("guest", "last_name", last_name)
        self._set("guest", "phone_number", phone_number)

    def get_guest_phone_number(self):
        return self._get("guest", "phone_number")
    
    def get_guest_first_name(self):
        return self._get("guest", "first_name")
    
    def get_guest_last_name(self):
        return self._get("guest", "last_name")
