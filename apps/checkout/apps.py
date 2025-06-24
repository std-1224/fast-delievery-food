import oscar.apps.checkout.apps as apps


class CheckoutConfig(apps.CheckoutConfig):
    name = 'apps.checkout'

    def ready(self):
        super().ready()

    def get_urls(self):
        from .urls import urlpatterns
        return self.post_process_urls(urlpatterns)