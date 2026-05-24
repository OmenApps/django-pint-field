"""Tests for analytics aggregate functions (percentile, median, histogram)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from django_pint_field.aggregates import PintMedian
from django_pint_field.aggregates import PintPercentile
from django_pint_field.aggregates import pint_histogram
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.fixture
def weights_1_to_5():
    """Create five rows weighing 1000, 2000, 3000, 4000, 5000 grams."""
    for grams in (1000, 2000, 3000, 4000, 5000):
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal(str(grams)), ureg.gram), name=f"{grams}g")
    yield


@pytest.mark.django_db
class TestPintPercentile:
    """Tests for the PintPercentile aggregate."""

    def test_p50_equals_middle_value_in_base_units(self, weights_1_to_5):
        """The 50th percentile of 1..5 kg is 3 kg (base units)."""
        result = DecimalPintFieldSaveModel.objects.aggregate(p=PintPercentile("weight", percentile=0.5))["p"]
        assert abs(result.quantity.magnitude - Decimal("3")) < Decimal("0.001")
        assert str(result.quantity.units) == "kilogram"

    def test_p90_interpolates(self, weights_1_to_5):
        """The 90th percentile interpolates to 4.6 kg."""
        result = DecimalPintFieldSaveModel.objects.aggregate(p=PintPercentile("weight", percentile=0.9))["p"]
        assert abs(result.quantity.magnitude - Decimal("4.6")) < Decimal("0.001")

    def test_output_unit_conversion(self, weights_1_to_5):
        """A requested output_unit converts the result."""
        result = DecimalPintFieldSaveModel.objects.aggregate(
            p=PintPercentile("weight", percentile=0.5, output_unit="gram")
        )["p"]
        assert abs(result.quantity.magnitude - Decimal("3000")) < Decimal("0.1")
        assert str(result.quantity.units) == "gram"

    def test_invalid_percentile_raises(self):
        """A percentile outside [0, 1] is rejected at construction."""
        with pytest.raises(ValidationError):
            PintPercentile("weight", percentile=1.5)

    def test_percentile_on_empty_queryset_returns_none(self):
        """With no rows, the percentile aggregate yields None."""
        result = DecimalPintFieldSaveModel.objects.aggregate(p=PintPercentile("weight", percentile=0.5))["p"]
        assert result is None


@pytest.mark.django_db
class TestPintPercentileIntegerField:
    """PintPercentile works on IntegerPintField, exercising the integer branch."""

    def test_p50_integer_field(self):
        """The 50th percentile of integer-backed 1..5 kg is 3 kg.

        PostgreSQL ``PERCENTILE_CONT`` returns double precision, so the integer
        field's result magnitude may be a float; assert on the value, not the type.
        """
        for grams in (1000, 2000, 3000, 4000, 5000):
            IntegerPintFieldSaveModel.objects.create(weight=Quantity(grams, ureg.gram), name=f"{grams}g")
        result = IntegerPintFieldSaveModel.objects.aggregate(p=PintPercentile("weight", percentile=0.5))["p"]
        assert abs(Decimal(str(result.quantity.magnitude)) - Decimal("3")) < Decimal("0.001")
        assert str(result.quantity.units) == "kilogram"


@pytest.mark.django_db
class TestPintMedian:
    """Tests for the PintMedian aggregate."""

    def test_median_of_1_to_5(self, weights_1_to_5):
        """Median of 1..5 kg is 3 kg."""
        result = DecimalPintFieldSaveModel.objects.aggregate(m=PintMedian("weight"))["m"]
        assert abs(result.quantity.magnitude - Decimal("3")) < Decimal("0.001")
        assert str(result.quantity.units) == "kilogram"

    def test_median_output_unit(self, weights_1_to_5):
        """PintMedian forwards output_unit to convert the result."""
        result = DecimalPintFieldSaveModel.objects.aggregate(m=PintMedian("weight", output_unit="gram"))["m"]
        assert abs(result.quantity.magnitude - Decimal("3000")) < Decimal("0.1")
        assert str(result.quantity.units) == "gram"


@pytest.mark.django_db
class TestPintHistogram:
    """Tests for the pint_histogram helper."""

    def test_buckets_count_rows_by_base_unit_range(self, weights_1_to_5):
        """With bounds [0.5, 5.5] kg over 5 buckets, each of 1..5 kg lands in its own bucket."""
        buckets = pint_histogram(
            DecimalPintFieldSaveModel.objects.all(),
            "weight",
            buckets=5,
            min_value=Quantity(Decimal("0.5"), ureg.kilogram),
            max_value=Quantity(Decimal("5.5"), ureg.kilogram),
        )
        counts = [b["count"] for b in buckets]
        assert sum(counts) == 5
        assert counts == [1, 1, 1, 1, 1]

    def test_bucket_boundaries_are_quantities(self, weights_1_to_5):
        """Each bucket exposes lower/upper boundaries as Quantities in base units."""
        buckets = pint_histogram(
            DecimalPintFieldSaveModel.objects.all(),
            "weight",
            buckets=5,
            min_value=Quantity(Decimal("0.5"), ureg.kilogram),
            max_value=Quantity(Decimal("5.5"), ureg.kilogram),
        )
        first = buckets[0]
        assert first["bucket"] == 1
        assert first["lower"] == Quantity(Decimal("0.5"), ureg.kilogram)
        assert first["upper"] == Quantity(Decimal("1.5"), ureg.kilogram)

    def test_invalid_bucket_count_raises(self):
        """A bucket count below 1 is rejected."""
        with pytest.raises(ValidationError):
            pint_histogram(
                DecimalPintFieldSaveModel.objects.all(),
                "weight",
                buckets=0,
                min_value=Quantity(Decimal("0"), ureg.kilogram),
                max_value=Quantity(Decimal("5"), ureg.kilogram),
            )

    def test_out_of_range_values_are_excluded(self, weights_1_to_5):
        """Values below min or at/above max fall outside the returned buckets."""
        # Bounds [2, 4] kg, 2 buckets: only the 2 kg and 3 kg rows are in range;
        # 1 kg underflows and 4 kg / 5 kg overflow.
        buckets = pint_histogram(
            DecimalPintFieldSaveModel.objects.all(),
            "weight",
            buckets=2,
            min_value=Quantity(Decimal("2"), ureg.kilogram),
            max_value=Quantity(Decimal("4"), ureg.kilogram),
        )
        assert [b["count"] for b in buckets] == [1, 1]
        assert sum(b["count"] for b in buckets) == 2

    def test_accepts_float_bounds(self, weights_1_to_5):
        """Float bounds must not be rounded to int (regression guard).

        ``Quantity(0.5, kg)`` / ``Quantity(5.5, kg)`` must keep their fractional
        value, so each of 1..5 kg lands in its own bucket.
        """
        buckets = pint_histogram(
            DecimalPintFieldSaveModel.objects.all(),
            "weight",
            buckets=5,
            min_value=Quantity(0.5, ureg.kilogram),
            max_value=Quantity(5.5, ureg.kilogram),
        )
        assert [b["count"] for b in buckets] == [1, 1, 1, 1, 1]
        assert buckets[0]["lower"] == Quantity(Decimal("0.5"), ureg.kilogram)


def test_analytics_aggregates_exported_from_package_root():
    """New analytics aggregates are importable from the package root."""
    import django_pint_field

    assert hasattr(django_pint_field, "PintPercentile")
    assert hasattr(django_pint_field, "PintMedian")
    assert hasattr(django_pint_field, "pint_histogram")
