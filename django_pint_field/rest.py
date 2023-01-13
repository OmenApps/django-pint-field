from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .units import ureg

Quantity = ureg.Quantity


class IntegerPintRestField(serializers.Field):
    """
    Serializes IntegerPintField and IntegerPintField objects as `Quantity(1,ounce)`.
    """

    def to_representation(self, value):
        """Converts to string"""
        return str(value.magnitude)

    def to_internal_value(self, data):
        """Converts back to a Quantity"""

        if isinstance(data, Quantity):
            return data

        if isinstance(data, str):
            if data.find(" ") and len(data) >= 3:
                magnitude, units = data.split(" ")
                magnitude = int(magnitude)
                return Quantity(magnitude, units)

        raise ValidationError("Incorrect type passed to to_internal_value")


class DecimalPintRestField(serializers.Field):
    """
    Serializes DecimalPintField objects as `Quantity(1.0,ounce)`.
    """

    def to_representation(self, value):
        """Converts to string"""
        return "Quantity(%s, %s)" % (value.magnitude, value.units)

    def to_internal_value(self, data):
        """Converts back to a Quantity"""

        if isinstance(data, Quantity):
            return data

        if isinstance(data, str):
            if data.find(" ") and len(data) >= 3:
                magnitude, units = data.split(" ")
                magnitude = Decimal(magnitude)
                return Quantity(magnitude, units)

        raise ValidationError("Incorrect type passed to to_internal_value")
