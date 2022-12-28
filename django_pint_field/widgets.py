from django.forms.widgets import MultiWidget, NumberInput, Select

import pint
from numbers import Number

from .units import ureg


class QuantityWidget(MultiWidget):
    def __init__(self, *, attrs=None, base_units=None, allowed_types=None):
        self.ureg = ureg
        choices = self.get_choices(allowed_types)
        self.base_units = base_units
        attrs = attrs or {}
        attrs.setdefault("step", "any")
        widgets = (NumberInput(attrs=attrs), Select(attrs=attrs, choices=choices))
        super(QuantityWidget, self).__init__(widgets, attrs)

    def get_choices(self, allowed_types=None):
        allowed_types = allowed_types or dir(self.ureg)
        return [(x, x) for x in allowed_types]

    def decompress(self, value):
        """This function is called during rendering

        It is responsible to split values for the two widgets
        """
        if isinstance(value, Number):
            # We assume that the given value is a proper number,
            # ready to be rendered
            return [value, self.base_units]
        elif isinstance(value, pint.Quantity):
            return [value.magnitude, value.units]

        return [None, self.base_units]
