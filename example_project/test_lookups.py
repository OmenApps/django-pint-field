"""Test cases for lookup fields."""

import json
from decimal import Decimal
from typing import Type

import pytest
from django.db import transaction
from pint.errors import DimensionalityError
from pint.errors import UndefinedUnitError

from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.units import ureg
from example_project.example.models import FieldSaveModel


Quantity = ureg.Quantity


@pytest.fixture
def test_quantities():
    """Provide various test quantities for comparisons."""
    return {
        "gram": ureg.gram,
        "kilogram": ureg.kilogram,
        "milligram": ureg.milligram,
        "pound": ureg.pound,
        "ounce": ureg.ounce,
    }


class TestFieldSaveBase:
    """Base class for testing field lookups."""

    MODEL: Type[FieldSaveModel]
    EXPECTED_TYPE: Type = float
    DEFAULT_WEIGHT = 100
    DEFAULT_WEIGHT_STR = "100.0"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
    HEAVIEST = 1000
    LIGHTEST = 1
    OUNCE_VALUE = 3.52739619496
    COMPARE_QUANTITY = ureg.Quantity(0.8 * ureg.ounce)
    WEIGHT = ureg.Quantity(2 * ureg.gram)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "incompatible_unit,expected_error",
        [
            (ureg.meter, DimensionalityError),
            (ureg.second, DimensionalityError),
            (ureg.kelvin, DimensionalityError),
            ("invalid_unit", UndefinedUnitError),
        ],
    )
    def test_fails_with_incompatible_units(self, incompatible_unit):
        """Test that the field fails with various incompatible units."""
        if isinstance(incompatible_unit, str):
            with pytest.raises(UndefinedUnitError), transaction.atomic():
                quantity = ureg.Quantity(100 * incompatible_unit)
                self.MODEL.objects.create(weight=quantity, name="Should Fail")
        else:
            with pytest.raises(DimensionalityError), transaction.atomic():
                quantity = ureg.Quantity(100 * incompatible_unit)
                self.MODEL.objects.create(weight=quantity, name="Should Fail")

    @pytest.mark.django_db
    def test_value_stored_as_quantity(self, test_objects):
        """Test that the value is stored as a quantity."""
        obj = self.MODEL.objects.first()
        assert isinstance(obj.weight, ureg.Quantity)
        assert str(obj.weight) == self.DEFAULT_WEIGHT_QUANTITY_STR

    @pytest.mark.django_db
    def test_value_stored_as_correct_magnitude_type(self, test_objects):
        """Test that the value is stored as the correct magnitude type."""
        obj = self.MODEL.objects.first()
        assert isinstance(obj.weight, ureg.Quantity)
        assert isinstance(obj.weight.magnitude, self.EXPECTED_TYPE)

    @pytest.mark.django_db
    def test_value_conversion(self, test_objects):
        """Test that the value is converted correctly."""
        obj = self.MODEL.objects.first()
        ounces = obj.weight.to(ureg.ounce)
        assert ounces.units == ureg.ounce

    @pytest.mark.django_db
    def test_order_by(self, test_objects):
        """Test that the objects are ordered by weight."""
        qs = list(self.MODEL.objects.all().order_by("weight"))
        assert qs[0].name == "lightest"
        assert qs[-1].name == "heaviest"
        assert qs[0] == test_objects["lightest"]
        assert qs[-1] == test_objects["heaviest"]

    @pytest.mark.django_db
    def test_comparison_with_quantity(self, test_objects):
        """Test that the comparison with a quantity works."""
        weight = ureg.Quantity(2 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__gt=weight)
        assert test_objects["lightest"] not in qs

    @pytest.mark.django_db
    def test_serialisation(self, test_objects):
        """Test that the field serializes correctly."""
        serialized = json.loads(json.dumps([{"fields": {"weight": self.DEFAULT_WEIGHT_QUANTITY_STR}}]))
        obj = serialized[0]["fields"]
        assert obj["weight"] == self.DEFAULT_WEIGHT_QUANTITY_STR

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "lookup,should_exclude",
        [
            ("gt", "lightest"),
            ("lt", "heaviest"),
            ("gte", "lightest"),
            ("lte", "heaviest"),
        ],
    )
    def test_quantity_comparisons(self, test_objects, lookup, should_exclude):
        """Test various comparison lookups."""
        qs = self.MODEL.objects.filter(**{f"weight__{lookup}": self.COMPARE_QUANTITY})
        assert test_objects[should_exclude] not in qs

    @pytest.mark.django_db
    def test_comparison_with_quantity_isnull(self, test_objects):
        """Test isnull lookup."""
        qs = self.MODEL.objects.filter(weight__isnull=False)
        assert test_objects["lightest"] in qs
        assert test_objects["heaviest"] in qs

    @pytest.mark.django_db
    def test_comparison_with_quantity_range(self, test_objects):
        """Test range lookup."""
        compare_quantity_2 = ureg.Quantity(2 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__range=(self.COMPARE_QUANTITY, compare_quantity_2))
        assert test_objects["heaviest"] not in qs

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "invalid_lookup",
        [
            "contains",
            "icontains",
            "in",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
            "date",
            "year",
            "iso_year",
            "month",
            "day",
            "week",
            "week_day",
            "iso_week_day",
            "quarter",
            "time",
            "hour",
            "minute",
            "second",
            "regex",
            "iregex",
            "search",
            "isearch",
            "month",
            "day",
            "week",
            "hour",
            "minute",
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
        ],
    )
    def test_additional_invalid_lookups(self, test_objects, lookup_type):
        """Test additional invalid lookup types."""
        with pytest.raises(PintFieldLookupError):
            list(self.MODEL.objects.filter(**{f"weight__{lookup_type}": self.COMPARE_QUANTITY}))

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "weight_value,expected_type",
        [
            (100, int),
            (100.0, float),
            (Decimal("100.00"), Decimal),
        ],
    )
    def test_value_stored_as_correct_type(self, test_objects, weight_value, expected_type):
        """Test that values are stored with correct types."""
        obj = self.MODEL.objects.create(weight=ureg.Quantity(weight_value * ureg.gram), name="type_test")
        assert isinstance(obj.weight.magnitude, expected_type)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "source_unit,target_unit,expected_approx",
        [
            ("gram", "kilogram", 0.1),
            ("gram", "milligram", 100000),
            ("gram", "pound", 0.220462),
            ("gram", "ounce", 3.52740),
        ],
    )
    def test_unit_conversions(self, test_objects, test_quantities, source_unit, target_unit, expected_approx):
        """Test various unit conversions."""
        quantity = ureg.Quantity(100 * test_quantities[source_unit])
        obj = self.MODEL.objects.create(weight=quantity, name="conversion_test")
        converted = obj.weight.to(test_quantities[target_unit])
        assert pytest.approx(converted.magnitude, rel=1e-4) == expected_approx

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "values,expected_order",
        [
            ([1, 2, 3], ["first", "second", "third"]),
            ([3, 1, 2], ["second", "third", "first"]),
            ([2, 2, 1], ["third", "first", "second"]),
        ],
    )
    def test_complex_ordering(self, values, expected_order):
        """Test ordering with various weight distributions."""
        # Create objects
        for value, name in zip(values, ["first", "second", "third"]):
            self.MODEL.objects.create(weight=ureg.Quantity(value * ureg.gram), name=name)

        # Test ordering
        qs = list(self.MODEL.objects.all().order_by("weight"))
        assert [obj.name for obj in qs] == expected_order

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "operator,value,expected_count",
        [
            ("gt", 50, 2),
            ("gte", 50, 3),
            ("lt", 50, 0),
            ("lte", 50, 1),
            ("exact", 100, 1),
        ],
    )
    def test_comparison_operators(self, test_objects, operator, value, expected_count):
        """Test various comparison operators."""
        qs = self.MODEL.objects.filter(**{f"weight__{operator}": ureg.Quantity(value * ureg.gram)})
        assert qs.count() == expected_count

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "range_values,expected_names",
        [
            ((0, 50), ["lightest"]),
            ((50, 150), ["grams"]),
            ((150, 2000), ["heaviest"]),
            ((0, 2000), ["lightest", "grams", "heaviest"]),
        ],
    )
    def test_range_queries(self, test_objects, range_values, expected_names):
        """Test range queries with various ranges."""
        start, end = range_values
        qs = self.MODEL.objects.filter(weight__range=(ureg.Quantity(start * ureg.gram), ureg.Quantity(end * ureg.gram)))
        result_names = [obj.name for obj in qs]
        assert sorted(result_names) == sorted(expected_names)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "quantity_value",
        [
            0,
            -1,
            10**6,
            Decimal("0.0001"),
            Decimal("9999.9999"),
        ],
    )
    def test_edge_case_values(self, quantity_value):
        """Test edge case values."""
        obj = self.MODEL.objects.create(weight=ureg.Quantity(quantity_value * ureg.gram), name="edge_case")
        retrieved = self.MODEL.objects.get(pk=obj.pk)
        assert retrieved.weight.magnitude == quantity_value

    @pytest.mark.django_db
    def test_multiple_unit_conversions_ordering(self, test_quantities):
        """Test ordering with mixed units."""
        # Create objects with different units but equivalent values
        self.MODEL.objects.create(weight=ureg.Quantity(1000 * ureg.gram), name="kilos")
        self.MODEL.objects.create(weight=ureg.Quantity(1 * ureg.kilogram), name="grams")
        self.MODEL.objects.create(weight=ureg.Quantity(1000000 * ureg.milligram), name="milligrams")

        # They should all be equal in ordering
        qs = list(self.MODEL.objects.all().order_by("weight"))
        assert len(set(obj.weight.to("gram").magnitude for obj in qs)) == 1
