from decimal import Decimal
from typing import List

from pint import DimensionalityError

from .units import ureg

Quantity = ureg.Quantity


def check_matching_unit_dimension(registry, default_unit: str, units_to_check: List[str]) -> None:
    """
    Check if all units_to_check have the same Dimension like the default_unit
    If not
    :raise DimensionalityError
    """

    default_unit = getattr(registry, default_unit)

    for unit_string in units_to_check:
        unit = getattr(registry, unit_string)

        if not unit.dimensionality == default_unit.dimensionality:
            raise DimensionalityError(default_unit, unit)


def is_decimal_or_int(input: str):
    try:
        float(input)
        return True
    except ValueError:
        return False


def get_base_units(registry, default_unit):
    """Returns the base units, based on a specific Pint registry and a default_unit"""
    temp_quantity = registry.Quantity(1 * default_unit)
    temp_quantity = temp_quantity.to_base_units()
    return temp_quantity.units


def get_base_unit_magnitude(value):
    """
    Provided a value (of type=Quantity), returns the magnitude of that quantity, converted to base units

    If the input is a float, we round it before converting.
    """
    if not isinstance(value.magnitude, Decimal) and not isinstance(value.magnitude, int):
        # The magnitude may be input as a float, but we want it as only int (or Decimal). If we allow it to be converted
        #   from a float value, we might record a comparator value with more precision than actually desired.
        int_magnitude = round(value.magnitude)
        value = Quantity(int_magnitude * value.units)

    comparator_value = value.to_base_units()

    return Decimal(str(comparator_value.magnitude))


def get_quantizing_string(max_digits=1, decimal_places=0):
    """_summary_
    Builds a string that can be used to quantize a decimal.Decimal value

    Args:
        max_digits (int, optional): _description_. Defaults to 1.
        decimal_places (int, optional): _description_. Defaults to 0.

    Returns:
        str: A string that can be used to quantize a decimal.Decimal value
    """
    leading_digits = max_digits - decimal_places

    if decimal_places == 0:
        quantizing_string = f"{'1' * leading_digits}"

    quantizing_string = f"{'1' * leading_digits}.{'1' * decimal_places}"

    return quantizing_string
