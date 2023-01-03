from django.conf import settings
from pint import UnitRegistry, set_application_registry

# Define default unit register
DJANGO_PINT_FIELD_UNIT_REGISTER = getattr(settings, "DJANGO_PINT_FIELD_UNIT_REGISTER", UnitRegistry())
# Set as default application registry for i.e. for pickle
set_application_registry(DJANGO_PINT_FIELD_UNIT_REGISTER)
