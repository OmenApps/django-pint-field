"""Helper functions for the django_pint_field app."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any
from typing import Union

from django.core.exceptions import ValidationError
from pint import Unit

from .units import ureg


Quantity = ureg.Quantity


def check_matching_unit_dimension(
    registry: Any, default_unit: Union[str, Unit], units_to_check: list[Union[str, Unit]], raise_exception: bool = True
) -> None:
    """Improved unit dimension checking with better type hints."""
    if not units_to_check:
        return

    try:
        default_unit = getattr(registry, str(default_unit))
    except AttributeError as e:
        if raise_exception:
            raise ValidationError(f"Invalid default unit: {default_unit}") from e

    for unit in units_to_check:
        try:
            unit_obj = getattr(registry, str(unit))
            if unit_obj.dimensionality != default_unit.dimensionality:
                raise ValidationError(f"Unit {unit} has incompatible dimensionality with default unit.")
        except AttributeError as e:
            if raise_exception:
                raise ValidationError(f"Invalid unit: {unit}") from e


def is_decimal_or_int(value):
    """Tries to convert value to a float, which would work for an int, float, or Decimal value."""
    if isinstance(value, bool):
        return False

    try:
        conversion = float(value)
        # If the conversion is infinite or NaN, we don't want to use it.
        if not math.isfinite(conversion):
            return False

        return True
    except (ValueError, TypeError):
        return False


def get_base_units(registry, default_unit: str | Unit) -> Unit:
    """Returns the base units, based on a specific Pint registry and a default_unit."""
    temp_quantity = registry.Quantity(1 * default_unit)
    temp_quantity = temp_quantity.to_base_units()
    return temp_quantity.units


def get_base_unit_magnitude(value: Quantity) -> Decimal:
    """Provided a value (of type=Quantity), returns the magnitude of that quantity, converted to base units.

    If the input is a float, we round it before converting.
    """
    if not isinstance(value.magnitude, Decimal) and not isinstance(value.magnitude, int):
        # The magnitude may be input as a float, but we want it as only int (or Decimal). If we allow it to be converted
        #   from a float value, we might record a comparator value with more precision than actually desired.
        int_magnitude = round(value.magnitude)
        value = Quantity(int_magnitude * value.units)

    comparator_value = value.to_base_units()

    return Decimal(str(comparator_value.magnitude))


def get_quantizing_string(max_digits: int = 1, decimal_places: int = 0) -> str:
    """Improved quantizing string generation with validation."""
    if max_digits < 1:
        raise ValidationError("max_digits must be greater than 0")
    if decimal_places < 0:
        raise ValidationError("decimal_places must be non-negative")
    if decimal_places > max_digits:
        raise ValidationError("decimal_places cannot be greater than max_digits")

    leading_digits = max_digits - decimal_places

    if decimal_places == 0:
        return "1" * leading_digits
    if max_digits == decimal_places:
        return f"0.{'1' * decimal_places}"
    return f"{'1' * leading_digits}.{'1' * decimal_places}"
