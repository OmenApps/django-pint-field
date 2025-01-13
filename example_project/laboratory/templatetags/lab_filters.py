"""Custom template filters for the laboratory app."""

import logging
from decimal import Decimal
from decimal import InvalidOperation

from django import template

from django_pint_field.units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using a variable as the key."""
    value = dictionary.get(key, dictionary.get(str(key), None))
    return value


@register.filter
def slice_map(value):
    """Convert a string of key:value pairs into a dictionary.

    Example inputs:
        "sm:8,md:12,lg:16"  ->  {'sm': '8', 'md': '12', 'lg': '16'}
        "1:Low,2:Medium,3:High"  ->  {'1': 'Low', '2': 'Medium', '3': 'High'}
    """
    if not value:
        logger.debug("slice_map: No value provided")
        return {}

    result = {}
    pairs = value.split(",")

    for pair in pairs:
        if ":" in pair:
            key, val = pair.strip().split(":")
            result[key.strip()] = val.strip()

    return result


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if isinstance(arg, (int, float)):
            arg = Decimal(str(arg))
        return value * arg
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.exception("Error multiplying values: %s", e)
        return Decimal(0)


@register.filter
def subtract(value, arg):
    """Subtract the argument from the value."""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if isinstance(arg, (int, float)):
            arg = Decimal(str(arg))
        return value - arg
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.exception("Error subtracting values: %s", e)
        return Decimal(0)


@register.filter
def add(value, arg):
    """Add the argument to the value."""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if isinstance(arg, (int, float)):
            arg = Decimal(str(arg))
        return value + arg
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.exception("Error adding values: %s", e)
        return Decimal(0)


@register.filter
def divide(value, arg):
    """Divide the value by the argument."""
    try:
        if isinstance(value, str):
            value = Decimal(value)
        if isinstance(arg, str):
            arg = Decimal(arg)
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if isinstance(arg, (int, float)):
            arg = Decimal(str(arg))
        return value / arg
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.exception("Error dividing values: %s", e)
        return Decimal(0)


@register.filter
def filter_high_risk(laboratories):
    """Filter laboratories with high risk level (4 or 5)."""
    return [lab for lab in laboratories if lab.containment_level >= 4]


@register.filter
def filter_evil(laboratories):
    """Filter evil laboratories."""
    return [lab for lab in laboratories if lab.is_evil]


@register.filter
def avg_stability(laboratories):
    """Calculate average dimensional stability."""
    if not laboratories:
        return 0
    return sum(lab.dimensional_stability for lab in laboratories) / len(laboratories)


@register.filter
def get_attr(obj, args):
    """Get an attribute of an object dynamically.

    Usage: {{ object|get_attr:"attribute_name" }}
           {{ object|get_attr:"method_name" }}
    """
    try:
        arg_list = [arg.strip() for arg in args.split(",")]
        attr = arg_list[0]
        if hasattr(obj, attr):
            result = getattr(obj, attr)
            if callable(result):
                return result()
            return result
        return None
    except (IndexError, AttributeError):
        return None


@register.filter
def get_display_value(obj, field_name):
    """Get the display value for an object using the specified field name."""
    if not field_name:
        return str(obj)
    try:
        # Split on dots for nested attributes
        attrs = field_name.split(".")
        value = obj
        for attr in attrs:
            value = getattr(value, attr)
        if callable(value):
            value = value()
        return value
    except (AttributeError, TypeError):
        return str(obj)
