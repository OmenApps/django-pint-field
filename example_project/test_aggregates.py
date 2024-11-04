"""Test cases for aggregate functions."""

from decimal import Decimal
from typing import Type

import pytest
from pint import Quantity

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintCount
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintMin
from django_pint_field.aggregates import PintStdDev
from django_pint_field.aggregates import PintSum
from django_pint_field.aggregates import PintVariance
from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.units import ureg
from example_project.example.models import FieldSaveModel


class TestFieldSaveBase:
    """Base class for testing the saving of a field."""

    MODEL: Type[FieldSaveModel]
    EXPECTED_TYPE: Type = float
    DEFAULT_WEIGHT = 100
    DEFAULT_WEIGHT_STR = "100.0"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
    HEAVIEST = 1000
    LIGHTEST = 1
    OUNCE_VALUE = 3.52739619496
    COMPARE_QUANTITY = Quantity(0.8 * ureg.ounce)  # 1 ounce = 28.34 grams
    WEIGHT = Quantity(2 * ureg.gram)

    @pytest.mark.django_db
    def test_comparison_with_invalid_lookup_second(self):
        """Test that comparison with invalid lookup second raises error."""
        with pytest.raises(PintFieldLookupError):
            self.MODEL.objects.filter(weight__second=self.COMPARE_QUANTITY).first()

    @pytest.mark.django_db
    def test_aggregate_avg(self, field_test_objects):
        """Test the aggregate average."""
        comparison = Quantity(Decimal("367.00000000000000000") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintAvg("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_count(self, field_test_objects):
        """Test the aggregate count."""
        comparison = 3
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintCount("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_max(self, field_test_objects):
        """Test the aggregate max."""
        comparison = Quantity(Decimal("1000") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMax("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_min(self, field_test_objects):
        """Test the aggregate min."""
        comparison = Quantity(Decimal("1.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMin("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_sum(self, field_test_objects):
        """Test the aggregate sum."""
        comparison = Quantity(Decimal("1101.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintSum("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_std_dev(self, field_test_objects):
        """Test the aggregate standard deviation."""
        comparison = Quantity(Decimal("449.41962573968662856") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintStdDev("weight"))["pint_agg"]
        assert comparison == pint_agg

    @pytest.mark.django_db
    def test_aggregate_variance(self, field_test_objects):
        """Test the aggregate variance."""
        comparison = Quantity(Decimal("201.978") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintVariance("weight"))["pint_agg"]
        assert comparison == pint_agg
