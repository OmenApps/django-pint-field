import logging
from decimal import getcontext
from io import StringIO

from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.utils.translation import gettext_lazy as _
from psycopg2.extensions import AsIs, adapt
from psycopg2.extras import register_composite

logger = logging.getLogger("django_pint_field")


def check_migrations_complete():
    """Runs the showmigrations command, and returns false if any have not been run yet"""
    out = StringIO()
    call_command("showmigrations", format="plan", stdout=out)
    out.seek(0)
    for line in out.readlines():
        status, name = line.rsplit(" ", 1)
        if "[X]" not in status:
            print(status, name)
            return False
    return True


def set_decimal_precision():
    """
    If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
      decimalprecision will be set to that value. Otherwise, it is left as default.
    """
    decimal_precision = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 0)

    if isinstance(decimal_precision, int) and decimal_precision > 0:
        getcontext().prec = decimal_precision


class DjangoPintFieldAppConfig(AppConfig):
    name = "django_pint_field"

    def ready(self):
        def integer_pint_field_adapter(value):
            comparator = adapt(value.comparator)
            magnitude = adapt(value.magnitude)
            units = adapt(str(value.units))
            return AsIs(
                "(%s::decimal, %s::integer, %s::text)"
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
                "(%s::decimal, %s::bigint, %s::text)"
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
                "(%s::decimal, %s::decimal, %s::text)"
                % (
                    comparator,
                    magnitude,
                    units,
                )
            )

        set_decimal_precision()

        if check_migrations_complete():
            from .lookups import get_pint_field_lookups

            # e.g.: x, y, z = IntegerPintDBField(comparator=Decimal("1.00"), magnitude=1, units="xyz")
            # In [1]: IntegerPintDBField(comparator=Decimal("1.00"), magnitude=1, units="xyz")
            # Out[1]: integer_pint_field(comparator=Decimal('1.00'), magnitude=1, units='xyz')

            IntegerPintDBField = register_composite(
                "integer_pint_field", connection.cursor().cursor, globally=True
            ).type
            BigIntegerPintDBField = register_composite(
                "big_integer_pint_field", connection.cursor().cursor, globally=True
            ).type
            DecimalPintDBField = register_composite(
                "decimal_pint_field", connection.cursor().cursor, globally=True
            ).type

            get_pint_field_lookups()
