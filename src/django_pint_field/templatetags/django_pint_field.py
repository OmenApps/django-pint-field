"""Custom template tags for the Django Pint Field app."""

import logging
from decimal import Decimal
from decimal import InvalidOperation

from django import template

from django_pint_field.helpers import get_quantizing_string
from django_pint_field.models import PintFieldProxy
from django_pint_field.units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity

register = template.Library()


@register.filter
def with_digits(obj, decimal_places):
    """Display a Pint Field value with to specific number of decimal places."""
    if isinstance(obj, PintFieldProxy):
        obj = obj.quantity
    if not isinstance(obj, Quantity):
        return obj

    if isinstance(decimal_places, str):
        try:
            decimal_places = int(decimal_places)
        except ValueError as e:
            logger.error("Invalid decimal_places: %s, %s", decimal_places, e)
            return obj

    try:
        quantizing_string = get_quantizing_string(decimal_places=decimal_places)
        return Quantity(obj.magnitude.quantize(Decimal(quantizing_string)), obj.units)

    except (AttributeError, InvalidOperation) as e:
        logger.error("Invalid operation: %s to %s, %s", obj, decimal_places, e)
        return obj


@register.filter
def with_units(obj, units):
    """Convert a Pint Field value to a specific unit."""
    if isinstance(obj, PintFieldProxy):
        obj = obj.quantity
    if not isinstance(obj, Quantity):
        return obj
    if units:
        obj = obj.to(units)

    try:
        return obj
    except InvalidOperation as e:
        logger.error("Invalid operation: %s to %s, %s", obj, units, e)
        return obj


@register.filter
def pint_str_format(obj, format_str):
    """Specify the format string for a Pint Field value."""
    if isinstance(obj, PintFieldProxy):
        obj = obj.quantity
    if not isinstance(obj, Quantity):
        return obj

    try:
        return f"{obj:{format_str}}"
    except ValueError as e:
        logger.error("Invalid format string: %s, %s", format_str, e)
        return obj


@register.filter
def magnitude_only(obj, units=None):
    """Display only the magnitude of a Pint Field value."""
    if isinstance(obj, PintFieldProxy):
        obj = obj.quantity
    if not isinstance(obj, Quantity):
        return obj

    if units:
        try:
            return obj.m_as(units)
        except ValueError as e:
            logger.error("Invalid units: %s, %s", units, e)

    return obj.magnitude


@register.filter
def units_only(obj: Quantity | PintFieldProxy | str) -> str:
    """Display only the units of a Pint Field value."""
    if isinstance(obj, str) and len(obj.split(" ")) > 1:
        return obj.split(" ")[1]
    if isinstance(obj, PintFieldProxy):
        obj = obj.quantity
    if not isinstance(obj, Quantity):
        return obj

    return obj.units
