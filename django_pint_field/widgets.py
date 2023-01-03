import pint
from django.forms.widgets import MultiWidget, NumberInput, Select

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

        return [(str(ureg(x).units), x) for x in unit_choices]

    def decompress(self, value):
        """
        This function is called during rendering

        It is responsible for splitting values for the two widgets
        """
        if isinstance(value, pint.Quantity):
            return [value.magnitude, value.units]

        return [None, self.default_unit]
