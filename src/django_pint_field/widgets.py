"""Widgets for django_pint_field."""

from __future__ import annotations

import logging
from collections.abc import Iterable  # pylint: disable=E0611
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.forms.widgets import MultiWidget
from django.forms.widgets import NumberInput
from django.forms.widgets import Select

from .helpers import get_pint_unit
from .helpers import is_decimal_or_int
from .units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity
Unit = ureg.Unit


class PintFieldWidget(MultiWidget):
    """Widget for PintField."""

    def __init__(
        self,
        *,
        attrs: Optional[dict] = None,
        default_unit: str | tuple[str, str] | list[str, str],
        unit_choices: Optional[Iterable[str] | Iterable[Iterable[str]]] = None,
    ):
        """Initializes the PintFieldWidget."""
        self.ureg = ureg

        if default_unit is None:
            raise ValidationError(
                "PintFieldWidgets require a default_unit kwarg of a single Pint unit type (eg: 'grams')"
            )

        # Normalize default_unit
        if isinstance(default_unit, str):
            self._default_unit_display = default_unit
            self._default_unit_value = default_unit
        elif isinstance(default_unit, (list, tuple)) and len(default_unit) == 2:
            self._default_unit_display, self._default_unit_value = default_unit
        else:
            raise ValidationError(
                "default_unit must be either a string or a 2-tuple/2-list of (display_name, unit_value)"
            )

        self.default_unit = self._default_unit_value

        unit_choices = unit_choices or [(self._default_unit_display, self._default_unit_value)]
        if not any(value[1] == self._default_unit_value for value in unit_choices):
            unit_choices.insert(0, (self._default_unit_display, self._default_unit_value))

        # Store the original choices for reference
        self.original_choices = unit_choices

        # Create choices for the Select widget
        # The value needs to be the Pint unit string, display name is what user sees
        self.choices = [(str(self.ureg(choice[1]).units), choice[0]) for choice in unit_choices]

        attrs = attrs or {}
        if "step" not in attrs:
            attrs.setdefault("step", "any")
        widgets = (NumberInput(attrs=attrs), Select(attrs=attrs, choices=self.choices))
        super().__init__(widgets, attrs)

    def decompress(self, value: Quantity):
        """Decompresses the value into a tuple of magnitude and unit."""
        if value is None:
            return [None, None]

        if hasattr(value, "value"):
            value = value.quantity

        return [value.magnitude, str(value.units)]


class TabledPintFieldWidget(PintFieldWidget):
    """Widget for PintField with a table of unit conversions."""

    template_name = "django_pint_field/tabled_django_pint_field_widget.html"

    def __init__(
        self,
        *,
        attrs: Optional[dict] = None,
        default_unit: str = None,
        unit_choices: list[str] = None,
        **kwargs,
    ):
        """Initializes the TabledPintFieldWidget."""
        self.styling_options = {
            # Wrapper classes
            "input_wrapper_class": kwargs.pop("input_wrapper_class", ""),
            "table_wrapper_class": kwargs.pop("table_wrapper_class", ""),
            # Table structure classes
            "table_class": kwargs.pop("table_class", ""),
            "thead_class": kwargs.pop("thead_class", ""),
            "tbody_class": kwargs.pop("tbody_class", ""),
            # Row classes
            "tr_header_class": kwargs.pop("tr_header_class", ""),
            "tr_class": kwargs.pop("tr_class", ""),
            # Cell classes
            "th_class": kwargs.pop("th_class", ""),
            "td_class": kwargs.pop("td_class", ""),
            "td_unit_class": kwargs.pop("td_unit_class", ""),
            "td_value_class": kwargs.pop("td_value_class", ""),
        }

        self.content_options = {
            "unit_header": kwargs.pop("unit_header", "Unit"),
            "value_header": kwargs.pop("value_header", "Value"),
            "show_units_in_values": kwargs.pop("show_units_in_values", False),
            "floatformat": kwargs.pop("floatformat", -1),  # -1 means only show necessary decimal places
        }

        super().__init__(attrs=attrs, default_unit=default_unit, unit_choices=unit_choices)

    def _normalize_value(self, value: list | tuple | Quantity) -> tuple[Optional[int | float | Decimal], str | Unit]:
        """Normalizes the input value into a consistent format."""
        if value is None:
            return None, self.default_unit

        # Handle PintFieldProxy
        if hasattr(value, "value") and hasattr(value.quantity, "magnitude"):
            return value.quantity.magnitude, value.quantity.units

        # Handle Quantity
        if hasattr(value, "magnitude"):
            return value.magnitude, value.units

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

        # Ensure magnitude is numeric
        if isinstance(magnitude, str):
            magnitude = Decimal(magnitude)
        elif isinstance(magnitude, (list, tuple)):
            magnitude = Decimal(str(magnitude[0]))

        if isinstance(unit, str):
            unit = get_pint_unit(self.ureg, unit)

        return self.ureg.Quantity(magnitude) * unit

    def create_table(self, value):
        """Create a list of converted quantities for the table display."""
        if value is None:
            return []

        # If value is a proxy, get the actual value
        if hasattr(value, "value"):
            value = value.quantity

        # Handle tuple/list input
        if isinstance(value, (list, tuple)) and len(value) == 2:
            value = self._create_quantity(*value)

        # Ensure we have a proper Quantity object
        if not isinstance(value, Quantity):
            raise ValueError(f"Expected Pint Quantity, got {type(value)}")

        # Ensure magnitude is numeric
        if not isinstance(value.magnitude, (int, float, Decimal)):
            try:
                float(value.magnitude)
                value = Quantity(Decimal(str(value.magnitude)), value.units)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid magnitude type: {type(value.magnitude)}") from e

        # Convert value to each available unit
        converted_values = []
        for _, target_unit in self.original_choices:
            try:
                # Convert the value to the target unit, skipping the current unit
                if str(target_unit) != str(value.units):
                    converted = value.to(target_unit)
                    converted_values.append(converted)
            except (AttributeError, ValueError) as e:
                logger.error("Error converting value to %s: %s", target_unit, e)
                continue

        return converted_values

    def get_context(self, name, value, attrs):
        """Add customization options to the widget context."""
        context = super().get_context(name, value, attrs)

        # Add all styling classes to context
        context.update(self.styling_options)

        # Add content options to context
        context.update(self.content_options)

        # Create the conversion table values
        context["values_list"] = self.create_table(value)

        # Pass the display choices directly as a list of tuples
        display_choices = []
        for display_name, unit_value in self.original_choices:
            unit_str = str(self.ureg(unit_value).units)
            display_choices.append((display_name, unit_str))
        context["display_choices"] = display_choices

        return context
