from django.forms.widgets import MultiWidget, NumberInput, Select

import pint

from .units import ureg


class PintFieldWidget(MultiWidget):
    def __init__(self, *, attrs=None, default_unit=None, unit_choices=None):
        self.ureg = ureg
        choices = self.get_choices(unit_choices)
        self.default_unit = default_unit
        attrs = attrs or {}
        attrs.setdefault("step", "any")
        widgets = (NumberInput(attrs=attrs), Select(attrs=attrs, choices=choices))
        super().__init__(widgets, attrs)

    def get_choices(self, unit_choices=None):
        unit_choices = unit_choices or dir(self.ureg)
        print(f"PintFieldWidget get_choices > unit_choices: {unit_choices}, type: {type(unit_choices)}")
        return [(x, x) for x in unit_choices]

    def decompress(self, value):
        """
        This function is called during rendering

        It is responsible for splitting values for the two widgets
        """
        print(f"PintFieldWidget decompress > value: {value}, type: {type(value)}")
        if isinstance(value, pint.Quantity):
            return [value.magnitude, value.units]

        return [None, self.default_unit]
