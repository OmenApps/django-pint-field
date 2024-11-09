"""Custom lookups for django_pint_field.

Implements custom lookups and provides errors for invalid lookups.
"""

from collections import namedtuple
from typing import Any

from django.db.models import Lookup

from .exceptions import PintFieldLookupError
from .helpers import get_base_unit_magnitude
from .models import BigIntegerPintField
from .models import DecimalPintField
from .models import IntegerPintField
from .units import ureg


Quantity = ureg.Quantity

PintFieldComposite = namedtuple("pint_field", ["comparator", "magnitude", "units"])


def get_comparator_from_rhs(rhs_params: Any) -> list[str]:
    """Extracts the comparator from the right-hand side of the lookup.

    Args:
        rhs_params: The right-hand side parameters from the lookup

    Returns:
        List of comparator strings
    """

    def extract_comparator(param: Any) -> str:
        if isinstance(param, Quantity):
            return str(get_base_unit_magnitude(param))
        if isinstance(param, PintFieldComposite):
            return str(param.comparator)
        if isinstance(param, (int, float, str)):
            return str(param)
        return ""

    if isinstance(rhs_params, (list, tuple)):
        if len(rhs_params) >= 1:
            inner_params = rhs_params[0]
            if isinstance(inner_params, (list, tuple)):
                return [extract_comparator(param) for param in inner_params]
            return [extract_comparator(inner_params)]
    return [extract_comparator(rhs_params)]


def get_pint_field_lookups():  # pylint: disable=too-many-locals
    """Registers lookups for PintField."""

    class BasePintLookup(Lookup):  # pylint: disable=W0223
        """Base class for PintField lookups."""

        operator = ""

        def process_rhs(self, compiler, connection) -> tuple[str, list[str]]:
            rhs, params = super().process_rhs(compiler, connection)
            modified_params = get_comparator_from_rhs(params)
            return rhs, modified_params

        def as_sql(self, compiler, connection) -> tuple[str, list[str]]:
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            params = lhs_params + rhs_params
            return f"({lhs}).comparator {self.operator} %s", params

    class PintGreaterThan(BasePintLookup):  # pylint: disable=W0223
        """Greater than lookup for comparing Quantities."""

        lookup_name = "gt"
        operator = ">"

    class PintGreaterThanOrEqual(BasePintLookup):  # pylint: disable=W0223
        """Greater than or equal lookup for comparing Quantities."""

        lookup_name = "gte"
        operator = ">="

    class PintLessThan(BasePintLookup):  # pylint: disable=W0223
        """Less than lookup for comparing Quantities."""

        lookup_name = "lt"
        operator = "<"

    class PintLessThanOrEqual(BasePintLookup):  # pylint: disable=W0223
        """Less than or equal lookup for comparing Quantities."""

        lookup_name = "lte"
        operator = "<="

    class PintExact(BasePintLookup):  # pylint: disable=W0223
        """Exact lookup for comparing Quantities."""

        lookup_name = "exact"
        operator = "="

    class PintRange(Lookup):  # pylint: disable=W0223
        """Range lookup for comparing Quantities."""

        lookup_name = "range"

        def as_sql(self, compiler, connection) -> tuple[str, list[str]]:
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params
            return f"({lhs}).comparator BETWEEN %s AND %s", params

    class BaseInvalidLookup(Lookup):  # pylint: disable=W0223
        """Base for invalid Lookups."""

        def as_sql(self, compiler, connection):
            raise PintFieldLookupError("The lookup used is not implemented for django_pint_field.")

    class PintInvalidContains(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "contains"

    class PintInvalidIContains(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "icontains"

    class PintInvalidIn(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "in"

    class PintInvalidStartsWith(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "startswith"

    class PintInvalidIStartsWith(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "istartswith"

    class PintInvalidEndsWith(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "endswith"

    class PintInvalidIEndsWith(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "iendswith"

    class PintInvalidTruncDate(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "date"

    class PintInvalidExtractYear(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "year"

    class PintInvalidExtractIsoYear(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "iso_year"

    class PintInvalidExtractMonth(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "month"

    class PintInvalidExtractDay(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "day"

    class PintInvalidExtractWeek(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "week"

    class PintInvalidExtractIsoWeekDay(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "iso_week_day"

    class PintInvalidExtractWeekDay(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "week_day"

    class PintInvalidExtractQuarter(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "quarter"

    class PintInvalidTruncTime(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "time"

    class PintInvalidExtractHour(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "hour"

    class PintInvalidExtractMinute(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "minute"

    class PintInvalidExtractSecond(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "second"

    class PintInvalidRegex(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "regex"

    class PintInvalidIRegex(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "iregex"

    class PintInvalidSearch(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "search"

    class PintInvalidISearch(BaseInvalidLookup):  # pylint: disable=W0223
        """Invalid lookup for comparing Quantities."""

        lookup_name = "isearch"

    # Register lookups for all field types
    for field_class in [IntegerPintField, BigIntegerPintField, DecimalPintField]:
        for lookup_class in [
            PintGreaterThan,
            PintGreaterThanOrEqual,
            PintLessThan,
            PintLessThanOrEqual,
            PintExact,
            PintRange,
            PintInvalidContains,
            PintInvalidIContains,
            PintInvalidIn,
            PintInvalidStartsWith,
            PintInvalidIStartsWith,
            PintInvalidEndsWith,
            PintInvalidIEndsWith,
            PintInvalidTruncDate,
            PintInvalidExtractYear,
            PintInvalidExtractIsoYear,
            PintInvalidExtractMonth,
            PintInvalidExtractDay,
            PintInvalidExtractWeek,
            PintInvalidExtractIsoWeekDay,
            PintInvalidExtractWeekDay,
            PintInvalidExtractQuarter,
            PintInvalidTruncTime,
            PintInvalidExtractHour,
            PintInvalidExtractMinute,
            PintInvalidExtractSecond,
            PintInvalidRegex,
            PintInvalidIRegex,
            PintInvalidSearch,
            PintInvalidISearch,
        ]:
            field_class.register_lookup(lookup_class)
