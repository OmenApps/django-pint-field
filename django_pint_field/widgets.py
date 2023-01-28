import pint
from decimal import Decimal
from django.forms.widgets import MultiWidget, NumberInput, Select
from django.core.exceptions import ImproperlyConfigured
from .units import ureg


class PintFieldWidget(MultiWidget):
    def __init__(self, *, attrs=None, default_unit=None, unit_choices=None):
        self.ureg = ureg
        self.default_unit = default_unit
        self.choices = self.get_choices(unit_choices)
        attrs = attrs or {}
        attrs.setdefault("step", "any")
        widgets = (NumberInput(attrs=attrs), Select(attrs=attrs, choices=self.choices))
        super().__init__(widgets, attrs)

    def get_choices(self, unit_choices=None):
        unit_choices = unit_choices or [
            self.default_unit,
        ]

        return [(str(self.ureg(x).units), x) for x in unit_choices]

    def decompress(self, value):
        """
        This function is called during rendering, and is responsible for splitting values for the two widgets
        """
        if isinstance(value, pint.Quantity):
            return [value.magnitude, value.units]

        return [None, self.default_unit]


class TabledPintFieldWidget(PintFieldWidget):
    template_name = "tabled_django_pint_field_widget.html"

    def create_table(self, value):
        values_list = []

        if value is not None:
            value_tuple = (str(value.units), str(value.units))

            if value_tuple in self.choices:
                self.choices.remove(value_tuple)

        for choice in self.choices:
            unit_output, unit_display = choice
            if value is not None:
                if isinstance(value, pint.Quantity):
                    output_value = value.to(unit_output)
                elif isinstance(value, (int, float, Decimal)):
                    # Convert to a Quantity using ureg
                    output_value = self.ureg.Quantity(value * self.ureg[unit_output])
                else:
                    raise ImproperlyConfigured(
                        f"Incorrect value type of '{type(value)}' in create_table method of TabledPintFieldWidget"
                    )
            else:
                output_value = 0
            values_list.append(output_value)
        return values_list

    def get_context(self, name, value, attrs):
        """Add table of unit conversions to widget context"""

        context = super().get_context(name, value, attrs)
        context["values_list"] = self.create_table(value)

        return context
