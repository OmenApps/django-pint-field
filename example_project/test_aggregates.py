"""Test cases for aggregate functions."""

from decimal import Decimal

import pytest

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintCount
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintMin
from django_pint_field.aggregates import PintStdDev
from django_pint_field.aggregates import PintSum
from django_pint_field.aggregates import PintVariance
from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestFieldAggregates:
    """Test class for field aggregates."""

    @pytest.fixture(autouse=True)
    def setup_class(self, request):
        """Set up the test parameters."""
        if request.param == "integer":
            self.MODEL = IntegerPintFieldSaveModel
            self.EXPECTED_TYPE = int
            self.DEFAULT_WEIGHT = 100
            self.HEAVIEST = 1000
            self.LIGHTEST = 1
        else:  # decimal
            self.MODEL = DecimalPintFieldSaveModel
            self.EXPECTED_TYPE = Decimal
            self.DEFAULT_WEIGHT = Decimal("100")
            self.HEAVIEST = Decimal("1000")
            self.LIGHTEST = Decimal("1")

        self.COMPARE_QUANTITY = Quantity(Decimal("0.8") * ureg.gram)
        self.WEIGHT = Quantity(2 * ureg.gram)

    @pytest.fixture
    def field_test_aggregate_objects(self):
        """Create test objects with different weights."""
        if self.EXPECTED_TYPE == Decimal:
            default = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.DEFAULT_WEIGHT)), ureg.gram),
                name="grams",
            )
            lightest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.LIGHTEST)), ureg.gram),
                name="lightest",
            )
            heaviest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.HEAVIEST)), ureg.gram),
                name="heaviest",
            )
        else:
            default = self.MODEL.objects.create(
                weight=Quantity(self.DEFAULT_WEIGHT, ureg.gram),
                name="grams",
            )
            lightest = self.MODEL.objects.create(
                weight=Quantity(self.LIGHTEST, ureg.gram),
                name="lightest",
            )
            heaviest = self.MODEL.objects.create(
                weight=Quantity(self.HEAVIEST, ureg.gram),
                name="heaviest",
            )

        yield default, lightest, heaviest

        self.MODEL.objects.all().delete()

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_comparison_with_invalid_lookup_second(self):
        """Test that comparison with invalid lookup second raises error."""
        with pytest.raises(PintFieldLookupError):
            self.MODEL.objects.filter(weight__second=self.COMPARE_QUANTITY).first()

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_count(self, field_test_aggregate_objects):
        """Test the aggregate count."""
        comparison = 3
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintCount("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_avg(self, field_test_aggregate_objects):
        """Test the aggregate average."""
        if self.EXPECTED_TYPE == Decimal:
            expected_avg = Decimal("0.367")
        else:
            expected_avg = Decimal("0.367")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintAvg("weight"))["pint_agg"]
        assert abs(expected_avg - pint_agg.quantity.magnitude) < Decimal("0.001")
        assert str(pint_agg.quantity.units) == "kilogram"

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_max(self, field_test_aggregate_objects):
        """Test the aggregate max."""
        if self.EXPECTED_TYPE == Decimal:
            expected_max = Decimal("1.0")
        else:
            expected_max = Decimal("1.0")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMax("weight"))["pint_agg"]
        assert abs(expected_max - pint_agg.quantity.magnitude) < Decimal("0.001")
        assert str(pint_agg.quantity.units) == "kilogram"

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_min(self, field_test_aggregate_objects):
        """Test the aggregate min."""
        if self.EXPECTED_TYPE == Decimal:
            expected_min = Decimal("0.001")
        else:
            expected_min = Decimal("0.001")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMin("weight"))["pint_agg"]
        assert abs(expected_min - pint_agg.quantity.magnitude) < Decimal("0.0001")
        assert str(pint_agg.quantity.units) == "kilogram"

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_sum(self, field_test_aggregate_objects):
        """Test the aggregate sum."""
        if self.EXPECTED_TYPE == Decimal:
            expected_sum = Decimal("1.101")
        else:
            expected_sum = Decimal("1.101")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintSum("weight"))["pint_agg"]
        assert abs(expected_sum - pint_agg.quantity.magnitude) < Decimal("0.001")
        assert str(pint_agg.quantity.units) == "kilogram"

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_std_dev(self, field_test_aggregate_objects):
        """Test the aggregate standard deviation."""
        if self.EXPECTED_TYPE == Decimal:
            expected_std = Decimal("0.449")
        else:
            expected_std = Decimal("0.449")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintStdDev("weight"))["pint_agg"]
        assert abs(expected_std - pint_agg.quantity.magnitude) < Decimal("0.001")
        assert str(pint_agg.quantity.units) == "kilogram"

    @pytest.mark.parametrize("setup_class", ["integer", "decimal"], indirect=True)
    def test_aggregate_variance(self, field_test_aggregate_objects):
        """Test the aggregate variance."""
        if self.EXPECTED_TYPE == Decimal:
            expected_var = Decimal("0.202")
        else:
            expected_var = Decimal("0.202")

        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintVariance("weight"))["pint_agg"]
        assert abs(expected_var - pint_agg.quantity.magnitude) < Decimal("0.001")
        assert str(pint_agg.quantity.units) == "kilogram"


@pytest.mark.django_db
def test_grouped_annotate_returns_proxy_per_group():
    """values().annotate() runs convert_value once per GROUP BY row.

    Pins the resolve_expression/convert_value contract: original_field must be
    set on the resolved copy so every grouped row produces a correct proxy.
    """
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("200"), ureg.gram), name="a")
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("50"), ureg.gram), name="b")

    rows = list(DecimalPintFieldSaveModel.objects.values("name").annotate(total=PintSum("weight")).order_by("name"))

    assert len(rows) == 2
    assert str(rows[0]["total"].quantity.units) == "kilogram"
    assert abs(rows[0]["total"].quantity.magnitude - Decimal("0.3")) < Decimal("0.001")  # a: 300 g
    assert str(rows[1]["total"].quantity.units) == "kilogram"
    assert abs(rows[1]["total"].quantity.magnitude - Decimal("0.05")) < Decimal("0.001")  # b: 50 g


@pytest.mark.django_db
def test_aggregate_instance_reused_across_queries():
    """Reusing one aggregate instance across queries does not leak cached state.

    Each resolve_expression() returns a fresh copy with its own base_unit, so the
    per-query cache cannot bleed across queries.
    """
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1000"), ureg.gram), name="x")
    agg = PintSum("weight")
    first = DecimalPintFieldSaveModel.objects.aggregate(t=agg)["t"]
    second = DecimalPintFieldSaveModel.objects.aggregate(t=agg)["t"]
    assert first.quantity == second.quantity == Quantity(Decimal("1"), ureg.kilogram)
    assert str(second.quantity.units) == "kilogram"
