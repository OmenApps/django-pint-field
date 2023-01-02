"""
Enables pint for use with Django
"""
import logging
from decimal import Decimal
from django.db import connection
from pint import Quantity
from psycopg2.extras import register_composite
from psycopg2.extensions import adapt, AsIs


logger = logging.getLogger("django_pint_field")


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


# e.g.: x, y, z = IntegerPintDBField(comparator=Decimal("1.00"), magnitude=1, units="xyz")
# In [1]: IntegerPintDBField(comparator=Decimal("1.00"), magnitude=1, units="xyz")
# Out[1]: integer_pint_field(comparator=Decimal('1.00'), magnitude=1, units='xyz')


# If migrations have not yet run, we cannot map to the new postgres composite fields, so we cheat
try:
    IntegerPintDBField = register_composite("integer_pint_field", connection.cursor().cursor, globally=True).type
    BigIntegerPintDBField = register_composite(
        "big_integer_pint_field", connection.cursor().cursor, globally=True
    ).type
    DecimalPintDBField = register_composite("decimal_pint_field", connection.cursor().cursor, globally=True).type
except Exception as e:
    logger.warning(
        "One or more types does not exist in the database. "
        "Run migrations for django_pint_field. If using docker, try restarting. "
        f"{e}"
    )

    class NullPintDBField:
        def __init__(self, comparator, magnitude, units) -> None:
            pass

        def __str__(self):
            return ""

    IntegerPintDBField = NullPintDBField
    BigIntegerPintDBField = NullPintDBField
    DecimalPintDBField = NullPintDBField


def integer_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::integer, %s::text)::integer_pint_field"
        % (
            comparator,
            magnitude,
            units,
        )
    )


def big_integer_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::bigint, %s::text)::big_integer_pint_field"
        % (
            comparator,
            magnitude,
            units,
        )
    )


def decimal_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::decimal, %s::text)::decimal_pint_field"
        % (
            comparator,
            magnitude,
            units,
        )
    )
