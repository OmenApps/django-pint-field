"""Validation utilities for django-pint-field."""

import logging
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import Optional
from typing import Union

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pint import DimensionalityError
from pint import Quantity as BaseQuantity
from pint import UndefinedUnitError
from pint import UnitRegistry

from .helpers import check_matching_unit_dimension
from .units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity


def validate_dimensionality(value: Any, default_unit: str) -> None:
    """Validate that the value has the correct dimensionality."""
    if not isinstance(value, BaseQuantity):
        return

    try:
        check_matching_unit_dimension(
            ureg,
            default_unit,
            [str(value.units)],
        )
    except DimensionalityError as e:
        raise ValidationError(
            _("%(value)s has invalid dimensionality"),
            code="invalid_dimensionality",
            params={"value": value},
        ) from e


def validate_required_value(value: Any, required: bool = True, blank: bool = False) -> None:
    """Validate that a required value is present."""
    if not required:
        return

    if value is None:
        raise ValidationError(_("This field cannot be null."), code="null")

    if not blank and value in validators.EMPTY_VALUES:
        raise ValidationError(_("This field cannot be blank."), code="blank")


def validate_decimal_places(
    value: Union[BaseQuantity, Decimal],
    decimal_places: int,
    max_digits: int,
    allow_rounding: bool = False,
) -> None:
    """Validate decimal places and digits for a value."""
    if not hasattr(value, "magnitude"):
        return

    magnitude = value.magnitude
    if not isinstance(magnitude, Decimal):
        try:
            magnitude = Decimal(str(magnitude))
        except (TypeError, InvalidOperation) as e:
            raise ValidationError(_("Value must be a valid decimal."), code="invalid") from e

    # Check number of decimal places
    if int(magnitude.as_tuple().exponent) < -decimal_places and not allow_rounding:
        raise ValidationError(
            _("Ensure that there are no more than %(decimal_places)s decimal places."),
            code="max_decimal_places",
            params={"decimal_places": decimal_places},
        )

    # Check total number of digits
    if len(magnitude.as_tuple().digits) > max_digits and not allow_rounding:
        raise ValidationError(
            _("Ensure that there are no more than %(max_digits)s digits in total."),
            code="max_digits",
            params={"max_digits": max_digits},
        )


def validate_value_range(
    value: Union[BaseQuantity, int, float, Decimal],
    min_value: Optional[Union[int, float, Decimal]] = None,
    max_value: Optional[Union[int, float, Decimal]] = None,
) -> None:
    """Validate that a value falls within the specified range."""
    if value is None:
        return

    magnitude = getattr(value, "magnitude", value)

    try:
        float_val = float(magnitude)
    except (TypeError, ValueError) as e:
        raise ValidationError(_("Value must be a number."), code="invalid") from e

    if min_value is not None and float_val < min_value:
        raise ValidationError(
            _("Ensure this value is greater than or equal to %(min_value)s."),
            code="min_value",
            params={"min_value": min_value},
        )

    if max_value is not None and float_val > max_value:
        raise ValidationError(
            _("Ensure this value is less than or equal to %(max_value)s."),
            code="max_value",
            params={"max_value": max_value},
        )


class QuantityConverter:
    """Handles conversion of various input types to Quantity objects."""

    def __init__(
        self,
        default_unit: str,
        field_type: str = "decimal",
        decimal_places: Optional[int] = None,
        unit_registry: Optional[UnitRegistry] = None,
    ):
        """Initialize the QuantityConverter."""
        self.default_unit = default_unit
        self.field_type = field_type
        self.decimal_places = decimal_places
        self.ureg = unit_registry or UnitRegistry()

    def convert(self, value: Any) -> Optional[BaseQuantity]:
        """Main entry point for converting values to quantities."""
        if value is None or value in validators.EMPTY_VALUES:
            return None

        try:
            # Dictionary of type handlers
            type_handlers = {
                str: self._handle_string,
                (int, float, Decimal): self._handle_numeric,
                BaseQuantity: self._handle_base_quantity,
                (list, tuple): self._handle_sequence,
                dict: self._handle_dictionary,
            }

            # Find and execute the appropriate handler
            for types, handler in type_handlers.items():
                if isinstance(value, types):
                    return handler(value)

            raise ValidationError(_("Could not convert value to quantity."), code="invalid")

        except (ValueError, InvalidOperation) as e:
            raise ValidationError(_("Invalid numeric value."), code="invalid") from e

    def _convert_magnitude(self, value: Union[str, int, float, Decimal]) -> Union[Decimal, int]:
        """Convert a value to either Decimal or int based on field_type."""
        str_value = str(value)
        return Decimal(str_value) if self.field_type == "decimal" else int(float(str_value))

    def _is_decimal_or_int(self, value: Any) -> bool:
        """Check if a value can be converted to Decimal or int."""
        try:
            Decimal(str(value))
            return True
        except (ValueError, TypeError, InvalidOperation):
            return False

    def _create_quantity(self, magnitude: Union[Decimal, int], units: str) -> BaseQuantity:
        """Create a Quantity object with validation."""
        check_matching_unit_dimension(self.ureg, self.default_unit, [str(units)])
        return self.ureg.Quantity(magnitude, units)

    def _handle_string(self, value: str) -> BaseQuantity:
        """Handle string input types."""
        if value.startswith("(") and value.endswith(")"):
            return self._handle_composite_string(value)

        if self._is_decimal_or_int(value):
            magnitude = self._convert_magnitude(value)
            return self.ureg.Quantity(magnitude, self.default_unit)

        try:
            return self.ureg.Quantity(value)
        except UndefinedUnitError as e:
            raise ValidationError(_("Invalid quantity string."), code="invalid") from e

    def _handle_composite_string(self, value: str) -> BaseQuantity:
        """Handle composite string format '(comparator,magnitude,units)'."""
        try:
            _comparator, magnitude, units = value.strip("()").split(",")
            magnitude = self._convert_magnitude(magnitude.strip())
            return self._create_quantity(magnitude, units.strip())
        except ValueError as e:
            raise ValidationError(_("Invalid composite string format."), code="invalid") from e

    def _handle_numeric(self, value: Union[int, float, Decimal]) -> BaseQuantity:
        """Handle numeric input types."""
        magnitude = self._convert_magnitude(value)
        return self.ureg.Quantity(magnitude, self.default_unit)

    def _handle_base_quantity(self, value: BaseQuantity) -> BaseQuantity:
        """Handle BaseQuantity input type."""
        if not isinstance(value, self.ureg.Quantity):
            magnitude = self._convert_magnitude(value.magnitude)
            return self._create_quantity(magnitude, str(value.units))
        return value

    def _handle_sequence(self, value: Union[list, tuple]) -> BaseQuantity:
        """Handle sequence (list/tuple) input types."""
        if len(value) == 2:
            magnitude, units = value
        elif len(value) == 3:
            _, magnitude, units = value
        else:
            raise ValidationError(_("Invalid sequence length for quantity."), code="invalid")

        if not self._is_decimal_or_int(magnitude):
            raise ValidationError(_("Magnitude must be a number."), code="invalid")

        magnitude = self._convert_magnitude(magnitude)
        return self._create_quantity(magnitude, units)

    def _handle_dictionary(self, value: dict) -> BaseQuantity:
        """Handle dictionary input type."""
        if "magnitude" not in value or "units" not in value:
            raise ValidationError(_("Dictionary must contain 'magnitude' and 'units' keys."), code="invalid")

        magnitude = value["magnitude"]
        units = value["units"]

        if not self._is_decimal_or_int(magnitude):
            raise ValidationError(_("Magnitude must be a number."), code="invalid")

        magnitude = self._convert_magnitude(magnitude)
        return self._create_quantity(magnitude, units)
