"""Tests for the helper functions in django_pint_field.helper."""

from decimal import Decimal

import pytest
from pint import DimensionalityError

import django_pint_field.helper as helper
import django_pint_field.models as models
from django_pint_field.units import ureg


# Fixtures that could go in conftest.py
@pytest.fixture
def unit_registry():
    """Return a Pint unit registry."""
    return ureg


@pytest.fixture
def integer_pint_field():
    """Return an IntegerPintField instance."""
    return models.IntegerPintField(default_unit="meter")


class TestMatchingUnitDimensions:
    """Test the check_matching_unit_dimension helper function."""

    def test_valid_choices(self, unit_registry):
        """Test that valid choices pass."""
        helper.check_matching_unit_dimension(unit_registry, "meter", ["mile", "foot", "cm"])

    def test_invalid_choices(self, unit_registry):
        """Test that invalid choices raise an error."""
        with pytest.raises(DimensionalityError):
            helper.check_matching_unit_dimension(unit_registry, "meter", ["mile", "foot", "cm", "kg"])


class TestEdgeCases:
    """Test edge cases for the pint field."""

    def test_fix_unit_registry_raises_error(self, integer_pint_field):
        """Test that the fix_unit_registry method raises ValueError for invalid input."""
        with pytest.raises(ValueError):
            integer_pint_field.fix_unit_registry(1)

    def test_get_prep_value_raises_error(self, integer_pint_field):
        """Test that the get_prep_value method raises ValueError for invalid input."""
        with pytest.raises(ValueError):
            integer_pint_field.get_prep_value("foobar")


class TestHelperFunctions:
    """Test the various helper functions."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("123", True),
            ("123.45", True),
            ("abc", False),
            (None, False),
        ],
    )
    def test_is_decimal_or_int(self, value, expected):
        """Test is_decimal_or_int with various inputs."""
        assert helper.is_decimal_or_int(value) == expected

    def test_get_base_units(self, unit_registry):
        """Test get_base_units returns correct base units."""
        base_units = helper.get_base_units(unit_registry, "kilometer")
        assert str(base_units) == "meter"

    @pytest.mark.parametrize(
        "max_digits,decimal_places,expected",
        [
            (1, 0, "1"),
            (2, 1, "1.1"),
            (3, 2, "1.11"),
        ],
    )
    def test_get_quantizing_string(self, max_digits, decimal_places, expected):
        """Test get_quantizing_string generates correct strings."""
        result = helper.get_quantizing_string(max_digits, decimal_places)
        assert result == expected


class TestBaseUnitMagnitude:
    """Test the get_base_unit_magnitude function."""

    def test_integer_input(self, unit_registry):
        """Test with integer magnitude."""
        value = unit_registry.Quantity(5, "kilometers")
        result = helper.get_base_unit_magnitude(value)
        assert result == Decimal("5000")
        assert isinstance(result, Decimal)

    def test_decimal_input(self, unit_registry):
        """Test with decimal magnitude."""
        value = unit_registry.Quantity(Decimal("2.5"), "kilometers")
        result = helper.get_base_unit_magnitude(value)
        assert result == Decimal("2500")
        assert isinstance(result, Decimal)

    def test_float_input(self, unit_registry):
        """Test with float magnitude (should be rounded)."""
        value = unit_registry.Quantity(2.7, "kilometers")
        result = helper.get_base_unit_magnitude(value)
        assert result == Decimal("3000")  # 2.7 rounds to 3, then converts to meters
        assert isinstance(result, Decimal)

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            (1.4, "1000"),  # rounds down to 1
            (1.6, "2000"),  # rounds up to 2
            (2.5, "3000"),  # rounds up to 3
            (3.49, "3000"),  # rounds down to 3
        ],
    )
    def test_float_rounding(self, unit_registry, input_value, expected):
        """Test various float rounding scenarios."""
        value = unit_registry.Quantity(input_value, "kilometers")
        result = helper.get_base_unit_magnitude(value)
        assert result == Decimal(expected)

    def test_different_unit_types(self, unit_registry):
        """Test conversion between different unit types."""
        cases = [
            (unit_registry.Quantity(1, "mile"), Decimal("1609.344")),  # 1 mile in meters
            (unit_registry.Quantity(100, "cm"), Decimal("1")),  # 100 cm in meters
            (unit_registry.Quantity(1, "foot"), Decimal("0.3048")),  # 1 foot in meters
        ]

        for input_value, expected in cases:
            result = helper.get_base_unit_magnitude(input_value)
            assert result == expected

    def test_preserves_precision(self, unit_registry):
        """Test that decimal precision is preserved."""
        value = unit_registry.Quantity(Decimal("1.23456"), "meters")
        result = helper.get_base_unit_magnitude(value)
        assert result == Decimal("1.23456")


class TestQuantizingString:
    """Additional tests for get_quantizing_string."""

    def test_zero_decimal_places(self):
        """Test when decimal_places is 0."""
        assert helper.get_quantizing_string(max_digits=3, decimal_places=0) == "111"

    def test_all_decimal_places(self):
        """Test when all digits are decimal places."""
        assert helper.get_quantizing_string(max_digits=3, decimal_places=3) == "0.111"

    def test_large_numbers(self):
        """Test with larger numbers of digits."""
        assert helper.get_quantizing_string(max_digits=10, decimal_places=5) == "11111.11111"
