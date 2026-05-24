"""django-filter integration for django_pint_field.

Filters parse a "<magnitude> <unit>" string into a pint Quantity and apply the
package's existing comparator-based field lookups, which compare across units
in PostgreSQL.
"""

from __future__ import annotations

from decimal import Decimal
from decimal import InvalidOperation

import django_filters
from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.fields import RangeField
from pint.errors import UndefinedUnitError

from .units import ureg


Quantity = ureg.Quantity


def parse_quantity_string(value: str | None) -> Quantity | None:
    """Parse ``"<magnitude> <unit>"`` into a Quantity, or None if blank.

    Args:
        value: A string like ``"2 kilogram"``, or None/blank.

    Returns:
        A pint Quantity, or None when the input is None or blank.

    Raises:
        ValueError: if the string is malformed, the magnitude is not numeric,
            or the unit is undefined.
    """
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None

    parts = value.split()
    if len(parts) != 2:
        raise ValueError("Expected '<magnitude> <unit>', e.g. '2 kilogram'.")

    raw_magnitude, raw_unit = parts
    try:
        magnitude = Decimal(raw_magnitude)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid magnitude: {raw_magnitude!r}") from exc

    try:
        unit = ureg.Unit(raw_unit)
    except UndefinedUnitError as exc:
        raise ValueError(f"Undefined unit: {raw_unit!r}") from exc

    return Quantity(magnitude, unit)


class QuantityFormField(forms.CharField):
    """A text form field that cleans ``"<magnitude> <unit>"`` into a Quantity."""

    def clean(self, value):
        """Parse the raw string into a Quantity, surfacing parse errors as form errors."""
        value = super().clean(value)
        try:
            return parse_quantity_string(value)
        except ValueError as exc:
            raise DjangoValidationError(str(exc)) from exc


class PintFieldFilter(django_filters.Filter):
    """Filter a PintField by a single comparison (gt/gte/lt/lte/exact).

    The supplied value is a ``"<magnitude> <unit>"`` string; comparison happens
    across units via the field's base-unit comparator.
    """

    field_class = QuantityFormField

    def filter(self, qs, value):
        """Apply ``field_name__lookup_expr=value`` when a Quantity is provided."""
        if value is None:
            return qs
        lookup = f"{self.field_name}__{self.lookup_expr}"
        return qs.filter(**{lookup: value})


class QuantityRangeField(RangeField):
    """A django-filter RangeField whose two bounds parse Quantity strings.

    Renders two ``"<magnitude> <unit>"`` inputs suffixed ``_min`` / ``_max``
    (django-filter's ``RangeWidget`` convention); either bound may be omitted.
    """

    def __init__(self, *args, **kwargs):
        """Build the two optional Quantity-parsing bound fields."""
        fields = (QuantityFormField(required=False), QuantityFormField(required=False))
        kwargs.setdefault("require_all_fields", False)
        super().__init__(fields, *args, **kwargs)


class PintFieldRangeFilter(django_filters.RangeFilter):
    """Filter a PintField by an inclusive ``[min, max]`` range.

    Inputs are ``"<magnitude> <unit>"`` strings; comparison is cross-unit via
    the base-unit comparator. Either bound may be omitted (open-ended range).
    """

    field_class = QuantityRangeField
