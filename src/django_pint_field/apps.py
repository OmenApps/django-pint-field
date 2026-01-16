"""AppConfig for the django_pint_field app."""

import logging
from decimal import getcontext

from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.db.models.signals import post_migrate

from .app_settings import DJANGO_PINT_FIELD_DECIMAL_PRECISION


logger = logging.getLogger(__name__)

# Global flag to ensure composite types are only registered once
_composite_types_registered = False


def set_decimal_precision():
    """Sets the decimal precision for the project.

    If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
      decimalprecision will be set to that value. Otherwise, it is left as default (28 digits).

    See: https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision
    """
    decimal_precision = DJANGO_PINT_FIELD_DECIMAL_PRECISION

    if isinstance(decimal_precision, int) and decimal_precision > 0:
        getcontext().prec = decimal_precision


def register_composite_types_once(sender=None, connection=None, **kwargs):
    """Register composite types once on first database connection.

    This function handles registration from both connection_created and post_migrate signals.
    It ensures types are only registered once using a global flag.
    """
    global _composite_types_registered  # pylint: disable=W0603
    if _composite_types_registered:
        return

    # Import here to avoid circular imports
    from django.db import connection as default_connection  # pylint: disable=C0415

    # Use the provided connection or fall back to default
    conn = connection if connection is not None else default_connection

    # Only register for PostgreSQL
    if conn.vendor != "postgresql":
        return

    try:
        from .models import register_pint_composite_types  # pylint: disable=C0415

        register_pint_composite_types(sender, connection=conn, **kwargs)
        _composite_types_registered = True
        logger.debug("Pint composite types registered successfully")
    except Exception as e:  # pylint: disable=W0718
        # Log the error but don't prevent the app from starting
        # Types will be registered on next connection or after migrations
        logger.debug("Could not register composite types yet: %s", e)


class DjangoPintFieldAppConfig(AppConfig):
    """AppConfig for the django_pint_field app."""

    name = "django_pint_field"

    def ready(self):
        """Runs when the app is ready.

        Uses a hybrid approach:
        - connection_created signal: registers types on first DB connection
        - post_migrate signal: registers types after migrations complete
        - Lookups and decimal precision are registered immediately (no DB needed)
        """
        # Connect signal handlers for composite type registration
        # These will only trigger when a database connection is actually made
        connection_created.connect(register_composite_types_once)
        post_migrate.connect(register_composite_types_once, sender=self)

        # Register lookups - this doesn't require database access
        from .lookups import get_pint_field_lookups  # pylint: disable=C0415

        get_pint_field_lookups()

        # Set decimal precision - this doesn't require database access
        set_decimal_precision()
