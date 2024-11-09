"""Settings for django_pint_field."""

from django.conf import settings
from pint import UnitRegistry
from pint import set_application_registry


# Define default unit register
DJANGO_PINT_FIELD_UNIT_REGISTER = getattr(settings, "DJANGO_PINT_FIELD_UNIT_REGISTER", UnitRegistry())
# Set as default application registry for i.e. for pickle
set_application_registry(DJANGO_PINT_FIELD_UNIT_REGISTER)

# Define decimal precision
# If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
#   decimalprecision will be set to that value. Otherwise, it is left as default (28 digits).
#
# See: https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision
DJANGO_PINT_FIELD_DECIMAL_PRECISION = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 0)
