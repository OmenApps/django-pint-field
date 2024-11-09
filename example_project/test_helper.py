"""Test cases for helper functions."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from django_pint_field.helpers import check_matching_unit_dimension
from django_pint_field.helpers import get_base_unit_magnitude
from django_pint_field.helpers import get_base_units
from django_pint_field.helpers import get_quantizing_string
from django_pint_field.helpers import is_decimal_or_int
from django_pint_field.units import ureg


class TestCheckMatchingUnitDimension:
    """Test the check_matching_unit_dimension function."""

    def test_valid_matching_units(self):
        """Test units with matching dimensions."""
        valid_units = ["gram", "kilogram", "pound"]
        check_matching_unit_dimension(ureg, "gram", valid_units)  # Should not raise

    def test_invalid_unit_dimensions(self):
        """Test units with non-matching dimensions."""
        invalid_units = ["meter", "second", "kelvin"]
        with pytest.raises(ValidationError):
            check_matching_unit_dimension(ureg, "gram", invalid_units)

    def test_mixed_valid_invalid_units(self):
        """Test a mix of valid and invalid units."""
        mixed_units = ["gram", "meter", "kilogram"]
        with pytest.raises(ValidationError):
            check_matching_unit_dimension(ureg, "gram", mixed_units)

    def test_empty_units_list(self):
        """Test with an empty list of units to check."""
        check_matching_unit_dimension(ureg, "gram", [])  # Should not raise

    def test_invalid_default_unit(self):
        """Test with an invalid default unit."""
        with pytest.raises(ValidationError, match="Invalid default unit"):
            check_matching_unit_dimension(ureg, "invalid_unit", ["gram"])

    def test_invalid_check_unit(self):
        """Test with an invalid unit in the check list."""
        with pytest.raises(ValidationError, match="Invalid unit"):
            check_matching_unit_dimension(ureg, "gram", ["invalid_unit"])


class TestIsDecimalOrInt:
    """Test the is_decimal_or_int function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (42, True),
            (-17, True),
            (3.14, True),
            (Decimal("10.5"), True),
            ("123", True),
            ("-456.789", True),
            (Decimal("0"), True),
            ("invalid", False),
            (None, False),
            ("", False),
            ("abc123", False),
            ([], False),
            ({}, False),
            (True, False),
        ],
    )
    def test_various_inputs(self, value, expected):
        """Test various input types."""
        assert is_decimal_or_int(value) == expected


class TestGetBaseUnits:
    """Test the get_base_units function."""

    @pytest.mark.parametrize(
        "unit,expected_base",
        [
            ("gram", "kilogram"),
            ("kilogram", "kilogram"),
            ("pound", "kilogram"),
            ("meter", "meter"),
            ("inch", "meter"),
            ("second", "second"),
        ],
    )
    def test_base_unit_conversion(self, unit, expected_base):
        """Test conversion to base units."""
        base_unit = get_base_units(ureg, unit)
        assert str(base_unit) == expected_base

    def test_invalid_unit(self):
        """Test with an invalid unit."""
        with pytest.raises(AttributeError):
            get_base_units(ureg, "invalid_unit")


class TestGetBaseUnitMagnitude:
    """Test the get_base_unit_magnitude function."""

    def test_gram_to_kilogram(self):
        """Test converting gram quantities to kilogram base units."""
        quantity = ureg.Quantity(1000, "gram")
        assert get_base_unit_magnitude(quantity) == Decimal("1")

    def test_integer_input(self):
        """Test with integer input magnitude."""
        quantity = ureg.Quantity(5, "gram")
        assert get_base_unit_magnitude(quantity) == Decimal("0.005")

    def test_decimal_input(self):
        """Test with Decimal input magnitude."""
        quantity = ureg.Quantity(Decimal("5.0"), "gram")
        assert get_base_unit_magnitude(quantity) == Decimal("0.005")

    def test_float_input_rounding(self):
        """Test that float inputs are properly rounded."""
        quantity = ureg.Quantity(5.6789, "gram")
        result = get_base_unit_magnitude(quantity)
        assert result == Decimal("0.006")  # Rounds to 6 grams


class TestGetQuantizingString:
    """Test the get_quantizing_string function."""

    @pytest.mark.parametrize(
        "max_digits,decimal_places,expected",
        [
            (1, 0, "1"),
            (2, 1, "1.1"),
            (3, 2, "1.11"),
            (5, 3, "11.111"),
            (4, 0, "1111"),
            (3, 0, "111"),
            (2, 2, "0.11"),
            (3, 3, "0.111"),
        ],
    )
    def test_valid_inputs(self, max_digits, decimal_places, expected):
        """Test various valid input combinations."""
        assert get_quantizing_string(max_digits, decimal_places) == expected

    @pytest.mark.parametrize(
        "max_digits,decimal_places,error_msg",
        [
            (0, 0, "max_digits must be greater than 0"),
            (-1, 0, "max_digits must be greater than 0"),
            (1, -1, "decimal_places must be non-negative"),
            (1, 2, "decimal_places cannot be greater than max_digits"),
        ],
    )
    def test_invalid_inputs(self, max_digits, decimal_places, error_msg):
        """Test various invalid input combinations."""
        with pytest.raises(ValidationError, match=error_msg):
            get_quantizing_string(max_digits, decimal_places)

    def test_edge_cases(self):
        """Test edge cases."""
        assert get_quantizing_string(1, 0) == "1"  # Minimum valid case
        assert get_quantizing_string(10, 9) == "1.111111111"  # Large number of decimal places
