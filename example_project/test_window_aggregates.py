"""Tests for Pint aggregates in window expressions.

Covers the two halves of the window-safety contract:

1. A bare ``django.db.models.Window`` around a unit-bearing Pint aggregate must
   fail loudly, because ``Window`` bypasses the aggregate's unit conversion and
   would otherwise return a base-unit number wearing the wrong unit.
2. ``PintWindow`` is the supported, unit-aware wrapper that returns a correctly
   converted ``PintFieldProxy`` running/partitioned result.
"""

from decimal import Decimal

import pytest
from django.db import NotSupportedError
from django.db.models import F
from django.db.models import Window

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintCount
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintMedian
from django_pint_field.aggregates import PintMin
from django_pint_field.aggregates import PintPercentile
from django_pint_field.aggregates import PintStdDev
from django_pint_field.aggregates import PintSum
from django_pint_field.aggregates import PintVariance
from django_pint_field.aggregates import PintWindow
from django_pint_field.helpers import PintFieldProxy
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import EmptyHayBaleDecimal
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.fixture
def reservoirs(db):
    """Create three rows in grams (base unit kilogram differs from default)."""
    a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
    b = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("200"), ureg.gram), name="b")
    c = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("300"), ureg.gram), name="c")
    return a, b, c


class TestBareWindowFailsLoudly:
    """A plain Window() around a unit-bearing aggregate must raise, not silently mislead."""

    @pytest.mark.parametrize(
        "aggregate,kwargs",
        [
            (PintSum, {}),
            (PintAvg, {}),
            (PintMax, {}),
            (PintMin, {}),
            (PintStdDev, {}),
            (PintVariance, {}),
            (PintPercentile, {"percentile": 0.5}),
            (PintMedian, {}),
        ],
    )
    def test_bare_window_raises(self, aggregate, kwargs):
        """A bare Window() around any unit-bearing aggregate raises at construction."""
        with pytest.raises(ValueError, match="isn't compatible with OVER clauses"):
            Window(aggregate("weight", **kwargs), order_by=F("pk").asc())

    def test_window_compatible_flag_is_false(self):
        """Unit-bearing aggregates advertise window_compatible = False."""
        assert PintSum.window_compatible is False
        assert PintAvg.window_compatible is False
        assert PintMax.window_compatible is False
        assert PintStdDev.window_compatible is False

    def test_pint_count_still_window_compatible(self):
        """PintCount needs no unit conversion, so a plain Window() stays valid."""
        assert getattr(PintCount, "window_compatible", True) is True
        # Construction must not raise.
        Window(PintCount("weight"), order_by=F("pk").asc())


@pytest.mark.django_db
class TestPintWindowIsCorrect:
    """PintWindow returns a unit-aware, correctly-converted running result."""

    def test_running_sum_values_and_units(self, reservoirs):
        """Running sum is a proxy in the base unit (kilogram) with the right magnitude."""
        rows = list(
            DecimalPintFieldSaveModel.objects.annotate(running=PintWindow(PintSum("weight"), order_by=F("pk").asc()))
            .order_by("pk")
            .values_list("name", "running")
        )

        results = {name: proxy for name, proxy in rows}

        # Every result is a unit-aware proxy, NOT a bare base-unit number.
        for proxy in results.values():
            assert isinstance(proxy, PintFieldProxy)

        # Results come back in the base unit (kilogram), like every other
        # aggregate. The magnitude is correct (0.1 kg == 100 g, etc.).
        assert str(results["a"].quantity.units) == "kilogram"
        assert results["a"].quantity == Quantity(Decimal("100"), ureg.gram)
        assert results["b"].quantity == Quantity(Decimal("300"), ureg.gram)
        assert results["c"].quantity == Quantity(Decimal("600"), ureg.gram)

    def test_integer_field_running_sum(self, db):
        """The IntegerPintField branch of convert_value is exercised in the window path."""
        IntegerPintFieldSaveModel.objects.create(weight=Quantity(100, ureg.gram), name="a")
        IntegerPintFieldSaveModel.objects.create(weight=Quantity(200, ureg.gram), name="b")
        rows = list(
            IntegerPintFieldSaveModel.objects.annotate(running=PintWindow(PintSum("weight"), order_by=F("pk").asc()))
            .order_by("pk")
            .values_list("name", "running")
        )
        results = {name: proxy for name, proxy in rows}
        assert isinstance(results["a"], PintFieldProxy)
        assert results["a"].quantity == Quantity(100, ureg.gram)
        assert results["b"].quantity == Quantity(300, ureg.gram)

    def test_matches_non_window_total(self, reservoirs):
        """The final running-sum row equals the equivalent plain aggregate."""
        plain_total = DecimalPintFieldSaveModel.objects.aggregate(total=PintSum("weight"))["total"]
        last = (
            DecimalPintFieldSaveModel.objects.annotate(running=PintWindow(PintSum("weight"), order_by=F("pk").asc()))
            .order_by("pk")
            .last()
        )
        assert last.running.quantity == plain_total.quantity

    def test_partitioned_window(self, reservoirs):
        """partition_by is supported and converts each partition correctly."""
        rows = list(
            DecimalPintFieldSaveModel.objects.annotate(per_name=PintWindow(PintSum("weight"), partition_by=[F("name")]))
            .order_by("pk")
            .values_list("name", "per_name")
        )
        results = {name: proxy for name, proxy in rows}
        # Each name is unique, so each partition sum equals that row's own weight.
        assert results["a"].quantity == Quantity(Decimal("100"), ureg.gram)
        assert results["b"].quantity == Quantity(Decimal("200"), ureg.gram)
        assert results["c"].quantity == Quantity(Decimal("300"), ureg.gram)

    def test_output_unit_is_respected(self, reservoirs):
        """PintWindow honors the wrapped aggregate's output_unit (distinct from the base unit)."""
        last = (
            DecimalPintFieldSaveModel.objects.annotate(
                running=PintWindow(PintSum("weight", output_unit="pound"), order_by=F("pk").asc())
            )
            .order_by("pk")
            .last()
        )
        # "pound" differs from both the field unit (gram) and the base unit
        # (kilogram), so this genuinely exercises output_unit conversion.
        assert str(last.running.quantity.units) == "pound"
        assert last.running.quantity == Quantity(Decimal("600"), ureg.gram)

    def test_running_avg_and_max_are_converted(self, reservoirs):
        """The convert_value delegation works for aggregates other than SUM."""
        rows = list(
            DecimalPintFieldSaveModel.objects.annotate(
                avg=PintWindow(PintAvg("weight"), order_by=F("pk").asc()),
                mx=PintWindow(PintMax("weight"), order_by=F("pk").asc()),
            )
            .order_by("pk")
            .values_list("name", "avg", "mx")
        )
        results = {name: (avg, mx) for name, avg, mx in rows}

        # Cumulative average: 100; (100+200)/2=150; (100+200+300)/3=200 (grams).
        assert results["a"][0].quantity == Quantity(Decimal("100"), ureg.gram)
        assert results["b"][0].quantity == Quantity(Decimal("150"), ureg.gram)
        assert results["c"][0].quantity == Quantity(Decimal("200"), ureg.gram)
        # Cumulative max: 100; 200; 300 (grams).
        assert results["a"][1].quantity == Quantity(Decimal("100"), ureg.gram)
        assert results["c"][1].quantity == Quantity(Decimal("300"), ureg.gram)
        # Still in the base unit, like every other aggregate.
        assert str(results["a"][0].quantity.units) == "kilogram"

    def test_null_rows_yield_none(self, db):
        """A window SUM over only-NULL rows returns None, not a bogus zero/proxy."""
        EmptyHayBaleDecimal.objects.create(name="a")  # weight is NULL
        EmptyHayBaleDecimal.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="b")
        rows = list(
            EmptyHayBaleDecimal.objects.annotate(running=PintWindow(PintSum("weight"), order_by=F("pk").asc()))
            .order_by("pk")
            .values_list("name", "running")
        )
        results = dict(rows)
        # Row "a": SUM over {NULL} is NULL -> None. Row "b": SUM over {NULL, 100g} = 100g.
        assert results["a"] is None
        assert isinstance(results["b"], PintFieldProxy)
        assert results["b"].quantity == Quantity(Decimal("100"), ureg.gram)

    def test_frame_is_forwarded(self, reservoirs):
        """A custom frame is passed through to Window and actually applied."""
        from django.db.models.expressions import RowRange

        rows = list(
            DecimalPintFieldSaveModel.objects.annotate(
                # CURRENT ROW only: each row's "sum" is just its own weight, not cumulative.
                per_row=PintWindow(PintSum("weight"), order_by=F("pk").asc(), frame=RowRange(start=0, end=0))
            )
            .order_by("pk")
            .values_list("name", "per_row")
        )
        results = dict(rows)
        # If frame were ignored we'd see the cumulative 100/300/600; instead we see 100/200/300.
        assert results["a"].quantity == Quantity(Decimal("100"), ureg.gram)
        assert results["b"].quantity == Quantity(Decimal("200"), ureg.gram)
        assert results["c"].quantity == Quantity(Decimal("300"), ureg.gram)


class TestPintWindowGuards:
    """PintWindow rejects expressions it cannot convert."""

    def test_rejects_pint_count(self):
        """PintCount has no unit to convert, so PintWindow rejects it with TypeError."""
        with pytest.raises(TypeError, match="requires a Pint aggregate"):
            PintWindow(PintCount("weight"), order_by=F("pk").asc())

    def test_rejects_plain_expression(self):
        """A plain F() expression lacks is_pint_aggregate and is rejected too."""
        with pytest.raises(TypeError, match="requires a Pint aggregate"):
            PintWindow(F("weight"), order_by=F("pk").asc())

    @pytest.mark.parametrize(
        "aggregate",
        [PintPercentile("weight", percentile=0.5), PintMedian("weight")],
    )
    def test_rejects_ordered_set_aggregates(self, aggregate):
        """PERCENTILE_CONT cannot be windowed, so PintWindow rejects it at construction."""
        with pytest.raises(NotSupportedError, match="ordered-set aggregate"):
            PintWindow(aggregate, order_by=F("pk").asc())
