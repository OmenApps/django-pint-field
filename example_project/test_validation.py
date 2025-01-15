"""Test cases for validation utilities in django-pint-field."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from django_pint_field.units import ureg
from django_pint_field.validation import QuantityConverter
from django_pint_field.validation import validate_decimal_precision
from django_pint_field.validation import validate_dimensionality
from django_pint_field.validation import validate_required_value
from django_pint_field.validation import validate_unit_choices
from django_pint_field.validation import validate_value_range


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestUnitChoicesValidation:

    @pytest.mark.parametrize(
        "unit_choices, default_unit, expected",
        [
            (
                ["kilogram", "gram", "pound"],
                "kilogram",
                [("kilogram", "kilogram"), ("gram", "gram"), ("pound", "pound")],
            ),
            (
                ("kilogram", "gram", "pound"),
                "kilogram",
                [("kilogram", "kilogram"), ("gram", "gram"), ("pound", "pound")],
            ),
            (
                [["kilogram", "kg"], ["gram", "g"], ["pound", "lb"]],
                "kilogram",
                [("kilogram", "kg"), ("gram", "g"), ("pound", "lb")],
            ),
            ([], "kilogram", []),
            (None, "kilogram", []),
        ],
    )
    def test_validate_unit_choices(self, unit_choices, default_unit, expected):
        """Test validation and normalization of unit choices."""
        result = validate_unit_choices(unit_choices, default_unit)
        assert result == expected

    @pytest.mark.parametrize(
        "unit_choices, default_unit, error_message",
        [
            (["invalid_unit"], "kilogram", "Invalid unit: invalid_unit"),
            ([["kilogram", "kg"], ["invalid_unit", "iu"]], "kilogram", "Invalid unit: iu"),
            ([["kilogram", "kg"], ["gram", "g"], ["invalid_unit", "iu"]], "kilogram", "Invalid unit: iu"),
        ],
    )
    def test_validate_unit_choices_invalid_units(self, unit_choices, default_unit, error_message):
        """Test validation of unit choices with invalid units."""
        with pytest.raises(ValidationError, match=error_message):
            validate_unit_choices(unit_choices, default_unit)


@pytest.mark.django_db
class TestQuantityConverter:
    """Tests of the QuantityConverter class."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (Quantity(100, "gram"), Quantity(100, "gram")),
            ({"magnitude": 100, "units": "gram"}, Quantity(100, "gram")),
            (["100", "gram"], Quantity(100, "gram")),
            ("100 gram", Quantity(100, "gram")),
            (None, None),
        ],
    )
    def test_quantity_converter_convert(self, value, expected):
        """Test conversion of various input types to Quantity objects."""
        converter = QuantityConverter(default_unit="gram", field_type="decimal")
        result = converter.convert(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value, error_message",
        [
            ({"magnitude": "invalid", "units": "gram"}, "Magnitude must be a number."),
            ("invalid gram", "Invalid quantity string"),
            ({"magnitude": 100}, "Dictionary must contain 'magnitude' and 'units' keys"),
        ],
    )
    def test_quantity_converter_convert_invalid(self, value, error_message):
        """Test conversion of invalid input types to Quantity objects."""
        converter = QuantityConverter(default_unit="gram", field_type="decimal")
        with pytest.raises(ValidationError, match=error_message):
            converter.convert(value)


@pytest.mark.django_db
class TestOtherValidation:
    """Other tests of validation.py."""

    @pytest.mark.parametrize(
        "value, default_unit, should_raise",
        [
            (Quantity(100, "gram"), "gram", False),
            (Quantity(100, "kilogram"), "gram", False),
            (Quantity(100, "meter"), "gram", True),
            (Quantity(100, "kilogram"), "meter", True),
        ],
    )
    def test_validate_dimensionality(self, value, default_unit, should_raise):
        """Test validation of dimensionality."""
        if should_raise:
            with pytest.raises(ValidationError, match="has incompatible dimensionality"):
                validate_dimensionality(value, default_unit)
        else:
            validate_dimensionality(value, default_unit)

    @pytest.mark.parametrize(
        "value, required, blank, should_raise",
        [
            (None, True, False, True),
            (None, True, True, True),
            (None, False, False, False),
            (None, False, True, False),
            ("", True, False, True),
            ("", True, True, False),
            ("", False, False, False),
            ("", False, True, False),
            (Quantity(100, "gram"), True, False, False),
            (Quantity(100, "gram"), True, True, False),
        ],
    )
    def test_validate_required_value(self, value, required, blank, should_raise):
        """Test validation of required values."""
        if should_raise:
            with pytest.raises(ValidationError):
                validate_required_value(value, required, blank)
        else:
            validate_required_value(value, required, blank)

    @pytest.mark.parametrize(
        "value, allow_rounding, should_raise",
        [
            (Quantity(Decimal("100.12345"), "gram"), False, False),
            (Quantity(Decimal("100.12345678901234567890123456789"), "gram"), False, True),
            (Quantity(Decimal("100.12345678901234567890123456789"), "gram"), True, False),
            (Quantity(100, "gram"), False, False),
            (None, False, False),
        ],
    )
    def test_validate_decimal_precision(self, value, allow_rounding, should_raise):
        """Test validation of decimal precision."""
        if should_raise:
            with pytest.raises(ValidationError, match="Ensure that the value does not exceed the maximum precision"):
                validate_decimal_precision(value, allow_rounding)
        else:
            validate_decimal_precision(value, allow_rounding)

    @pytest.mark.parametrize(
        "value, min_value, max_value, should_raise",
        [
            (Quantity(100, "gram"), Quantity(50, "gram"), Quantity(150, "gram"), False),
            (Quantity(100, "gram"), Quantity(150, "gram"), Quantity(200, "gram"), True),
            (Quantity(100, "gram"), Quantity(50, "gram"), Quantity(75, "gram"), True),
            (Quantity(100, "gram"), None, Quantity(150, "gram"), False),
            (Quantity(100, "gram"), Quantity(50, "gram"), None, False),
            (Quantity(100, "gram"), None, None, False),
            (100, 50, 150, False),
            (100, 150, 200, True),
            (100, 50, 75, True),
            (100, None, 150, False),
            (100, 50, None, False),
            (100, None, None, False),
            (None, Quantity(50, "gram"), Quantity(150, "gram"), False),
        ],
    )
    def test_validate_value_range(self, value, min_value, max_value, should_raise):
        """Test validation of value ranges."""
        if should_raise:
            with pytest.raises(ValidationError):
                validate_value_range(value, min_value, max_value)
        else:
            validate_value_range(value, min_value, max_value)
