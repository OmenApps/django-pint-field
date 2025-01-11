"""Define the unit register and default format used in the package."""

from .app_settings import DJANGO_PINT_FIELD_DEFAULT_FORMAT
from .app_settings import DJANGO_PINT_FIELD_UNIT_REGISTER


# The unit register that was defined in the settings
ureg = DJANGO_PINT_FIELD_UNIT_REGISTER
ureg.formatter.default_format = DJANGO_PINT_FIELD_DEFAULT_FORMAT
