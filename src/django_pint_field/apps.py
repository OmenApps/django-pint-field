"""AppConfig for the django_pint_field app."""

import logging
from decimal import getcontext

from django.apps import AppConfig
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.signals import post_migrate

from .app_settings import DJANGO_PINT_FIELD_DECIMAL_PRECISION


logger = logging.getLogger(__name__)


def check_migrations_complete(app_label=None):
    """Check if all migrations have been applied."""
    executor = MigrationExecutor(connection=connection)

    if app_label:
        targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] == app_label]
    else:
        targets = executor.loader.graph.leaf_nodes()

    return len(executor.migration_plan(targets)) == 0


def set_decimal_precision():
    """Sets the decimal precision for the project.

    If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
      decimalprecision will be set to that value. Otherwise, it is left as default (28 digits).

    See: https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision
    """
    decimal_precision = DJANGO_PINT_FIELD_DECIMAL_PRECISION

    if isinstance(decimal_precision, int) and decimal_precision > 0:
        getcontext().prec = decimal_precision


class DjangoPintFieldAppConfig(AppConfig):
    """AppConfig for the django_pint_field app."""

    name = "django_pint_field"

    def ready(self):
        """Runs when the app is ready."""
        if check_migrations_complete():
            from .models import register_pint_composite_types  # pylint: disable=C0415

            post_migrate.connect(register_pint_composite_types, sender=self)

            from .lookups import get_pint_field_lookups  # pylint: disable=C0415

            get_pint_field_lookups()
            set_decimal_precision()
