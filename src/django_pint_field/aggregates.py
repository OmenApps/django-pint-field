"""Provides aggregation functions for django_pint_field."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Aggregate
from django.db.models import Count
from django.db.models import F
from django.db.models import Func
from django.db.models import IntegerField
from django.db.models.expressions import Star
from django.db.models.functions import Cast

from .helpers import PintFieldConverter
from .helpers import PintFieldProxy
from .units import ureg


Quantity = ureg.Quantity


TEMPLATE = "%(function)s((%(distinct)s%(expressions)s).comparator)"


class QuantityOutputFieldMixin:
    """Mixin to convert aggregate results to PintFieldProxy objects."""

    is_pint_aggregate = True
    original_field = None
    template = TEMPLATE

    def __init__(self, expression, output_unit=None, **extra):
        """Initialize the QuantityOutputFieldMixin object."""
        self.output_unit = output_unit
        super().__init__(expression, **extra)

    def convert_to_quantity(self, value, field):
        """Convert the aggregate result to a Quantity object."""
        if value is None:
            return None

        # Get the base unit from the PintField
        default_unit = field.default_unit
        throwaway_quantity = Quantity(f"1 * {default_unit}")
        base_unit = throwaway_quantity.to_base_units().units

        # Create quantity with base unit
        quantity = Quantity(value, base_unit)

        # Convert to output unit if specified
        if self.output_unit:
            try:
                quantity = quantity.to(self.output_unit)
            except Exception as e:
                raise ValidationError(f"Cannot convert from {base_unit} to {self.output_unit}: {str(e)}") from e

        return quantity

    def as_sql(self, compiler, connection, **extra):
        """Modify the SQL to convert the result to a Quantity object."""
        # Ensure we're working with numeric values in the database
        if not getattr(self.output_field, "numeric_type", False):
            self.source_expressions[0] = Cast(self.source_expressions[0], output_field=self.output_field)
        return super().as_sql(compiler, connection, **extra)

    def resolve_expression(self, *args, **kwargs):
        """Resolved the expression, setting the original_field value."""
        resolved = super().resolve_expression(*args, **kwargs)

        # Store the original field for unit conversion
        self.original_field = resolved.source_expressions[0].field
        return resolved

    def convert_value(self, value, expression, connection):
        """Convert the value to a Quantity object."""
        field = self.output_field
        internal_type = field.get_internal_type()

        self.resolve_expression()

        if value is None:
            return None

        quantity_value = None
        if internal_type == "DecimalPintField":
            quantity_value = self.convert_to_quantity(Decimal(str(value)), self.original_field)
        elif internal_type == "IntegerPintField":
            quantity_value = self.convert_to_quantity(value, self.original_field)

        if quantity_value is None:
            return None

        # Always wrap in a proxy, reusing the field's cached converter when available
        if self.original_field is not None:
            if hasattr(self.original_field, "get_cached_converter"):
                converter = self.original_field.get_cached_converter()
            else:
                converter = PintFieldConverter(self.original_field)
            return PintFieldProxy(quantity_value, converter)

        # Fallback if something is off
        return quantity_value

    def __rand__(self, other: Any):
        """Return None for bitwise operations."""
        return None

    def __ror__(self, other: Any):
        """Return None for bitwise operations."""
        return None

    def __rxor__(self, other: Any):
        """Return None for bitwise operations."""
        return None


class PintCount(Aggregate):
    """Provides count aggregation for PintFields."""

    function = "COUNT"
    name = "PintCount"
    template = TEMPLATE
    output_field = IntegerField()
    allow_distinct = True
    empty_result_set_value = 0

    def __init__(
        self,
        expression,
        *args,
        distinct=False,
        filter=None,
        default=None,
        **extra,
    ):  # pylint: disable=unused-argument disable=redefined-builtin
        """Initialize the PintCount object."""
        if expression == "*":
            expression = Star()
        if isinstance(expression, Star) and filter is not None:
            raise ValidationError("Star cannot be used with filter. Please specify a field.")
        super().__init__(expression, filter=filter, **extra)

    def __rand__(self, other: Any):
        """Return None for bitwise operations."""
        return None

    def __ror__(self, other: Any):
        """Return None for bitwise operations."""
        return None

    def __rxor__(self, other: Any):
        """Return None for bitwise operations."""
        return None


class PintAvg(QuantityOutputFieldMixin, Aggregate):
    """Provides average aggregation for PintFields."""

    function = "AVG"
    name = "PintAvg"
    allow_distinct = True


class PintMax(QuantityOutputFieldMixin, Aggregate):
    """Provides max aggregation for PintFields."""

    function = "MAX"
    name = "PintMax"


class PintMin(QuantityOutputFieldMixin, Aggregate):
    """Provides min aggregation for PintFields."""

    function = "MIN"
    name = "PintMin"


class PintSum(QuantityOutputFieldMixin, Aggregate):
    """Provides sum aggregation for PintFields."""

    function = "SUM"
    name = "PintSum"
    allow_distinct = True


class PintStdDev(QuantityOutputFieldMixin, Aggregate):
    """Provides standard deviation aggregation for PintFields."""

    name = "PintStdDev"

    def __init__(self, expression, sample=False, **extra):
        """Initialize the PintStdDev object."""
        self.function = "STDDEV_SAMP" if sample else "STDDEV_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        """Return the options for the __repr__ method."""
        return {**super()._get_repr_options(), "sample": self.function == "STDDEV_SAMP"}


class PintVariance(QuantityOutputFieldMixin, Aggregate):
    """Provides variance aggregation for PintFields."""

    name = "PintVariance"

    def __init__(self, expression, sample=False, **extra):
        """Initialize the PintVariance object."""
        self.function = "VAR_SAMP" if sample else "VAR_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        """Return the options for the __repr__ method."""
        return {**super()._get_repr_options(), "sample": self.function == "VAR_SAMP"}


class PintPercentile(QuantityOutputFieldMixin, Aggregate):
    """Continuous percentile of a PintField, computed in PostgreSQL.

    Usage::

        Model.objects.aggregate(p=PintPercentile("weight", percentile=0.95))

    ``percentile`` is a float in the closed interval [0, 1]. The result is a
    ``PintFieldProxy`` in the field's base unit, or in ``output_unit`` if given.
    """

    name = "PintPercentile"
    function = "PERCENTILE_CONT"
    template = "%(function)s(%(percentile)s) WITHIN GROUP (ORDER BY (%(expressions)s).comparator)"

    def __init__(self, expression, percentile, output_unit=None, **extra):
        """Validate and store the percentile fraction."""
        if isinstance(percentile, bool) or not isinstance(percentile, (int, float)) or not 0 <= percentile <= 1:
            raise ValidationError("percentile must be a number between 0 and 1 inclusive.")
        self.percentile = percentile
        super().__init__(expression, output_unit=output_unit, **extra)

    def as_sql(self, compiler, connection, **extra):
        """Inject the percentile fraction into the ordered-set template."""
        extra["percentile"] = repr(float(self.percentile))
        return super().as_sql(compiler, connection, **extra)

    def _get_repr_options(self):
        """Include the percentile in the repr."""
        return {**super()._get_repr_options(), "percentile": self.percentile}


class PintMedian(PintPercentile):
    """Median (50th percentile) of a PintField, computed in PostgreSQL.

    Usage::

        Model.objects.aggregate(m=PintMedian("weight"))
    """

    name = "PintMedian"

    def __init__(self, expression, output_unit=None, **extra):
        """Delegate to PintPercentile with percentile fixed at 0.5."""
        super().__init__(expression, percentile=0.5, output_unit=output_unit, **extra)


class _WidthBucket(Func):
    """Wrap PostgreSQL ``width_bucket`` over a Pint field's comparator.

    ``as_sql`` builds the SQL directly (to reach the composite ``.comparator``
    component), so no ``function``/``template`` class attribute is used.
    """

    output_field = IntegerField()

    def __init__(self, field_name, low, high, buckets, **extra):
        """Store the bucket bounds and wrap the field reference."""
        self._low = low
        self._high = high
        self._buckets = buckets
        super().__init__(F(field_name), **extra)

    def as_sql(self, compiler, connection, **extra):
        """Compile to ``width_bucket((col).comparator, low, high, buckets)``."""
        col_sql, col_params = compiler.compile(self.source_expressions[0])
        sql = f"WIDTH_BUCKET(({col_sql}).comparator, %s, %s, %s)"
        return sql, [*col_params, self._low, self._high, self._buckets]


def pint_histogram(queryset, field_name, *, buckets, min_value, max_value):
    """Compute an equi-width histogram of a Pint field in PostgreSQL.

    Args:
        queryset: A queryset of the model owning ``field_name``.
        field_name: Name of the IntegerPintField / DecimalPintField.
        buckets: Number of equal-width buckets (int >= 1).
        min_value: Lower bound as a pint Quantity.
        max_value: Upper bound as a pint Quantity.

    Returns:
        A list of dicts ``{"bucket": int, "lower": Quantity, "upper": Quantity,
        "count": int}`` ordered by bucket, where boundaries are expressed in the
        field's base units. Values below ``min_value`` or at/above ``max_value``
        fall outside the returned buckets (PostgreSQL ``width_bucket`` semantics).

    Raises:
        ValidationError: if ``buckets`` is less than 1.
    """
    if buckets < 1:
        raise ValidationError("buckets must be >= 1")

    # Convert the bounds to base-unit magnitudes directly. (Do NOT route through
    # get_base_unit_magnitude: it rounds non-Decimal magnitudes to int, which
    # would silently corrupt fractional float bounds like 0.5.)
    base_unit = max_value.to_base_units().units
    low = Decimal(str(min_value.to_base_units().magnitude))
    high = Decimal(str(max_value.to_base_units().magnitude))
    width = (high - low) / Decimal(buckets)

    rows = (
        queryset.annotate(_bucket=_WidthBucket(field_name, low, high, buckets))
        .values("_bucket")
        .annotate(count=Count("pk"))
    )
    counts = {row["_bucket"]: row["count"] for row in rows}

    result = []
    for index in range(1, buckets + 1):
        lower = low + width * Decimal(index - 1)
        upper = low + width * Decimal(index)
        result.append(
            {
                "bucket": index,
                "lower": Quantity(lower, base_unit),
                "upper": Quantity(upper, base_unit),
                "count": counts.get(index, 0),
            }
        )
    return result
