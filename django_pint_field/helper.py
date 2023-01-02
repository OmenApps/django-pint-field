from pint import DimensionalityError
from typing import List


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
