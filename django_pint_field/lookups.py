from django.db.models import Lookup
from django.utils.translation import gettext_lazy as _
from psycopg2.extensions import AsIs

from .exceptions import PintFieldLookupError
from .models import BigIntegerPintField, DecimalPintField, IntegerPintField

# ToDo: Find a good way to validate in lookups that the lhs and rhs Quantities use the same dimensionality


def get_comparator_from_rhs(rhs_params):
    def extract_comparator(input):
        return str(input)[1:].split(":")[0]

    if (
        isinstance(rhs_params, (list, tuple))
        and isinstance(rhs_params[0], (list, tuple))
        and isinstance(rhs_params[0][0], AsIs)
    ):
        return [extract_comparator(param) for param in rhs_params[0]]

    elif isinstance(rhs_params, (list, tuple)) and isinstance(rhs_params[0], AsIs):
        comparator = extract_comparator(rhs_params[0])
        return [
            comparator,
        ]

    else:
        return [""]


def get_pint_field_lookups():
    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintGreaterThan(Lookup):
        lookup_name = "gt"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator > %s" % (lhs, rhs), params

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintLessThan(Lookup):
        lookup_name = "lt"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator < %s" % (lhs, rhs), params

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintGreaterThanOrEqual(Lookup):
        lookup_name = "gte"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator >= %s" % (lhs, rhs), params

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintLessThanOrEqual(Lookup):
        lookup_name = "lte"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            params = lhs_params + modified_rhs_params

            return "(%s).comparator <= %s" % (lhs, rhs), params

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintRange(Lookup):
        lookup_name = "range"

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)

            modified_rhs_params = get_comparator_from_rhs(rhs_params)
            rhs = "BETWEEN %s AND %s"

            params = lhs_params + modified_rhs_params

            return "(%s).comparator %s" % (lhs, rhs), params

    class BaseInvalidLookup(Lookup):
        """Base for invalid Lookups"""

        def as_sql(self, compiler, connection):
            raise PintFieldLookupError("The lookup used is not implemented for django_pint_field.")

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidContains(BaseInvalidLookup):
        lookup_name = "contains"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIContains(BaseInvalidLookup):
        lookup_name = "icontains"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIn(BaseInvalidLookup):
        lookup_name = "in"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidStartsWith(BaseInvalidLookup):
        lookup_name = "startswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIStartsWith(BaseInvalidLookup):
        lookup_name = "istartswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidEndsWith(BaseInvalidLookup):
        lookup_name = "endswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidIEndsWith(BaseInvalidLookup):
        lookup_name = "iendswith"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidTruncDate(BaseInvalidLookup):
        lookup_name = "date"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractYear(BaseInvalidLookup):
        lookup_name = "year"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractIsoYear(BaseInvalidLookup):
        lookup_name = "iso_year"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractMonth(BaseInvalidLookup):
        lookup_name = "month"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractDay(BaseInvalidLookup):
        lookup_name = "day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractWeek(BaseInvalidLookup):
        lookup_name = "week"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractIsoWeekDay(BaseInvalidLookup):
        lookup_name = "iso_week_day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractWeekDay(BaseInvalidLookup):
        lookup_name = "week_day"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractQuarter(BaseInvalidLookup):
        lookup_name = "quarter"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidTruncTime(BaseInvalidLookup):
        lookup_name = "time"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractHour(BaseInvalidLookup):
        lookup_name = "hour"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractMinute(BaseInvalidLookup):
        lookup_name = "minute"

    @IntegerPintField.register_lookup
    @BigIntegerPintField.register_lookup
    @DecimalPintField.register_lookup
    class PintInvalidExtractSecond(BaseInvalidLookup):
        lookup_name = "second"
