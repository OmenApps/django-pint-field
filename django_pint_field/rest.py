from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .helper import is_decimal_or_int
from .units import ureg

Quantity = ureg.Quantity


class IntegerPintRestField(serializers.Field):
    """
    Serializes IntegerPintField and IntegerPintField objects as `Quantity(1,ounce)`.
    """

    def to_representation(self, value):
        """Converts to string"""
        if isinstance(value, Quantity):
            return str(value)

        raise ValidationError(f"value of type {type(value)} passed to to_representation, but expected type Quantity.")

    def to_internal_value(self, data):
        """Converts back to a Quantity"""

        if isinstance(data, Quantity):
            return data

        if isinstance(data, str):
            if data.find(" ") and len(data) >= 3:
                magnitude, units = data.split(" ")
                if is_decimal_or_int(magnitude):
                    magnitude = int(magnitude)
                    return Quantity(magnitude, units)

        raise ValidationError(
            f"data of type {type(data)} passed to to_internal_value, but expected type str or Quantity."
        )


class DecimalPintRestField(serializers.Field):
    """
    Serializes DecimalPintField objects as `Quantity(1.0,ounce)`.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        # Throw out unexpected kwargs if encountered
        kwargs.pop("max_digits", None)
        kwargs.pop("decimal_places", None)

        super().__init__(
            *args,
            **kwargs,
        )

    def to_representation(self, value):
        """Converts to string"""
        if isinstance(value, Quantity):
            return f"Quantity({str(value)})"

        raise ValidationError(f"value of type {type(value)} passed to to_representation, but expected type Quantity.")

    def to_internal_value(self, data):
        """Converts back to a Quantity"""

        if isinstance(data, Quantity):
            return data

        if isinstance(data, str):
            if data.find(" ") and len(data) >= 3:
                magnitude, units = data.split(" ")
                if is_decimal_or_int(magnitude):
                    magnitude = Decimal(magnitude)
                    return Quantity(magnitude, units)

        raise ValidationError(
            f"data of type {type(data)} passed to to_internal_value, but expected type str or Quantity."
        )
