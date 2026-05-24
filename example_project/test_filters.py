"""Tests for django-filter and admin integration."""

from decimal import Decimal

import django_filters
import pytest
from django.contrib.admin import site as admin_site
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from django_pint_field.admin import PintComparatorRangeListFilter
from django_pint_field.filters import PintFieldFilter
from django_pint_field.filters import PintFieldRangeFilter
from django_pint_field.filters import parse_quantity_string
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.fixture
def three_weights():
    """Create rows of 1 g, 1000 g, 2500 g."""
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1"), ureg.gram), name="light")
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1000"), ureg.gram), name="mid")
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2500"), ureg.gram), name="heavy")


class TestParseQuantityString:
    """Tests for the filter input parser."""

    def test_parses_magnitude_and_unit(self):
        """A '2 kilogram' string becomes a Quantity."""
        assert parse_quantity_string("2 kilogram") == Quantity(Decimal("2"), ureg.kilogram)

    def test_blank_returns_none(self):
        """Blank input yields None (no filtering)."""
        assert parse_quantity_string("") is None
        assert parse_quantity_string(None) is None

    def test_invalid_unit_raises(self):
        """An undefined unit raises ValueError."""
        with pytest.raises(ValueError):
            parse_quantity_string("2 notaunit")

    def test_missing_unit_raises(self):
        """A bare number with no unit raises ValueError."""
        with pytest.raises(ValueError):
            parse_quantity_string("2")


class WeightFilterSet(django_filters.FilterSet):
    """A FilterSet exercising PintFieldFilter."""

    weight = PintFieldFilter(field_name="weight", lookup_expr="gte")

    class Meta:
        model = DecimalPintFieldSaveModel
        fields = ["weight"]


@pytest.mark.django_db
class TestPintFieldFilter:
    """Tests for the single-comparison filter."""

    def test_gte_filter_across_units(self, three_weights):
        """Filtering weight >= '1 kilogram' returns the 1000 g and 2500 g rows."""
        fs = WeightFilterSet({"weight": "1 kilogram"}, queryset=DecimalPintFieldSaveModel.objects.all())
        assert fs.is_valid(), fs.form.errors  # a compatible cross-unit input must validate
        names = set(fs.qs.values_list("name", flat=True))
        assert names == {"mid", "heavy"}

    def test_blank_filter_returns_all(self, three_weights):
        """Blank input does not filter."""
        fs = WeightFilterSet({"weight": ""}, queryset=DecimalPintFieldSaveModel.objects.all())
        assert fs.qs.count() == 3

    def test_invalid_input_is_a_form_error(self, three_weights):
        """Invalid input makes the FilterSet invalid rather than crashing."""
        fs = WeightFilterSet({"weight": "2 notaunit"}, queryset=DecimalPintFieldSaveModel.objects.all())
        assert not fs.is_valid()

    def test_incompatible_dimension_is_a_form_error(self, three_weights):
        """A dimensionally-incompatible unit is a form error, not a query-time crash."""
        fs = WeightFilterSet({"weight": "5 meter"}, queryset=DecimalPintFieldSaveModel.objects.all())
        assert not fs.is_valid()
        assert "weight" in fs.form.errors


class WeightRangeFilterSet(django_filters.FilterSet):
    """A FilterSet exercising PintFieldRangeFilter."""

    weight = PintFieldRangeFilter(field_name="weight")

    class Meta:
        model = DecimalPintFieldSaveModel
        fields = ["weight"]


@pytest.mark.django_db
class TestPintFieldRangeFilter:
    """Tests for the two-sided range filter."""

    def test_range_filters_between_bounds(self, three_weights):
        """A range of 0.5 kg .. 2 kg returns only the 1000 g row."""
        fs = WeightRangeFilterSet(
            {"weight_min": "0.5 kilogram", "weight_max": "2 kilogram"},
            queryset=DecimalPintFieldSaveModel.objects.all(),
        )
        names = set(fs.qs.values_list("name", flat=True))
        assert names == {"mid"}

    def test_only_min_bound(self, three_weights):
        """Supplying only the min bound filters as >= ."""
        fs = WeightRangeFilterSet(
            {"weight_min": "1 kilogram"},
            queryset=DecimalPintFieldSaveModel.objects.all(),
        )
        names = set(fs.qs.values_list("name", flat=True))
        assert names == {"mid", "heavy"}

    def test_only_max_bound(self, three_weights):
        """Supplying only the max bound filters as <= ."""
        fs = WeightRangeFilterSet(
            {"weight_max": "1 kilogram"},
            queryset=DecimalPintFieldSaveModel.objects.all(),
        )
        names = set(fs.qs.values_list("name", flat=True))
        assert names == {"light", "mid"}

    def test_incompatible_dimension_is_a_form_error(self, three_weights):
        """A dimensionally-incompatible bound is a form error, not a query-time crash."""
        fs = WeightRangeFilterSet(
            {"weight_min": "5 meter"},
            queryset=DecimalPintFieldSaveModel.objects.all(),
        )
        assert not fs.is_valid()
        assert "weight" in fs.form.errors


class WeightBucketFilter(PintComparatorRangeListFilter):
    """Admin filter bucketing weight into named ranges."""

    parameter_name = "weight_bucket"
    title = "weight"
    field_name = "weight"
    ranges = [
        ("light", None, Quantity(Decimal("0.5"), ureg.kilogram)),
        ("heavy", Quantity(Decimal("0.5"), ureg.kilogram), None),
    ]


@pytest.mark.django_db
class TestPintComparatorRangeListFilter:
    """Tests for the admin range list filter."""

    def _request(self, params):
        rf = RequestFactory()
        request = rf.get("/admin/", params)
        request.user = get_user_model()(is_superuser=True, is_staff=True)
        return request

    def test_lookups_render_each_named_range(self, three_weights):
        """The filter offers one choice per configured range."""
        f = WeightBucketFilter(self._request({}), {}, DecimalPintFieldSaveModel, admin_site)
        labels = [label for _value, label in f.lookups(self._request({}), None)]
        assert labels == ["light", "heavy"]

    def test_selecting_heavy_filters_queryset(self, three_weights):
        """Selecting 'heavy' returns rows >= 0.5 kilogram."""
        request = self._request({"weight_bucket": "heavy"})
        # Django's admin passes filter params as lists (request.GET semantics).
        f = WeightBucketFilter(request, {"weight_bucket": ["heavy"]}, DecimalPintFieldSaveModel, admin_site)
        qs = f.queryset(request, DecimalPintFieldSaveModel.objects.all())
        names = set(qs.values_list("name", flat=True))
        assert names == {"mid", "heavy"}

    def test_selecting_light_filters_queryset(self, three_weights):
        """Selecting 'light' (upper-bound-only range) returns rows < 0.5 kilogram."""
        request = self._request({"weight_bucket": "light"})
        f = WeightBucketFilter(request, {"weight_bucket": ["light"]}, DecimalPintFieldSaveModel, admin_site)
        qs = f.queryset(request, DecimalPintFieldSaveModel.objects.all())
        names = set(qs.values_list("name", flat=True))
        assert names == {"light"}

    def test_no_selection_returns_all(self, three_weights):
        """With no range selected, the queryset is unfiltered."""
        request = self._request({})
        f = WeightBucketFilter(request, {}, DecimalPintFieldSaveModel, admin_site)
        qs = f.queryset(request, DecimalPintFieldSaveModel.objects.all())
        assert qs.count() == 3
