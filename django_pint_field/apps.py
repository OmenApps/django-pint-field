import logging
from decimal import Decimal, getcontext
from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.db.models import Lookup
from django.utils.translation import gettext_lazy as _
from io import StringIO
from psycopg2.extensions import register_adapter
from . import (
    get_IntegerPintDBField,
    get_DecimalPintDBField,
    get_BigIntegerPintDBField,
    integer_pint_field_adapter,
    big_integer_pint_field_adapter,
    decimal_pint_field_adapter,
)
from .fields import IntegerPintField, BigIntegerPintField, DecimalPintField
from .exceptions import PintFieldLookupError
from psycopg2.extensions import AsIs


logger = logging.getLogger("watervize.entities_flags")


def check_migrations_complete():
    """Runs the showmigrations command, and returns false if any have not been run yet"""
    out = StringIO()
    call_command("showmigrations", format="plan", stdout=out)
    out.seek(0)
    for line in out.readlines():
        status, name = line.rsplit(" ", 1)
        logger.debug(f"Migration '{name}' status: {status}")
        if "[X]" not in status:
            logger.warning(f"Migration '{name}' incomplete")
            return False
    return True


def get_comparator_from_rhs(rhs_params):
    def extract_comparator(input):
        print(f"input: {input}")
        return str(input)[1:].split(":")[0]

    if (
        isinstance(rhs_params, (list, tuple))
        and isinstance(rhs_params[0], (list, tuple))
        and isinstance(rhs_params[0][0], AsIs)
    ):
        return [extract_comparator(param) for param in rhs_params[0]]

    elif isinstance(rhs_params, (list, tuple)) and isinstance(rhs_params[0], AsIs):
        comparator = extract_comparator(rhs_params[0])
        return [
            comparator,
        ]

    else:
        return [""]


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
        if check_migrations_complete():
            # e.g.: x, y = IntegerPintDBField(magnitude=1, units="xyz")

            IntegerPintDBField = get_IntegerPintDBField()
            BigIntegerPintDBField = get_BigIntegerPintDBField()
            DecimalPintDBField = get_DecimalPintDBField()

            register_adapter(IntegerPintDBField, integer_pint_field_adapter)
            register_adapter(BigIntegerPintDBField, big_integer_pint_field_adapter)
            register_adapter(DecimalPintDBField, decimal_pint_field_adapter)
