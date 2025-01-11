"""Helper functions for the django_pint_field app."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any
from typing import Optional

from django.core.exceptions import ValidationError
from pint import Unit

from .units import ureg


Quantity = ureg.Quantity


def get_pint_unit(registry, unit_name: str) -> Optional[object]:
    """Get unit from registry using newer formatter API."""
    if unit_name is None:
        return None

    # Store the unit
    unit = getattr(registry, str(unit_name))

    # Configure the formatter for this unit if needed
    if hasattr(registry, "formatter"):
        registry.formatter.default_format = "D"  # Use default format
        # Note: fmt_locale can be set here if locale formatting is needed

    return unit


def get_unit_string(unit_value):
    """Extract the actual unit string from various possible formats.

    Args:
        unit_value: Can be:
            - A string representing the unit
            - A Unit object
            - A tuple/list of (display_name, unit_str)
            - A compound unit string (e.g. "mol/L")

    Returns:
        str: The Pint unit string
    """
    if isinstance(unit_value, (list, tuple)):
        if len(unit_value) != 2:
            raise ValidationError(f"Unit choices must be 2-element lists/tuples, got {unit_value}")
        # Return the second element which should be the Pint unit string
        return str(unit_value[1])
    return str(unit_value)


def check_matching_unit_dimension(
    registry: Any,
    default_unit: str | Unit | tuple | list,
    units_to_check: list[str | Unit | tuple | list],
    raise_exception: bool = True,
) -> None:
    """Check that unit choices match dimension of default unit."""
    if not units_to_check:
        return

    if hasattr(registry, "formatter"):
        registry.formatter.default_format = "D"

    try:
        # Get the actual unit string for the default unit
        default_unit_str = get_unit_string(default_unit)
        default_unit_obj = getattr(registry, default_unit_str)
    except AttributeError as e:
        if raise_exception:
            raise ValidationError(f"Invalid default unit: {default_unit_str}") from e
        return

    for unit in units_to_check:
        try:
            unit_str = get_unit_string(unit)
            unit_obj = getattr(registry, unit_str)
            if unit_obj.dimensionality != default_unit_obj.dimensionality:
                if raise_exception:
                    raise ValidationError(
                        f"Unit {unit_str} has incompatible dimensionality with default unit {default_unit_str}."
                    )
        except AttributeError as e:
            if raise_exception:
                raise ValidationError(f"Invalid unit: {unit_str}") from e


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


def get_quantizing_string(*, max_digits: Optional[int] = None, decimal_places: int = 0) -> str:
    """Quantizing string generation with leading digits and decimal places.

    If max_digits is provided, the leading digits will be set to max_digits - decimal_places.

    Examples:
        get_full_quantizing_string(max_digits=1, decimal_places=0) -> "1."  # Rounds to integer
        get_full_quantizing_string(max_digits=3, decimal_places=2) -> "1.11"  # Preserve 3 digits and 2 decimal places
        get_full_quantizing_string(max_digits=5, decimal_places=3) -> "11.111"  # Preserve 5 digits and 3 decimal places
        get_full_quantizing_string(decimal_places=3) -> ".111"  # Preserve 3 decimal places
    """
    if max_digits and max_digits < 1:
        raise ValidationError("max_digits must be greater than 0")
    if decimal_places < 0:
        raise ValidationError("decimal_places must be non-negative")
    if max_digits and decimal_places > max_digits:
        raise ValidationError("decimal_places cannot be greater than max_digits")

    if max_digits:
        leading_digits = max_digits - decimal_places

        if decimal_places == 0:
            return f"{'1' * leading_digits}."
        if max_digits == decimal_places:
            return f"0.{'1' * decimal_places}"
        return f"{'1' * leading_digits}.{'1' * decimal_places}"

    if decimal_places == 0:
        return "1."
    return f".{'1' * decimal_places}"
