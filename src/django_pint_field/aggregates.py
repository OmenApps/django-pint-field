"""Provides aggregation functions for django_pint_field."""

from django.db.models import Aggregate
from django.db.models.expressions import Star
from django.db.models.fields import IntegerField
from django.db.models.functions.mixins import NumericOutputFieldMixin

TEMPLATE = "%(function)s((%(distinct)s%(expressions)s).comparator)"


class PintAvg(NumericOutputFieldMixin, Aggregate):
    """Provides average aggregation for PintFields."""

    function = "AVG"
    name = "PintAvg"
    template = TEMPLATE
    allow_distinct = True


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
        if expression == "*":
            expression = Star()
        if isinstance(expression, Star) and filter is not None:
            raise ValueError("Star cannot be used with filter. Please specify a field.")
        super().__init__(expression, filter=filter, **extra)


class PintMax(Aggregate):
    """Provides max aggregation for PintFields."""

    function = "MAX"
    name = "PintMax"
    template = TEMPLATE


class PintMin(Aggregate):
    """Provides min aggregation for PintFields."""

    function = "MIN"
    name = "PintMin"
    template = TEMPLATE


class PintSum(Aggregate):
    """Provides sum aggregation for PintFields."""

    function = "SUM"
    name = "PintSum"
    template = TEMPLATE
    allow_distinct = True


class PintStdDev(NumericOutputFieldMixin, Aggregate):
    """Provides standard deviation aggregation for PintFields."""

    name = "PintStdDev"
    template = TEMPLATE

    def __init__(self, expression, sample=False, **extra):
        self.function = "STDDEV_SAMP" if sample else "STDDEV_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        return {**super()._get_repr_options(), "sample": self.function == "STDDEV_SAMP"}


class PintVariance(NumericOutputFieldMixin, Aggregate):
    """Provides variance aggregation for PintFields."""

    name = "PintVariance"
    template = TEMPLATE

    def __init__(self, expression, sample=False, **extra):
        self.function = "VAR_SAMP" if sample else "VAR_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        return {**super()._get_repr_options(), "sample": self.function == "VAR_SAMP"}
