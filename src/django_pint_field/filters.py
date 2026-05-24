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
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.fields import RangeField

from .helpers import units_are_dimensionally_compatible
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
        raise ValueError("Enter a number followed by a unit, e.g. '2 kilogram'.")

    raw_magnitude, raw_unit = parts
    try:
        magnitude = Decimal(raw_magnitude)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid magnitude: {raw_magnitude!r}") from exc
    if not magnitude.is_finite():
        raise ValueError(f"Magnitude must be a finite number: {raw_magnitude!r}")

    # ureg.Unit can raise a variety of errors for malformed input
    # (UndefinedUnitError, AssertionError, tokenize.TokenError, ...); normalize
    # them all to ValueError so callers see a clean validation error.
    try:
        unit = ureg.Unit(raw_unit)
    except Exception as exc:
        raise ValueError(f"Invalid or undefined unit: {raw_unit!r}") from exc

    return Quantity(magnitude, unit)


class QuantityFormField(forms.CharField):
    """A text form field that cleans ``"<magnitude> <unit>"`` into a Quantity.

    When ``field_unit`` is supplied (the model field's ``default_unit``), input
    in an incompatible dimension is rejected as a form validation error rather
    than reaching the database and raising at query time.
    """

    def __init__(self, *args, field_unit=None, **kwargs):
        """Store the expected unit for dimensionality validation."""
        self.field_unit = field_unit
        super().__init__(*args, **kwargs)

    def clean(self, value):
        """Parse the raw string into a Quantity, surfacing errors as form errors."""
        value = super().clean(value)
        try:
            quantity = parse_quantity_string(value)
        except ValueError as exc:
            raise DjangoValidationError(str(exc)) from exc

        if (
            quantity is not None
            and self.field_unit is not None
            and not units_are_dimensionally_compatible(ureg, quantity.units, self.field_unit)
        ):
            raise DjangoValidationError(
                f"Unit '{quantity.units}' is not compatible with this field "
                f"(expected a unit measuring the same quantity as '{self.field_unit}')."
            )
        return quantity


class _PintFilterUnitMixin:
    """Inject the model field's ``default_unit`` into the filter's form field.

    Lets ``QuantityFormField`` validate that filter input is dimensionally
    compatible with the field, producing a clean form error instead of a
    query-time exception. Degrades gracefully (no validation) when the model or
    field cannot be resolved, e.g. a filter used outside a FilterSet.
    """

    def _resolve_field_unit(self):
        """Return the target model field's ``default_unit``, or None."""
        model = getattr(self, "model", None)
        if model is None or not self.field_name:
            return None
        try:
            model_field = model._meta.get_field(self.field_name)  # pylint: disable=W0212
        except FieldDoesNotExist:
            return None
        return getattr(model_field, "default_unit", None)

    @property
    def field(self):
        """Build the form field, passing the resolved unit for validation.

        ``field_unit`` is injected into ``self.extra`` (the kwargs django-filter
        forwards to ``field_class``); ``super().field`` then builds and caches it.
        """
        if not hasattr(self, "_field"):
            self.extra.setdefault("field_unit", self._resolve_field_unit())
        return super().field


class PintFieldFilter(_PintFilterUnitMixin, django_filters.Filter):
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
    ``field_unit`` is forwarded to each bound for dimensionality validation.
    """

    def __init__(self, *args, field_unit=None, **kwargs):
        """Build the two optional Quantity-parsing bound fields."""
        fields = (
            QuantityFormField(required=False, field_unit=field_unit),
            QuantityFormField(required=False, field_unit=field_unit),
        )
        kwargs.setdefault("require_all_fields", False)
        super().__init__(fields, *args, **kwargs)


class PintFieldRangeFilter(_PintFilterUnitMixin, django_filters.RangeFilter):
    """Filter a PintField by an inclusive ``[min, max]`` range.

    Inputs are ``"<magnitude> <unit>"`` strings; comparison is cross-unit via
    the base-unit comparator. Either bound may be omitted (open-ended range).
    """

    field_class = QuantityRangeField
