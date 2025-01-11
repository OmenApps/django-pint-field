"""Custom template tags for the Django Pint Field app."""

import logging
from decimal import Decimal
from decimal import InvalidOperation

from django import template

from django_pint_field.models import PintFieldProxy
from django_pint_field.units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity

register = template.Library()


@register.filter
def decimal_display(obj, decimal_places, units=None):
    """Display a Pint Field value with a specific number of decimal places."""
    if isinstance(obj, PintFieldProxy):
        obj = obj.value
    if not isinstance(obj, Quantity):
        return obj
    if units:
        obj = obj.to(units)

    return f"{obj.magnitude:.{decimal_places}f} {obj.units}"
