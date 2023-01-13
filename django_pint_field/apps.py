from decimal import getcontext
from io import StringIO

from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.utils.translation import gettext_lazy as _


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
        from .lookups import get_pint_field_lookups

        get_pint_field_lookups()

        set_decimal_precision()

        if check_migrations_complete():
            pass
