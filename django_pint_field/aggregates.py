from django.db.models import Aggregate
from django.db.models.expressions import Star
from django.db.models.fields import IntegerField
from django.db.models.functions.mixins import NumericOutputFieldMixin


class PintAvg(NumericOutputFieldMixin, Aggregate):
    function = "AVG"
    name = "PintAvg"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"
    allow_distinct = True


class PintCount(Aggregate):
    function = "COUNT"
    name = "PintCount"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"
    output_field = IntegerField()
    allow_distinct = True
    empty_result_set_value = 0

    def __init__(self, expression, filter=None, **extra):
        if expression == "*":
            expression = Star()
        if isinstance(expression, Star) and filter is not None:
            raise ValueError("Star cannot be used with filter. Please specify a field.")
        super().__init__(expression, filter=filter, **extra)


class PintMax(Aggregate):
    function = "MAX"
    name = "PintMax"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"


class PintMin(Aggregate):
    function = "MIN"
    name = "PintMin"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"


class PintSum(Aggregate):
    function = "SUM"
    name = "PintSum"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"
    allow_distinct = True


class PintStdDev(NumericOutputFieldMixin, Aggregate):
    name = "PintStdDev"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"

    def __init__(self, expression, sample=False, **extra):
        self.function = "STDDEV_SAMP" if sample else "STDDEV_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        return {**super()._get_repr_options(), "sample": self.function == "STDDEV_SAMP"}


class PintVariance(NumericOutputFieldMixin, Aggregate):
    name = "PintVariance"
    template = "%(function)s((%(distinct)s%(expressions)s).comparator)"

    def __init__(self, expression, sample=False, **extra):
        self.function = "VAR_SAMP" if sample else "VAR_POP"
        super().__init__(expression, **extra)

    def _get_repr_options(self):
        return {**super()._get_repr_options(), "sample": self.function == "VAR_SAMP"}
