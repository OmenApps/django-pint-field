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
        set_decimal_precision()

        if check_migrations_complete():
            from .lookups import get_pint_field_lookups

            get_pint_field_lookups()
