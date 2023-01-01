import logging
from decimal import Decimal, getcontext
from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.db.models import Lookup
from django.utils.translation import gettext_lazy as _
from io import StringIO
from psycopg2.extensions import register_adapter
from . import (
    get_IntegerPintDBField,
    get_DecimalPintDBField,
    get_BigIntegerPintDBField,
    integer_pint_field_adapter,
    big_integer_pint_field_adapter,
    decimal_pint_field_adapter,
)
from .fields import IntegerPintField, BigIntegerPintField, DecimalPintField
from .exceptions import PintFieldLookupError
from psycopg2.extensions import AsIs


logger = logging.getLogger("watervize.entities_flags")


def check_migrations_complete():
    """Runs the showmigrations command, and returns false if any have not been run yet"""
    out = StringIO()
    call_command("showmigrations", format="plan", stdout=out)
    out.seek(0)
    for line in out.readlines():
        status, name = line.rsplit(" ", 1)
        logger.debug(f"Migration '{name}' status: {status}")
        if "[X]" not in status:
            logger.warning(f"Migration '{name}' incomplete")
            return False
    return True


def get_comparator_from_rhs(rhs_params):
    def extract_comparator(input):
        print(f"input: {input}")
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


def set_decimal_precision():
    """
    If `DJANGO_PINT_FIELD_DECIMAL_PRECISION` is set to an int value greater than 0, the project's
      decimalprecision will be set to that value. Otherwise, it is left as default.
    """
    decimal_precision = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 0)

    if isinstance(decimal_precision, int) and decimal_precision > 0:
        getcontext().prec = decimal_precision


class DjangoPintFieldAppConfig(AppConfig):
    name = "django_pint_field"

    def ready(self):
        if check_migrations_complete():
            # e.g.: x, y = IntegerPintDBField(magnitude=1, units="xyz")

            IntegerPintDBField = get_IntegerPintDBField()
            BigIntegerPintDBField = get_BigIntegerPintDBField()
            DecimalPintDBField = get_DecimalPintDBField()

            register_adapter(IntegerPintDBField, integer_pint_field_adapter)
            register_adapter(BigIntegerPintDBField, big_integer_pint_field_adapter)
            register_adapter(DecimalPintDBField, decimal_pint_field_adapter)

            set_decimal_precision()

            # ToDo: Find a good way to validate in lookups that the lhs and rhs Quantities use the same dimensionality

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
                    modified_rhs_params = get_comparator_from_rhs(rhs_params)  # [AsIs,]
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

                    print(f"RANGE >> lhs: {lhs}, lhs_params: {lhs_params}, rhs: {rhs}, " f"rhs_params: {rhs_params}")

                    modified_rhs_params = get_comparator_from_rhs(rhs_params)  # [[AsIs, AsIs]]
                    rhs = "BETWEEN %s AND %s"

                    print(
                        f"RANGE >> lhs: {lhs}, lhs_params: {lhs_params}, rhs: {rhs}, "
                        f"rhs_params: {rhs_params}, modified_rhs_params: {modified_rhs_params}"
                    )
                    params = lhs_params + modified_rhs_params

                    return "(%s).comparator %s" % (lhs, rhs), params

            class BaseInvalidIExact(Lookup):
                """Base for invalid Lookups"""

                def as_sql(self, compiler, connection):
                    raise PintFieldLookupError("The lookup used is not implemented for django_pint_field.")

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidContains(BaseInvalidIExact):
                lookup_name = "contains"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIcontains(BaseInvalidIExact):
                lookup_name = "icontains"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIn(BaseInvalidIExact):
                lookup_name = "in"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidStartswith(BaseInvalidIExact):
                lookup_name = "startswith"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIstartswith(BaseInvalidIExact):
                lookup_name = "istartswith"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidEndswith(BaseInvalidIExact):
                lookup_name = "endswith"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIendswith(BaseInvalidIExact):
                lookup_name = "iendswith"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidDate(BaseInvalidIExact):
                lookup_name = "date"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidYear(BaseInvalidIExact):
                lookup_name = "year"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIso_year(BaseInvalidIExact):
                lookup_name = "iso_year"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidMonth(BaseInvalidIExact):
                lookup_name = "month"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidDay(BaseInvalidIExact):
                lookup_name = "day"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidWeek(BaseInvalidIExact):
                lookup_name = "week"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidWeek_day(BaseInvalidIExact):
                lookup_name = "week_day"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIso_week_day(BaseInvalidIExact):
                lookup_name = "iso_week_day"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidQuarter(BaseInvalidIExact):
                lookup_name = "quarter"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidTime(BaseInvalidIExact):
                lookup_name = "time"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidHour(BaseInvalidIExact):
                lookup_name = "hour"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidMinute(BaseInvalidIExact):
                lookup_name = "minute"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidSecond(BaseInvalidIExact):
                lookup_name = "second"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidRegex(BaseInvalidIExact):
                lookup_name = "regex"

            @IntegerPintField.register_lookup
            @BigIntegerPintField.register_lookup
            @DecimalPintField.register_lookup
            class PintInvalidIregex(BaseInvalidIExact):
                lookup_name = "iregex"
