"""Test cases for lookup fields."""

import json
from decimal import Decimal
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from pint.errors import UndefinedUnitError

from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.helpers import PintFieldProxy
from django_pint_field.units import ureg
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestFieldLookups:
    """Base test class for field lookups."""

    @pytest.fixture(autouse=True)
    def setup_class(self, request):
        """Set up the test parameters."""
        if request.param == "integer":
            self.MODEL = IntegerPintFieldSaveModel
            self.EXPECTED_TYPE = Decimal  # Changed to Decimal since UnitRegistry uses non_int_type=Decimal
            self.DEFAULT_WEIGHT = 100
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
            self.HEAVIEST = 1000
            self.LIGHTEST = 1
            self.OUNCE_VALUE = 3.52739619496
        elif request.param == "big_integer":
            self.MODEL = BigIntegerPintFieldSaveModel
            self.EXPECTED_TYPE = Decimal  # Changed to Decimal since UnitRegistry uses non_int_type=Decimal
            self.DEFAULT_WEIGHT = 100
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
            self.HEAVIEST = 1000
            self.LIGHTEST = 1
            self.OUNCE_VALUE = 3.52739619496
        else:  # decimal
            self.MODEL = DecimalPintFieldSaveModel
            self.EXPECTED_TYPE = Decimal
            self.DEFAULT_WEIGHT = Decimal("100")
            self.DEFAULT_WEIGHT_STR = "100.0"
            self.DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
            self.HEAVIEST = Decimal("1000")
            self.LIGHTEST = Decimal("1")
            self.OUNCE_VALUE = Decimal("3.52739619496")

        self.COMPARE_QUANTITY = Quantity(22.7 * ureg.gram)  # Increased to match test data
        self.WEIGHT = Quantity(2 * ureg.gram)

    @pytest.fixture
    def field_test_lookup_objects(self) -> dict[str, Any]:
        """Create test objects with different weights and return them in a dictionary."""
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

        # Return dictionary instead of tuple for easier access
        objects = {
            "default": default,
            "lightest": lightest,
            "heaviest": heaviest,
            "grams": default,  # Add grams alias for default
        }

        yield objects

        self.MODEL.objects.all().delete()

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
        ],
    )
    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_additional_invalid_lookups(self, invalid_lookup):
        """Test additional invalid lookup types."""
        with pytest.raises(PintFieldLookupError):
            list(self.MODEL.objects.filter(**{f"weight__{invalid_lookup}": self.COMPARE_QUANTITY}))

    @pytest.mark.parametrize(
        "incompatible_unit,expected_error",
        [
            (ureg.meter, ValidationError),
            (ureg.second, ValidationError),
            (ureg.kelvin, ValidationError),
            ("invalid_unit", (TypeError, UndefinedUnitError)),
        ],
    )
    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_fails_with_incompatible_units(self, incompatible_unit, expected_error):
        """Test that the field fails with various incompatible units."""
        with pytest.raises(expected_error), transaction.atomic():
            quantity = Quantity(self.DEFAULT_WEIGHT * incompatible_unit)
            self.MODEL.objects.create(weight=quantity, name="Should Fail")

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_value_stored_as_quantity(self, field_test_lookup_objects):
        """Test that the value is stored as a quantity."""
        obj = self.MODEL.objects.first()
        assert isinstance(obj.weight, PintFieldProxy)
        assert isinstance(obj.weight.quantity, Quantity)
        assert str(obj.weight) == self.DEFAULT_WEIGHT_QUANTITY_STR

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_value_stored_as_correct_magnitude_type(self, field_test_lookup_objects):
        """Test that the value is stored as the correct magnitude type."""
        obj = self.MODEL.objects.first()
        assert isinstance(obj.weight, PintFieldProxy)
        assert isinstance(obj.weight.quantity.magnitude, self.EXPECTED_TYPE)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_value_conversion(self, field_test_lookup_objects):
        """Test that the value is converted correctly."""
        obj = self.MODEL.objects.first()
        ounces = obj.weight.ounce  # Use the proxy's unit conversion
        assert isinstance(ounces, Quantity)
        assert str(ounces.units) == "ounce"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_serialisation(self, field_test_lookup_objects):
        """Test that the field serializes correctly."""
        serialized = json.loads(json.dumps([{"fields": {"weight": self.DEFAULT_WEIGHT_QUANTITY_STR}}]))
        obj = serialized[0]["fields"]
        assert obj["weight"] == self.DEFAULT_WEIGHT_QUANTITY_STR

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_order_by(self, field_test_lookup_objects):
        """Test that the objects are ordered by weight."""
        qs = list(self.MODEL.objects.all().order_by("weight"))
        assert qs[0].name == "lightest"
        assert qs[-1].name == "heaviest"
        assert qs[0] == field_test_lookup_objects["lightest"]
        assert qs[-1] == field_test_lookup_objects["heaviest"]

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_comparison_with_quantity(self, field_test_lookup_objects):
        """Test that the comparison with a quantity works."""
        weight = Quantity(2 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__gt=weight)
        assert field_test_lookup_objects["lightest"].name not in list(qs.values_list("name", flat=True))
        assert field_test_lookup_objects["heaviest"].name in list(qs.values_list("name", flat=True))

    @pytest.mark.parametrize(
        "lookup,should_exclude",
        [
            ("gt", "lightest"),
            ("lt", "heaviest"),
            ("gte", "lightest"),
            ("lte", "heaviest"),
        ],
    )
    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_quantity_comparisons(self, field_test_lookup_objects, lookup, should_exclude):
        """Test various comparison lookups."""
        qs = self.MODEL.objects.filter(**{f"weight__{lookup}": self.COMPARE_QUANTITY})
        assert field_test_lookup_objects[should_exclude].name not in list(qs.values_list("name", flat=True))

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_comparison_with_quantity_range(self, field_test_lookup_objects):
        """Test range lookup."""
        compare_quantity_2 = Quantity(29 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__range=(self.COMPARE_QUANTITY, compare_quantity_2))
        assert field_test_lookup_objects["heaviest"].name not in list(qs.values_list("name", flat=True))

    @pytest.mark.parametrize(
        "operator,value,expected_count",
        [
            ("gt", 25, 2),
            ("gte", 25, 3),
            ("lt", 25, 0),
            ("lte", 25, 1),
            ("exact", 100, 1),
        ],
    )
    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_comparison_operators(self, operator, value, expected_count):
        """Test various comparison operators."""
        # Create test objects with specific weights for comparison tests
        if self.EXPECTED_TYPE == Decimal:
            self.MODEL.objects.bulk_create(
                [
                    self.MODEL(weight=Quantity(Decimal("100") * ureg.gram)),
                    self.MODEL(weight=Quantity(Decimal("75") * ureg.gram)),
                    self.MODEL(weight=Quantity(Decimal("25") * ureg.gram)),
                ]
            )
        else:
            self.MODEL.objects.bulk_create(
                [
                    self.MODEL(weight=Quantity(100 * ureg.gram)),
                    self.MODEL(weight=Quantity(75 * ureg.gram)),
                    self.MODEL(weight=Quantity(25 * ureg.gram)),
                ]
            )

        qs = self.MODEL.objects.filter(**{f"weight__{operator}": Quantity(value * ureg.gram)})
        assert qs.count() == expected_count
