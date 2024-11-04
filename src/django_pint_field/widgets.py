"""Widgets for django_pint_field."""

from decimal import Decimal
from typing import List, Optional, Tuple, Union

import pint
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import MultiWidget, NumberInput, Select

from .units import ureg


class PintFieldWidget(MultiWidget):
    """Widget for PintField."""

    def __init__(
        self, *, attrs: Optional[dict] = None, default_unit: str = None, unit_choices: List[str] = None, **kwargs
    ):
        """Initializes the PintFieldWidget.

        Args:
            attrs (dict): The attributes to apply to the widget.
            default_unit (str): The default unit to use.
            unit_choices (list): The list of unit choices.
        """
        self.ureg = ureg

        if default_unit is None:
            raise ValueError(
                "PintFieldWidget and TabledPintFieldWidget require a default_unit kwarg of a single Pint unit type (eg: 'grams')"
            )
        self.default_unit = default_unit

        unit_choices = unit_choices or [self.default_unit]
        if self.default_unit not in unit_choices:
            unit_choices.append(self.default_unit)
        self.choices = [(str(self.ureg(x).units), x) for x in unit_choices]

        attrs = attrs or {}
        attrs.setdefault("step", "any")
        widgets = (NumberInput(attrs=attrs), Select(attrs=attrs, choices=self.choices))
        super().__init__(widgets, attrs)

    def decompress(self, value: Union[pint.Quantity, List[Union[float, str]]]) -> List[Union[Optional[float], str]]:
        """This function is called during rendering, and is responsible for splitting values for the two widgets."""
        if isinstance(value, pint.Quantity):
            return [value.magnitude, value.units]

        return [None, self.default_unit]


class TabledPintFieldWidget(PintFieldWidget):
    """Widget for PintField with a table of unit conversions."""

    template_name = "django_pint_field/tabled_django_pint_field_widget.html"

    def __init__(
        self, *, attrs: Optional[dict] = None, default_unit: str = None, unit_choices: List[str] = None, **kwargs
    ):
        """Initializes the TabledPintFieldWidget.

        Args:
            floatformat (int): The number of decimal places to display in the table.
            table_class (str): The class to apply to the table.
            td_class (str): The class to apply to the table data cells.

            Also inherits the args from PintFieldWidget.
        """
        self.floatformat = kwargs.pop("floatformat", 6)
        self.table_class = kwargs.pop("table_class", "p-5 m-5")
        self.td_class = kwargs.pop("td_class", "text-end")
        super().__init__(attrs=attrs, default_unit=default_unit, unit_choices=unit_choices)

    def create_table(self, value: ureg.Quantity = None):
        """Create a table of unit conversions."""
        values_list = []

        # if value is not None:
        if isinstance(value, self.ureg.Quantity):
            value_tuple = (str(value.units), str(value.units))

            if value_tuple in self.choices:
                self.choices.remove(value_tuple)

        for choice in self.choices:
            unit_output, unit_display = choice
            if value is not None:
                if isinstance(value, self.ureg.Quantity):
                    output_value = value.to(unit_output)
                elif isinstance(value, (int, float, Decimal)):
                    # Convert to a Quantity using ureg
                    output_value = self.ureg.Quantity(value * self.ureg[unit_output])
                else:
                    raise ImproperlyConfigured(
                        f"Incorrect value type of '{type(value)}' in create_table method of TabledPintFieldWidget"
                    )
            else:
                output_value = self.ureg.Quantity(0 * self.ureg[unit_output])
            values_list.append(output_value)
        return values_list

    def get_context(self, name: str, value: Optional[ureg.Quantity], attrs: dict):
        """Adds table of unit conversions to widget context."""

        context = super().get_context(name, value, attrs)
        context["values_list"] = self.create_table(value)
        context["floatformat"] = self.floatformat
        context["table_class"] = self.table_class
        context["td_class"] = self.td_class

        return context
