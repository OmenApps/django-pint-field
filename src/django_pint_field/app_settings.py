"""Settings for django_pint_field."""

from decimal import Decimal

from django.conf import settings
from pint import UnitRegistry
from pint import set_application_registry


# Define default unit register
# See: https://pint.readthedocs.io/en/stable/advanced/defining.html
DJANGO_PINT_FIELD_UNIT_REGISTER = getattr(
    settings,
    "DJANGO_PINT_FIELD_UNIT_REGISTER",
    UnitRegistry(non_int_type=Decimal),
)
# Set as default application registry for i.e. for pickle
set_application_registry(DJANGO_PINT_FIELD_UNIT_REGISTER)

# Define decimal precision
# If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
#   decimalprecision will be set to that value. Otherwise, it is left as default (28 digits).
# See: https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision
DJANGO_PINT_FIELD_DECIMAL_PRECISION = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 0)

# Define default format
# If `DJANGO_PINT_FIELD_DEFAULT_FORMAT` is set to a string value, the project's default format
#   will be set to that value. Otherwise, it is left as default ("D").
# See: https://pint.readthedocs.io/en/stable/user/formatting.html for other options.
DJANGO_PINT_FIELD_DEFAULT_FORMAT = getattr(settings, "DJANGO_PINT_FIELD_DEFAULT_FORMAT", "D")
