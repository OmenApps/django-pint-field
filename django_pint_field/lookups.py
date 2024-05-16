"""Custom lookups for django_pint_field."""

from django.db.models import Lookup
from django.utils.translation import gettext_lazy as _
from psycopg2.extensions import AsIs

from .exceptions import PintFieldLookupError
from .models import BigIntegerPintField, DecimalPintField, IntegerPintField

# ToDo: Find a good way to validate in lookups that the lhs and rhs Quantities use the same dimensionality

# def get_comparator_from_lhs(lhs_params):
#     """Extracts the comparator from the left-hand side of the lookup.

#     Args:
#         lhs_params (list): The left-hand side of the lookup.

#     Returns:
#         list: The comparator extracted from the left-hand side of the lookup.
#     """

#     def extract_comparator(param):
#         """Extracts the comparator from the left-hand side of the lookup."""
#         return str(param)[1:].split(":", maxsplit=1)[0]

#     if (
#         isinstance(lhs_params, (list, tuple))
#         and isinstance(lhs_params[0], (list, tuple))
#         and isinstance(lhs_params[0][0], AsIs)
#     ):
#         return [extract_comparator(param) for param in lhs_params[0]]

#     if isinstance(lhs_params, (list, tuple)) and isinstance(lhs_params[0], AsIs):
#         comparator = extract_comparator(lhs_params[0])
#         return [
#             comparator,
#         ]

#     return [""]


def get_comparator_from_rhs(rhs_params):
    """Extracts the comparator from the right-hand side of the lookup.

    Args:
        rhs_params (list): The right-hand side of the lookup.

    Returns:
        list: The comparator extracted from the right-hand side of the lookup.
    """

    def extract_comparator(param):
        """Extracts the comparator from the right-hand side of the lookup."""
        return str(param)[1:].split(":", maxsplit=1)[0]

    if (
        isinstance(rhs_params, (list, tuple))
        and isinstance(rhs_params[0], (list, tuple))
        and isinstance(rhs_params[0][0], AsIs)
    ):
        return [extract_comparator(param) for param in rhs_params[0]]

    if isinstance(rhs_params, (list, tuple)) and isinstance(rhs_params[0], AsIs):
        comparator = extract_comparator(rhs_params[0])
        return [
            comparator,
        ]

    return [""]


# def compare_rhs_with_lhs(lhs, rhs, comparator):
#     """Compares the right-hand side with the left-hand side of the lookup.

#     Args:
#         lhs (str): The left-hand side of the lookup.
#         rhs (str): The right-hand side of the lookup.
#         comparator (str): The comparator extracted from the right-hand side of the lookup.

#     Returns:
#         str: The SQL for the comparison of the right-hand side with the left-hand side of the lookup.
#     """

#     if comparator == "quantity":
#         return f"({lhs}).quantity {rhs}"

#     if comparator == "magnitude":
#         return f"({lhs}).magnitude {rhs}"

#     if comparator == "units":
#         return f"({lhs}).units {rhs}"

#     return f"({lhs}).comparator {rhs}"


def get_pint_field_lookups():  # pylint: disable=too-many-locals
    """Registers lookups for PintField"""

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintGreaterThan(Lookup):
        """Greater-than lookup for comparing Quantities"""

        lookup_name = "gt"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator > %s" % (lhs, rhs), params  # pylint: disable=consider-using-f-string

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintGreaterThanOrEqual(Lookup):
        """Greater-than-or-equal lookup for comparing Quantities"""

        lookup_name = "gte"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator >= %s" % (lhs, rhs), params  # pylint: disable=consider-using-f-string

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintLessThan(Lookup):
        """Less-than lookup for comparing Quantities"""

        lookup_name = "lt"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator < %s" % (lhs, rhs), params  # pylint: disable=consider-using-f-string

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintLessThanOrEqual(Lookup):
        """Less-than-or-equal lookup for comparing Quantities"""

        lookup_name = "lte"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator <= %s" % (lhs, rhs), params  # pylint: disable=consider-using-f-string

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintRange(Lookup):
        """Range lookup for comparing Quantities"""

        lookup_name = "range"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)

            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            rhs = "BETWEEN %s AND %s"

            params = lhs_params + modified_rhs_params

            return "(%s).comparator %s" % (lhs, rhs), params  # pylint: disable=consider-using-f-string

    class BaseInvalidLookup(Lookup):
        """Base for invalid Lookups"""

        def as_sql(self, compiler, connection):
            raise PintFieldLookupError("The lookup used is not implemented for django_pint_field.")

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidContains(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "contains"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIContains(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "icontains"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIn(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "in"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidStartsWith(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "startswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIStartsWith(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "istartswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidEndsWith(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "endswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIEndsWith(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "iendswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidTruncDate(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "date"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractYear(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "year"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractIsoYear(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "iso_year"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractMonth(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "month"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractDay(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractWeek(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "week"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractIsoWeekDay(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "iso_week_day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractWeekDay(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "week_day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractQuarter(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "quarter"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidTruncTime(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "time"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractHour(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "hour"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractMinute(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "minute"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractSecond(BaseInvalidLookup):
        """Invalid lookup for comparing Quantities"""

        lookup_name = "second"
