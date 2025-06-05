import oscar.apps.order.apps as apps


class OrderConfig(apps.OrderConfig):
    name = 'apps.order'

    def ready(self):
        # noinspection PyUnresolvedReferences
        import apps.order.signals
