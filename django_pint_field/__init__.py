"""
Enables pint for use with Django
"""
from decimal import Decimal
from django.db import connection
from pint import Quantity
from psycopg2.extras import register_composite
from psycopg2.extensions import adapt, AsIs


def get_base_unit_magnitude(value):
    """
    Provided a value (of type=Quantity), returns the magnitude of that quantity, converted to base units

    If the input is a float, we round it before converting.
    """
    print(f"get_base_unit_magnitude() type(value.magnitude): {type(value.magnitude)}")

    if not isinstance(value.magnitude, Decimal) and not isinstance(value.magnitude, int):
        # The magnitude may be input as a float, but we want it as only int (or Decimal). If we allow it to be converted
        #   from a float value, we might record a comparator value with more precision than actually desired.
        int_magnitude = round(value.magnitude)
        value = Quantity(int_magnitude * value.units)

    comparator_value = value.to_base_units()

    print(f"get_base_unit_magnitude() comparator_value: {comparator_value}")
    return Decimal(str(comparator_value.magnitude))


# e.g.: x, y = IntegerPintDBField(comparator=Decimal("1.00"), magnitude=1, unit="xyz")


def get_IntegerPintDBField():
    return register_composite("integer_pint_field", connection.cursor().cursor, globally=True).type


def get_BigIntegerPintDBField():
    return register_composite("big_integer_pint_field", connection.cursor().cursor, globally=True).type


def get_DecimalPintDBField():
    return register_composite("decimal_pint_field", connection.cursor().cursor, globally=True).type


def integer_pint_field_adapter(value):
    return AsIs(
        "(%s::decimal, %s::integer, %s::text)::integer_pint_field"
        % (
            adapt(value.comparator),
            adapt(value.magnitude),
            adapt(str(value.units)),
        )
    )


def big_integer_pint_field_adapter(value):
    return AsIs(
        "(%s::decimal, %s::bigint, %s::text)::big_integer_pint_field"
        % (
            adapt(value.comparator),
            adapt(value.magnitude),
            adapt(str(value.units)),
        )
    )


def decimal_pint_field_adapter(value):
    return AsIs(
        "(%s::decimal, %s::decimal, %s::text)::decimal_pint_field"
        % (
            adapt(value.comparator),
            adapt(value.magnitude),
            adapt(str(value.units)),
        )
    )
