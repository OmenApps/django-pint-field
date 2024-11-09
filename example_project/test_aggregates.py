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
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestFieldAggregates:
    """Base test class for field aggregates."""

    @pytest.fixture(autouse=True)
    def setup_class(self, request):
        """Set up the test parameters."""
        if request.param == "integer":
            self.MODEL = IntegerPintFieldSaveModel
            self.EXPECTED_TYPE = int
            self.DEFAULT_WEIGHT = 100
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
            self.HEAVIEST = 1000
            self.LIGHTEST = 1
            self.OUNCE_VALUE = 3.52739619496
        elif request.param == "big_integer":
            self.MODEL = BigIntegerPintFieldSaveModel
            self.EXPECTED_TYPE = int
            self.DEFAULT_WEIGHT = 100
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
            self.HEAVIEST = 1000
            self.LIGHTEST = 1
            self.OUNCE_VALUE = 3.52739619496
        else:  # decimal
            self.MODEL = DecimalPintFieldSaveModel
            self.EXPECTED_TYPE = Decimal
            self.DEFAULT_WEIGHT = Decimal("100")
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
            self.HEAVIEST = Decimal("1000")
            self.LIGHTEST = Decimal("1")
            self.OUNCE_VALUE = Decimal("3.52739619496")

        self.COMPARE_QUANTITY = Quantity(0.8 * ureg.ounce)
        self.WEIGHT = Quantity(2 * ureg.gram)

    @pytest.fixture
    def field_test_aggregate_objects(self):
        """Create test objects with different weights."""
        if self.EXPECTED_TYPE == Decimal:
            default = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.DEFAULT_WEIGHT)) * ureg.gram),
                name="grams",
            )
            lightest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.LIGHTEST)) * ureg.gram),
                name="lightest",
            )
            heaviest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.HEAVIEST)) * ureg.gram),
                name="heaviest",
            )
        else:
            default = self.MODEL.objects.create(
                weight=Quantity(self.DEFAULT_WEIGHT * ureg.gram),
                name="grams",
            )
            lightest = self.MODEL.objects.create(
                weight=Quantity(self.LIGHTEST * ureg.gram),
                name="lightest",
            )
            heaviest = self.MODEL.objects.create(
                weight=Quantity(self.HEAVIEST * ureg.gram),
                name="heaviest",
            )

        yield default, lightest, heaviest

        self.MODEL.objects.all().delete()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_comparison_with_invalid_lookup_second(self):
        """Test that comparison with invalid lookup second raises error."""
        with pytest.raises(PintFieldLookupError):
            self.MODEL.objects.filter(weight__second=self.COMPARE_QUANTITY).first()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_count(self, field_test_aggregate_objects):
        """Test the aggregate count."""
        comparison = 3
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintCount("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_avg_without_output_unit(self, field_test_aggregate_objects):
        """Test the aggregate average."""
        comparison = Quantity(Decimal("367.00000000000000000") * ureg.gram).to_base_units()
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintAvg("weight"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_avg(self, field_test_aggregate_objects):
        """Test the aggregate average."""
        comparison = Quantity(Decimal("367.00000000000000000") * ureg.gram).to_base_units()
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintAvg("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_max(self, field_test_aggregate_objects):
        """Test the aggregate max."""
        comparison = Quantity(Decimal("1000") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMax("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_min(self, field_test_aggregate_objects):
        """Test the aggregate min."""
        comparison = Quantity(Decimal("1.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMin("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_sum(self, field_test_aggregate_objects):
        """Test the aggregate sum."""
        comparison = Quantity(Decimal("1101.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintSum("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_std_dev(self, field_test_aggregate_objects):
        """Test the aggregate standard deviation."""
        comparison = Quantity(Decimal("449.41962573968662856") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintStdDev("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_aggregate_variance(self, field_test_aggregate_objects):
        """Test the aggregate variance."""
        comparison = Quantity(Decimal("201.978") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintVariance("weight", output_unit="gram"))["pint_agg"]
        assert comparison == pint_agg.to_base_units()
