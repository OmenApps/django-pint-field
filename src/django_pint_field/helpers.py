"""Helper functions for the django_pint_field app."""

from __future__ import annotations

import logging
import math
from decimal import Decimal
from typing import Any
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Field
from pint import Unit
from pint.errors import UndefinedUnitError

from .units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity


class PintFieldConverter:
    """Handles unit conversions for PintField values in admin displays."""

    def __init__(self, field_instance: Field):
        """Initialize the converter with the field instance."""
        self.field = field_instance
        self.ureg = field_instance.ureg
        # Add display_decimal_places from the field instance
        self.display_decimal_places = getattr(field_instance, "display_decimal_places", None)

    def convert_to_unit(self, value: Quantity, target_unit: str) -> Optional[Quantity]:
        """Convert a quantity to the target unit."""
        if value is None:
            return None

        try:
            target_unit_obj = get_pint_unit(self.ureg, target_unit)
            return value.to(target_unit_obj)
        except (AttributeError, UndefinedUnitError):
            return None


class PintFieldProxy:
    """Proxy for PintField values that enables unit conversion via attribute access."""

    def __init__(self, value: Quantity, converter: PintFieldConverter):
        """Initialize the proxy with the value and converter.

        :param value: A pint.Quantity instance
        :param converter: A PintFieldConverter instance
        """
        self.quantity = value
        self.converter = converter

    def __str__(self):
        """Return the string representation of the value."""
        if self.quantity is None:
            return ""

        # Format magnitude according to display_decimal_places if set
        if (
            hasattr(self.converter.field, "display_decimal_places")
            and self.converter.field.display_decimal_places is not None
        ):
            magnitude = float(self.quantity.magnitude)
            formatted_magnitude = f"{magnitude:.{self.converter.field.display_decimal_places}f}"
            # Remove trailing zeros after decimal point, but keep the decimal point if places > 0
            if "." in formatted_magnitude:
                formatted_magnitude = formatted_magnitude.rstrip("0").rstrip(".")
            return f"{formatted_magnitude} {self.quantity.units}"

        return str(self.quantity)

    def __format__(self, format_spec: str) -> str:
        """Format the value according to the format specification."""
        if not format_spec:
            return str(self)

        if self.quantity is None:
            return ""

        # Delegate formatting to the underlying Quantity object
        return format(self.quantity, format_spec)

    def __getattr__(self, name: str) -> Quantity | str:
        """Handle attribute access for unit conversions.

        Supports the following:
        - Simple unit conversion: instance.fieldname.MW
        - Unit conversion with decimal places: instance.fieldname.MW__4 (4 decimal places in new unit)
        - Decimal places only: instance.fieldname.digits__4 (4 decimal places, original units)
        """
        if name.startswith("__"):
            raise AttributeError(name)

        # If the attribute starts with 'get_', remove that part
        if name.startswith("get_"):
            name = name[4:]

        # Check if we have a decimal places specification
        parts = name.split("__")
        if len(parts) == 1:
            if name == "magnitude":
                return self.quantity.magnitude
            if name == "units":
                return self.quantity.units

        if len(parts) == 2:
            try:
                prefix, decimal_places = parts
                decimal_places = int(decimal_places)

                # If prefix is digits, just format decimal places without unit conversion
                if prefix == "digits":
                    quantizing_string = "0." + "0" * decimal_places
                    magnitude = Decimal(str(self.quantity.magnitude)).quantize(Decimal(quantizing_string))
                    return type(self.quantity)(magnitude, self.quantity.units)

                # Otherwise treat prefix as unit name and do unit conversion
                converted = self.converter.convert_to_unit(self.quantity, prefix)
                if converted is None:
                    raise AttributeError(f"Invalid unit conversion: {prefix}")

                # Then format to the specified decimal places
                quantizing_string = "0." + "0" * decimal_places
                magnitude = Decimal(str(converted.magnitude)).quantize(Decimal(quantizing_string))
                return type(converted)(magnitude, converted.units)

            except ValueError as e:
                raise AttributeError(f"Invalid decimal places specification: {parts[1]}") from e

        # Convert the value to the requested unit
        converted = self.converter.convert_to_unit(self.quantity, name)
        if converted is not None:
            return converted

        raise AttributeError(f"Invalid unit conversion: {name} for quantity {self.quantity}")

    def __getstate__(self):
        """Return a state that can be safely pickled.
        We'll store:
          - The numeric magnitude as a string
          - The string representation of units
          - Enough info to reconstruct self.converter
        """
        magnitude_str = str(self.quantity.magnitude)
        units_str = str(self.quantity.units)

        # Gather the minimal info needed to rebuild the converter’s field
        field_info = {
            "default_unit": self.converter.field.default_unit,
            "unit_choices": getattr(self.converter.field, "unit_choices", None),
            "rounding_method": getattr(self.converter.field, "rounding_method", None),
            "display_decimal_places": getattr(self.converter.field, "display_decimal_places", None),
            # add rounding_method or other attributes if relevant
        }

        return {
            "magnitude": magnitude_str,
            "units": units_str,
            "field_info": field_info,
        }

    def __setstate__(self, state):
        """Rebuild our Quantity and re-init the converter so the proxy works again."""
        from django_pint_field.models import BasePintField  # pylint: disable=C0415

        magnitude_str = state["magnitude"]
        units_str = state["units"]
        field_info = state["field_info"]

        # Rebuild the raw pint.Quantity
        magnitude = Decimal(magnitude_str)
        unit_obj = get_pint_unit(ureg, units_str)
        quantity = ureg.Quantity(magnitude, unit_obj)

        # Create a minimal "dummy" field to hold the same config
        class DummyField(BasePintField):
            """Dummy field to hold the same config as the original field."""

            def __init__(self):
                """We skip real __init__ calls to BasePintField."""

        dummy_field = DummyField()
        dummy_field.default_unit = field_info["default_unit"]
        dummy_field.unit_choices = field_info["unit_choices"]
        dummy_field.rounding_method = field_info["rounding_method"]
        dummy_field.display_decimal_places = field_info["display_decimal_places"]
        dummy_field.ureg = ureg

        # Rebuild the converter
        converter = PintFieldConverter(field_instance=dummy_field)

        # Assign back to self
        self.quantity = quantity
        self.converter = converter


def get_pint_unit(registry, unit_name: str) -> Optional[object]:
    """Get unit from registry using newer formatter API."""
    if unit_name is None:
        return None

    # Store the unit
    unit = getattr(registry, str(unit_name))

    # Configure the formatter for this unit if needed
    if hasattr(registry, "formatter") and not registry.formatter.default_format:
        registry.formatter.default_format = "D"  # Use default format

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
    if max_digits is not None and max_digits < 1:
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


def is_aggregate_expression(expr):
    """Check if an expression is an aggregate expression."""
    if getattr(expr, "is_pint_aggregate", False) or hasattr(expr, "_constructor"):
        return True

    # Fallback for safety:
    return expr.__class__.__module__.startswith("django_pint_field.aggregates") or expr.__class__.__module__.startswith(
        "django.db.models.aggregates"
    )
