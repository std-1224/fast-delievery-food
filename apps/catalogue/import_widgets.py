from decimal import InvalidOperation

from import_export.widgets import IntegerWidget, CharWidget, DecimalWidget


class PositiveDecimalWidget(DecimalWidget):
    def __init__(self, coerce_to_string=True, allow_blank=True):
        self.allow_blank = allow_blank
        super().__init__(coerce_to_string)

    def clean(self, value, row=None, **kwargs):
        try:
            val = super().clean(value, row=row, **kwargs)
        except (ValueError, TypeError, InvalidOperation):
            # Raise a validation error if the value is not numeric
            raise ValueError("value is not a valid number")

        if not self.allow_blank and not val:
            raise ValueError("value must be provide")
        if val and val < 0:
            raise ValueError("value must be positive")
        return val


class PositiveIntegerWidget(IntegerWidget):
    def __init__(self, coerce_to_string=True, allow_blank=True):
        self.allow_blank = allow_blank
        super().__init__(coerce_to_string)

    def clean(self, value, row=None, **kwargs):
        try:
            val = super().clean(value, row=row, **kwargs)
        except (ValueError, TypeError, InvalidOperation):
            # Raise a validation error if the value is not numeric
            raise ValueError("value is not a valid number")

        if self.allow_blank and not val:
            raise ValueError("value must be provide")
        if val and val < 0:
            raise ValueError("value must be positive")
        return val


class RequiredCharWidget(CharWidget):
    """Returns a positive integer value"""

    def clean(self, value, row=None, **kwargs):
        val = super().clean(value, row=row, **kwargs)
        if not val:
            raise ValueError("value must be provide")
        return val
