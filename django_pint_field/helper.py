from pint import DimensionalityError
from typing import List


def check_matching_unit_dimension(registry, default_unit: str, units_to_check: List[str]) -> None:
    """
    Check if all units_to_check have the same Dimension like the default_unit
    If not
    :raise DimensionalityError
    """

    default_unit = getattr(registry, default_unit)

    print("check_matching_unit_dimension")

    for unit_string in units_to_check:
        unit = getattr(registry, unit_string)
        print(
            f"check_matching_unit_dimension unit: {unit} {unit.dimensionality}, "
            f"default_unit: {default_unit} {default_unit.dimensionality}, "
            f"equal: {unit.dimensionality == default_unit.dimensionality}"
        )
        if not unit.dimensionality == default_unit.dimensionality:
            print("check_matching_unit_dimension RAISE ERROR!")
            raise DimensionalityError(default_unit, unit)
