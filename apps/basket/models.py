from django.db import models
from oscar.apps.basket.abstract_models import AbstractBasket, AbstractLine, Unavailable
from django.utils.translation import gettext_lazy as _
from apps.catalogue.models import Option
from oscar.templatetags.currency_filters import currency
from django.utils.encoding import smart_str

from apps.catalogue.models import AttributeOption


class Basket(AbstractBasket):
    def add_product(self, product, quantity=1, options=None):
        """
        Add a product to the basket

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value
        respectively.

        Returns (line, created).
          line: the matching basket line
          created: whether the line was created or updated

        """
        if options is None:
            options = []
        if not self.id:
            self.save()

        # Ensure that all lines are the same currency
        price_currency = self.currency
        stock_info = self.get_stock_info(product, options)

        if not stock_info.price.exists:
            raise ValueError("Strategy hasn't found a price for product %s" % product)

        if price_currency and stock_info.price.currency != price_currency:
            raise ValueError(
                (
                    "Basket lines must all have the same currency. Proposed "
                    "line has currency %s, while basket has currency %s"
                )
                % (stock_info.price.currency, price_currency)
            )

        if stock_info.stockrecord is None:
            raise ValueError(
                (
                    "Basket lines must all have stock records. Strategy hasn't "
                    "found any stock record for product %s"
                )
                % product
            )

        # Line reference is used to distinguish between variations of the same
        # product (eg T-shirts with different personalisations)
        line_ref = self._create_line_reference(product, stock_info.stockrecord, options)

        # Determine price to store (if one exists).  It is only stored for
        # audit and sometimes caching.
        price_include_tax = price_exclude_tax = stock_info.price.excl_tax
        if stock_info.price.is_tax_known:
            price_include_tax = stock_info.price.incl_tax
        extra_price = 0
        for option in options:
            if option["option"].type in [Option.RADIO, Option.SELECT]:
                att_opt = AttributeOption.objects.get(group=option["option"].option_group, key=option["value"])
                if att_opt.price:
                    extra_price += att_opt.price


            # if option is multiple select, option["value"] will be a list of values
            if option["option"].type in [Option.CHECKBOX, Option.MULTI_SELECT] and isinstance(option["value"], list):
                for value in option["value"]:
                    att_opt = AttributeOption.objects.get(group=option["option"].option_group, key=value)
                    if att_opt.price:
                        extra_price += att_opt.price

        price_exclude_tax += extra_price
        price_include_tax += extra_price
        defaults = {
            "quantity": quantity,
            "price_excl_tax": price_exclude_tax,
            "price_currency": stock_info.price.currency,
            "tax_code": stock_info.price.tax_code,
            "price_incl_tax": price_include_tax,
            "extra_price": extra_price
        }

        line, created = self.lines.get_or_create(
            line_reference=line_ref,
            product=product,
            stockrecord=stock_info.stockrecord,
            defaults=defaults,
        )
        if created:
            for option_dict in options:
                line.attributes.create(
                    option=option_dict["option"], value=option_dict["value"]
                )
        else:
            line.quantity = max(0, line.quantity + quantity)
            line.save()
        self.reset_offer_applications()

        # Returning the line is useful when overriding this method.
        return line, created

    add_product.alters_data = True
    add = add_product


class Line(AbstractLine):
    extra_price = models.DecimalField(_("Extra Price"), decimal_places=2, max_digits=12, blank=True, default=0)

    @property
    def unit_price_excl_tax(self):
        return self.purchase_info.price.excl_tax + self.extra_price

    @property
    def unit_price_incl_tax(self):
        return self.purchase_info.price.incl_tax + self.extra_price
    
    @property
    def product_title(self):
        return smart_str(self.product)
    
    @property
    def attribute_values(self):
        values = self.attributes.values_list("value", flat=True)
        flat_values = []
        for value in values:
            if isinstance(value, list):
                for v in value:
                    flat_values.append(v)
            else:
                flat_values.append(value)
        return flat_values

    def get_warning(self):
        """
        Return a warning message about this basket line if one is applicable

        This could be things like the price has changed
        """
        if isinstance(self.purchase_info.availability, Unavailable):
            msg = "'%(product)s' is no longer available"
            return _(msg) % {"product": self.product.get_title()}

        if not self.price_incl_tax:
            return
        if not self.purchase_info.price.is_tax_known:
            return

        # Compare current price to price when added to basket
        current_price_incl_tax = self.unit_price_incl_tax
        if current_price_incl_tax != self.price_incl_tax:
            product_prices = {
                "product": self.product.get_title(),
                "old_price": currency(self.price_incl_tax, self.price_currency),
                "new_price": currency(current_price_incl_tax, self.price_currency),
            }
            if current_price_incl_tax > self.price_incl_tax:
                warning = _(
                    "The price of '%(product)s' has increased from"
                    " %(old_price)s to %(new_price)s since you added"
                    " it to your basket"
                )
                return warning % product_prices
            else:
                warning = _(
                    "The price of '%(product)s' has decreased from"
                    " %(old_price)s to %(new_price)s since you added"
                    " it to your basket"
                )
                return warning % product_prices


from oscar.apps.basket.models import *
