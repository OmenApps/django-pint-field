"""REST framework integration for django-pint-field.

Recommendation for usage:

Use PintRestField when:

- You need a more structured, explicit format
- Working with APIs where the data structure is more important than human readability
- Dealing with front-end applications that expect consistent JSON structures

Use IntegerPintRestField / DecimalPintRestField when:

- You need a more compact, human-readable format
- Working with APIs where string representation is preferred
- Dealing with systems that expect string-based representations
"""

from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import Optional
from typing import Union

from pint import UndefinedUnitError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .helpers import is_decimal_or_int
from .units import ureg


Quantity = ureg.Quantity


class PintRestField(serializers.Field):
    """Serializer field for Pint quantities that uses dictionary representation.

    Converts between Pint Quantity objects and dictionaries containing magnitude and units.
    Example: Quantity(1, "gram") <-> {"magnitude": 1, "units": "gram"}
    """

    default_error_messages = {
        "invalid_magnitude": "Invalid magnitude value.",
        "invalid_units": "Invalid or undefined unit.",
        "missing_field": "Both magnitude and units are required.",
        "incompatible_units": "Incompatible unit dimensions.",
    }

    def to_representation(self, value: Optional[Quantity]) -> Optional[dict[str, Any]]:
        """Convert a Pint Quantity to a dictionary representation."""
        if value is None:
            return None

        if not isinstance(value, Quantity):
            raise ValidationError("Value must be a Pint Quantity")

        return {"magnitude": value.magnitude, "units": str(value.units)}

    def _prep_quantity(self, magnitude: Union[str, int, float, Decimal], units: str) -> Quantity:
        """Prepare Quantity object from provided magnitude and units."""
        try:
            if isinstance(magnitude, (int, float)):
                magnitude = Decimal(str(magnitude))
            elif not isinstance(magnitude, Decimal):
                magnitude = Decimal(magnitude)
        except (TypeError, ValueError, InvalidOperation) as e:
            raise ValidationError(self.error_messages["invalid_magnitude"]) from e

        try:
            unit_obj = getattr(ureg, str(units))
        except (AttributeError, UndefinedUnitError) as e:
            raise ValidationError(self.error_messages["invalid_units"]) from e

        try:
            return Quantity(magnitude * unit_obj)
        except Exception as e:
            raise ValidationError(str(e)) from e

    def to_internal_value(self, data: dict[str, Any]) -> Quantity:
        """Convert a dictionary representation to a Pint Quantity."""
        if not isinstance(data, dict):
            raise ValidationError("Invalid format. Expected dictionary with 'magnitude' and 'units'.")

        if "magnitude" not in data or "units" not in data:
            raise ValidationError(self.error_messages["missing_field"])

        magnitude = data["magnitude"]
        units = data["units"]

        return self._prep_quantity(magnitude, units)


class BasePintRestField(serializers.Field):
    """Base class for string-based Pint quantity serialization.

    Should not be used directly.
    """

    default_error_messages = {
        "invalid_format": 'Invalid format. Expected "number unit" or Quantity object.',
        "invalid_magnitude": "Invalid magnitude value.",
        "invalid_units": "Invalid or undefined unit.",
    }

    def __init__(self, *args, **kwargs):
        """Initialize field with Pint registry."""
        self.wrap = kwargs.pop("wrap", False)
        super().__init__(*args, **kwargs)

    def to_representation(self, value: Optional[Quantity]) -> Optional[str]:
        """Convert Quantity to string representation."""
        if value is None:
            return None

        if not isinstance(value, Quantity):
            raise ValidationError(f"Expected Quantity type but got {type(value)}", code="invalid_type")

        if self.wrap:
            return f"Quantity({value.magnitude} {value.units})"
        return str(value)

    def parse_string_value(self, data: str) -> Quantity:
        """Parse string value into Quantity."""
        try:
            if "Quantity(" in data:
                # Handle "Quantity(1.0 gram)" format
                data = data.replace("Quantity(", "").rstrip(")")

            if " " not in data or len(data.split(" ")) != 2:
                raise ValidationError(self.error_messages["invalid_format"])

            magnitude, units = data.split(" ")

            if not is_decimal_or_int(magnitude):
                raise ValidationError(self.error_messages["invalid_magnitude"])

            try:
                unit_obj = getattr(ureg, units)
            except (AttributeError, UndefinedUnitError) as e:
                raise ValidationError(self.error_messages["invalid_units"]) from e

            return self._create_quantity(magnitude, unit_obj)

        except (ValueError, TypeError) as e:
            raise ValidationError(str(e)) from e

    def _create_quantity(self, magnitude: Union[str, int, float, Decimal], units: Any) -> Quantity:
        """Create Quantity object with proper type handling."""
        raise NotImplementedError("Subclasses must implement _create_quantity")

    def to_internal_value(self, data: Union[str, Quantity]) -> Quantity:
        """Convert string or Quantity to Quantity object."""
        if isinstance(data, Quantity):
            return data
        if isinstance(data, str):
            return self.parse_string_value(data)
        raise ValidationError(f"Expected string or Quantity but got {type(data)}", code="invalid_type")


class IntegerPintRestField(BasePintRestField):
    """Serializes IntegerPintField objects using string representation.

    Example: Quantity(1, "gram") <-> "1 gram"
    """

    def _create_quantity(self, magnitude: Union[str, int, float, Decimal], units: Any) -> Quantity:
        """Create Quantity with integer magnitude."""
        return Quantity(int(float(magnitude)), units)


class DecimalPintRestField(BasePintRestField):
    """Serializes DecimalPintField objects using string representation.

    Example: Quantity(1.0, "gram") <-> "Quantity(1.0 gram)"
    """

    def __init__(self, *args, **kwargs):
        """Initialize field, ignoring decimal-specific kwargs."""
        kwargs.pop("max_digits", None)
        kwargs.pop("decimal_places", None)
        super().__init__(*args, **kwargs)

    def _create_quantity(self, magnitude: Union[str, int, float, Decimal], units: Any) -> Quantity:
        """Create Quantity with decimal magnitude."""
        return Quantity(Decimal(str(magnitude)), units)
