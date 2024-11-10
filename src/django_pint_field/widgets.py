"""Widgets for django_pint_field."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.forms.widgets import MultiWidget
from django.forms.widgets import NumberInput
from django.forms.widgets import Select

from .helpers import is_decimal_or_int
from .units import ureg


Quantity = ureg.Quantity
Unit = ureg.Unit


class PintFieldWidget(MultiWidget):
    """Widget for PintField."""

    def __init__(self, *, attrs: Optional[dict] = None, default_unit: str = None, unit_choices: list[str] = None):
        """Initializes the PintFieldWidget."""
        self.ureg = ureg

        if default_unit is None:
            raise ValidationError(
                "PintFieldWidgets require a default_unit kwarg of a single Pint unit type (eg: 'grams')"
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

    def decompress(self, value: Quantity):
        """Decompresses the value into a tuple of magnitude and unit."""
        if value is None:
            return [None, None]

        return value


class TabledPintFieldWidget(PintFieldWidget):
    """Widget for PintField with a table of unit conversions."""

    template_name = "django_pint_field/tabled_django_pint_field_widget.html"

    def __init__(
        self, *, attrs: Optional[dict] = None, default_unit: str = None, unit_choices: list[str] = None, **kwargs
    ):
        """Initializes the TabledPintFieldWidget."""
        self.floatformat = kwargs.pop("floatformat", 6)
        self.table_class = kwargs.pop("table_class", "p-5 m-5")
        self.td_class = kwargs.pop("td_class", "text-end")
        super().__init__(attrs=attrs, default_unit=default_unit, unit_choices=unit_choices)

    def _normalize_value(self, value: list | tuple) -> tuple[Optional[int | float | Decimal], str | Unit]:
        """Normalizes the input value into a consistent format."""
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ImproperlyConfigured(f"Expected list/tuple of length 2, got {value}")

        magnitude, unit = value

        if magnitude is not None:
            if is_decimal_or_int(magnitude):
                magnitude = Decimal(str(magnitude))
            elif not isinstance(magnitude, (int, float, Decimal)):
                raise ImproperlyConfigured(f"Magnitude must be numeric, got {type(magnitude)}")

        if not isinstance(unit, (str, ureg.Unit)):
            raise ImproperlyConfigured(f"Unit must be string or ureg.Unit, got {type(unit)}")

        return magnitude, unit

    def _create_quantity(self, magnitude: Optional[int | float | Decimal], unit: str | Unit) -> Quantity:
        """Creates a Quantity object from magnitude and unit."""
        if magnitude is None:
            magnitude = 0

        if isinstance(unit, str):
            unit = getattr(self.ureg, unit)

        return self.ureg.Quantity(magnitude * unit)

    def _convert_to_unit(self, quantity: Quantity, target_unit: str) -> Quantity:
        """Converts a quantity to the target unit."""
        return quantity.to(target_unit)

    def _filter_choices(self, value: Optional[Quantity]) -> list[tuple[str, str]]:
        """Filters out the current value from choices if present."""
        if not isinstance(value, self.ureg.Quantity):
            return self.choices

        value_tuple = (str(value.units), str(value.units))
        return [choice for choice in self.choices if choice != value_tuple]

    def create_table(self, value: Optional[Quantity] = None) -> list[Quantity]:
        """Create a table of unit conversions."""
        filtered_choices = self._filter_choices(value)

        try:
            if isinstance(value, (list, tuple)):
                magnitude, unit = self._normalize_value(value)
                base_quantity = self._create_quantity(magnitude, unit)
            else:
                # Default case: zero quantity in the first available unit
                first_unit = filtered_choices[0][0] if filtered_choices else None
                base_quantity = self._create_quantity(0, first_unit)

            return [self._convert_to_unit(base_quantity, unit_output) for unit_output, _ in filtered_choices]

        except (AttributeError, ValueError) as e:
            raise ImproperlyConfigured(f"Error creating unit conversion table: {e}") from e

    def get_context(self, name: str, value: Optional[Quantity], attrs: dict):
        """Adds table of unit conversions to widget context."""
        context = super().get_context(name, value, attrs)
        context["values_list"] = self.create_table(value)
        context["floatformat"] = self.floatformat
        context["table_class"] = self.table_class
        context["td_class"] = self.td_class

        return context
