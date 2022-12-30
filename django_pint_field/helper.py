from pint import DimensionalityError, UnitRegistry
from typing import List


def check_matching_unit_dimension(
    ureg: UnitRegistry, default_unit: str, units_to_check: List[str]
) -> None:
    """
    Check if all units_to_check have the same Dimension like the default_unit
    If not
    :raise DimensionalityError
    """

    default_unit = getattr(ureg, default_unit)

    for unit_string in units_to_check:
        unit = getattr(ureg, unit_string)
        if unit.dimensionality != default_unit.dimensionality:
            raise DimensionalityError(default_unit, unit)
