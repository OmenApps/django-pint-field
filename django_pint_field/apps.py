import logging
from django.apps import AppConfig
from django.core.management import call_command
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
