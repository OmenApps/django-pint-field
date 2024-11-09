"""Provides aggregation functions for django_pint_field."""

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Aggregate
from django.db.models import IntegerField
from django.db.models.expressions import Star
from django.db.models.functions import Cast

from .units import ureg


Quantity = ureg.Quantity


TEMPLATE = "%(function)s((%(distinct)s%(expressions)s).comparator)"


class QuantityOutputFieldMixin:
    """Mixin to convert aggregate results to Pint Quantity objects."""

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

    def convert_value(self, value, expression, connection):  # pylint: disable=W0613
        """Prepare to convert the value, based on the field type."""
        field = self.output_field
        internal_type = field.get_internal_type()

        self.resolve_expression()

        if value is None:
            return None

        if internal_type == "DecimalPintField":
            converted = self.convert_to_quantity(Decimal(str(value)), self.original_field)
            return converted
        elif internal_type == "IntegerPintField":
            converted = self.convert_to_quantity(value, self.original_field)
            return converted
        elif internal_type == "BigIntegerPintField":
            converted = self.convert_to_quantity(value, self.original_field)
            return converted

        return self._convert_value_noop

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
