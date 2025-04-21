"""Test cases for helper functions."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from pint.errors import DimensionalityError

from django_pint_field.helpers import PintFieldConverter
from django_pint_field.helpers import PintFieldProxy
from django_pint_field.helpers import check_matching_unit_dimension
from django_pint_field.helpers import get_base_unit_magnitude
from django_pint_field.helpers import get_base_units
from django_pint_field.helpers import get_pint_unit
from django_pint_field.helpers import get_quantizing_string
from django_pint_field.helpers import get_unit_string
from django_pint_field.helpers import is_aggregate_expression
from django_pint_field.helpers import is_decimal_or_int
from django_pint_field.models import DecimalPintField
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
            (1, 0, "1."),
            (2, 1, "1.1"),
            (3, 2, "1.11"),
            (5, 3, "11.111"),
            (4, 0, "1111."),
            (3, 0, "111."),
            (2, 2, "0.11"),
            (3, 3, "0.111"),
        ],
    )
    def test_valid_inputs(self, max_digits, decimal_places, expected):
        """Test various valid input combinations."""
        assert get_quantizing_string(max_digits=max_digits, decimal_places=decimal_places) == expected

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
            get_quantizing_string(max_digits=max_digits, decimal_places=decimal_places)

    def test_edge_cases(self):
        """Test edge cases."""
        assert get_quantizing_string(max_digits=1, decimal_places=0) == "1."  # Minimum valid case
        assert get_quantizing_string(max_digits=10, decimal_places=9) == "1.111111111"  # Large number of decimal places


class TestGetPintUnit:
    """Test the get_pint_unit function."""

    def test_valid_unit(self):
        """Test getting a valid unit."""
        unit = get_pint_unit(ureg, "gram")
        assert str(unit) == "gram"
        assert unit.dimensionality == ureg.gram.dimensionality

    def test_none_unit(self):
        """Test passing None returns None."""
        assert get_pint_unit(ureg, None) is None

    def test_compound_unit(self):
        """Test getting a compound unit."""
        unit = get_pint_unit(ureg, "kilogram/meter^3")
        assert unit.dimensionality == (ureg.kilogram / ureg.meter**3).dimensionality

    def test_invalid_unit(self):
        """Test getting an invalid unit raises AttributeError."""
        with pytest.raises(AttributeError):
            get_pint_unit(ureg, "invalid_unit")


class TestGetUnitString:
    """Test the get_unit_string function."""

    def test_string_input(self):
        """Test with string input."""
        assert get_unit_string("meter") == "meter"

    def test_unit_object_input(self):
        """Test with Unit object input."""
        unit = ureg.meter
        assert get_unit_string(unit) == "meter"

    def test_tuple_input(self):
        """Test with tuple input."""
        assert get_unit_string(("Meters", "meter")) == "meter"

    def test_list_input(self):
        """Test with list input."""
        assert get_unit_string(["Meters", "meter"]) == "meter"

    def test_invalid_tuple(self):
        """Test with invalid tuple length."""
        with pytest.raises(ValidationError):
            get_unit_string(("meter", "cm", "inch"))

    def test_compound_unit(self):
        """Test with compound unit string."""
        assert get_unit_string("meter/second") == "meter/second"


class TestPintFieldProxy:
    """Test the PintFieldProxy class."""

    @pytest.fixture
    def field_instance(self):
        """Create a field instance for testing."""
        return DecimalPintField(default_unit="gram", display_decimal_places=2)

    @pytest.fixture
    def converter(self, field_instance):
        """Create a converter instance for testing."""
        return PintFieldConverter(field_instance)

    @pytest.fixture
    def proxy(self, converter):
        """Create a proxy instance with a test quantity."""
        quantity = ureg.Quantity(Decimal("10.325"), "gram")
        return PintFieldProxy(quantity, converter)

    def test_str_representation(self, proxy):
        """Test string representation with display decimal places."""
        assert str(proxy) == "10.32 gram"  # Should round to 2 decimal places

    def test_str_representation_no_decimal_places(self, converter):
        """Test string representation without display decimal places."""
        converter.field.display_decimal_places = None
        quantity = ureg.Quantity(Decimal("10.325"), "gram")
        proxy = PintFieldProxy(quantity, converter)
        assert str(proxy) == "10.325 gram"

    def test_format(self, proxy):
        """Test format method."""
        assert format(proxy, ".1f") == "10.3 gram"

    def test_getattr_unit_conversion(self, proxy):
        """Test unit conversion via attribute access."""
        converted = proxy.kilogram
        assert isinstance(converted, ureg.Quantity)
        assert converted.units == ureg.kilogram
        assert float(converted.magnitude) == pytest.approx(0.010325)

    def test_getattr_decimal_places(self, proxy):
        """Test decimal places specification via attribute access."""
        formatted = proxy.digits__3
        assert isinstance(formatted, ureg.Quantity)
        assert formatted.units == ureg.gram
        assert str(formatted.magnitude) == "10.325"

    def test_getattr_unit_conversion_with_decimal_places(self, proxy):
        """Test unit conversion with decimal places via attribute access."""
        formatted = proxy.kilogram__4
        assert isinstance(formatted, ureg.Quantity)
        assert formatted.units == ureg.kilogram
        assert str(formatted.magnitude) == "0.0103"

    def test_invalid_unit_conversion(self, proxy):
        """Test invalid unit conversion raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = proxy.invalid_unit

    def test_invalid_decimal_places(self, proxy):
        """Test invalid decimal places specification raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = proxy.gram__invalid

    def test_eq_with_proxy(self, converter):
        """Test equality with another PintFieldProxy."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy3 = PintFieldProxy(ureg.Quantity(Decimal("20.0"), "gram"), converter)

        assert proxy1 == proxy2
        assert proxy1 != proxy3

    def test_eq_with_quantity(self, converter):
        """Test equality with Quantity objects."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        quantity1 = ureg.Quantity(Decimal("10.0"), "gram")
        quantity2 = ureg.Quantity(Decimal("0.01"), "kilogram")
        quantity3 = ureg.Quantity(Decimal("20.0"), "gram")

        assert proxy == quantity1
        assert proxy == quantity2
        assert proxy != quantity3

    def test_eq_with_other_types(self, converter):
        """Test equality with non-compatible types."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)

        assert proxy != 10
        assert proxy != "10 gram"
        assert proxy is not None

    @pytest.mark.parametrize(
        "val1,val2,expected_lt,expected_gt",
        [
            (Decimal("10.0"), Decimal("20.0"), True, False),
            (Decimal("20.0"), Decimal("10.0"), False, True),
            (Decimal("10.0"), Decimal("10.0"), False, False),
        ],
    )
    def test_comparison_with_proxy(self, converter, val1, val2, expected_lt, expected_gt):
        """Test comparison operators with another PintFieldProxy."""
        proxy1 = PintFieldProxy(ureg.Quantity(val1, "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(val2, "gram"), converter)

        assert (proxy1 < proxy2) == expected_lt
        assert (proxy1 > proxy2) == expected_gt
        assert (proxy1 <= proxy2) == (expected_lt or val1 == val2)
        assert (proxy1 >= proxy2) == (expected_gt or val1 == val2)

    def test_comparison_with_quantity(self, converter):
        """Test comparison with Quantity objects."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        smaller = ureg.Quantity(Decimal("5.0"), "gram")
        equal = ureg.Quantity(Decimal("0.01"), "kilogram")
        larger = ureg.Quantity(Decimal("20.0"), "gram")

        assert proxy > smaller
        assert proxy >= smaller
        assert proxy >= equal
        assert proxy <= equal
        assert proxy < larger
        assert proxy <= larger

    def test_comparison_with_incompatible_types(self, converter):
        """Test comparison with incompatible types raises TypeError."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)

        with pytest.raises(TypeError):
            proxy < 10
        with pytest.raises(TypeError):
            proxy > "10 gram"
        with pytest.raises(TypeError):
            proxy <= None
        with pytest.raises(TypeError):
            proxy >= []

    def test_comparison_with_incompatible_units(self, converter):
        """Test comparison with incompatible units raises DimensionalityError."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        incompatible = ureg.Quantity(Decimal("10.0"), "meter")

        with pytest.raises(DimensionalityError):
            proxy < incompatible

    def test_addition(self, converter):
        """Test addition operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("5.0"), "gram"), converter)
        quantity = ureg.Quantity(Decimal("3.0"), "gram")

        # Test proxy + proxy
        result = proxy1 + proxy2
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("15.0")
        assert str(result.units) == "gram"

        # Test proxy + quantity
        result = proxy1 + quantity
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("13.0")
        assert str(result.units) == "gram"

    def test_subtraction(self, converter):
        """Test subtraction operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("3.0"), "gram"), converter)
        quantity = ureg.Quantity(Decimal("2.0"), "gram")

        # Test proxy - proxy
        result = proxy1 - proxy2
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("7.0")
        assert str(result.units) == "gram"

        # Test proxy - quantity
        result = proxy1 - quantity
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("8.0")
        assert str(result.units) == "gram"

    def test_multiplication(self, converter):
        """Test multiplication operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("2.0"), "meter"), converter)
        quantity = ureg.Quantity(Decimal("3.0"), "meter")

        # Test proxy * proxy
        result = proxy1 * proxy2
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("20.0")
        assert str(result.units) == "gram * meter"

        # Test proxy * quantity
        result = proxy1 * quantity
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("30.0")
        assert str(result.units) == "gram * meter"

    def test_division(self, converter):
        """Test division operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("2.0"), "second"), converter)
        quantity = ureg.Quantity(Decimal("5.0"), "second")

        # Test proxy / proxy
        result = proxy1 / proxy2
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("5.0")
        assert str(result.units) == "gram / second"

        # Test proxy / quantity
        result = proxy1 / quantity
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("2.0")
        assert str(result.units) == "gram / second"

    def test_floor_division(self, converter):
        """Test floor division operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("3.0"), "gram"), converter)  # Changed to same units
        quantity = ureg.Quantity(Decimal("3.0"), "gram")  # Changed to same units

        # Test proxy // proxy
        result = proxy1 // proxy2
        assert isinstance(result, ureg.Quantity)
        assert float(result.magnitude) == pytest.approx(3.0)
        assert str(result.units) == "dimensionless"  # Result of gram/gram is dimensionless

        # Test proxy // quantity
        result = proxy1 // quantity
        assert isinstance(result, ureg.Quantity)
        assert float(result.magnitude) == pytest.approx(3.0)
        assert str(result.units) == "dimensionless"  # Result of gram/gram is dimensionless

    def test_modulo(self, converter):
        """Test modulo operations."""
        proxy1 = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)
        proxy2 = PintFieldProxy(ureg.Quantity(Decimal("3.0"), "gram"), converter)
        quantity = ureg.Quantity(Decimal("3.0"), "gram")

        # Test proxy % proxy
        result = proxy1 % proxy2
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("1.0")
        assert str(result.units) == "gram"

        # Test proxy % quantity
        result = proxy1 % quantity
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("1.0")
        assert str(result.units) == "gram"

    def test_arithmetic_with_incompatible_types(self, converter):
        """Test arithmetic operations with incompatible types raise TypeError."""
        proxy = PintFieldProxy(ureg.Quantity(Decimal("10.0"), "gram"), converter)

        with pytest.raises(TypeError):
            proxy + 5
        with pytest.raises(TypeError):
            proxy - "5 gram"
        with pytest.raises(TypeError):
            proxy * None
        with pytest.raises(TypeError):
            proxy / []
        with pytest.raises(TypeError):
            proxy // {}
        with pytest.raises(TypeError):
            proxy % True

    def test_getstate_setstate(self, converter):
        """Test that PintFieldProxy can be pickled and unpickled correctly."""
        import pickle

        proxy = PintFieldProxy(ureg.Quantity(Decimal("15.789"), "gram"), converter)

        # Test pickling
        pickle_data = pickle.dumps(proxy)

        # Test unpickling
        reconstructed = pickle.loads(pickle_data)

        # Verify the reconstructed object has the same properties
        assert isinstance(reconstructed, PintFieldProxy)
        assert str(reconstructed.quantity.magnitude) == "15.789"
        assert str(reconstructed.quantity.units) == "gram"

        # Verify the converter was properly reconstructed
        assert hasattr(reconstructed.converter, "field")
        assert reconstructed.converter.field.default_unit == "gram"
        assert reconstructed.converter.field.display_decimal_places == 2

        # Test that the proxy operations still work after pickling
        converted = reconstructed.kilogram
        assert isinstance(converted, ureg.Quantity)
        assert float(converted.magnitude) == pytest.approx(0.015789)
        assert str(converted.units) == "kilogram"

    def test_edge_cases_and_error_handling(self, converter):
        """Test edge cases and error handling."""
        # Test with zero values
        zero_proxy = PintFieldProxy(ureg.Quantity(Decimal("0"), "gram"), converter)
        positive_proxy = PintFieldProxy(ureg.Quantity(Decimal("10"), "gram"), converter)

        assert zero_proxy < positive_proxy
        assert zero_proxy <= positive_proxy
        assert positive_proxy > zero_proxy
        assert positive_proxy >= zero_proxy

        # Test division by zero
        with pytest.raises(ZeroDivisionError):
            positive_proxy / zero_proxy

        # Test unit conversions with extreme values
        large_proxy = PintFieldProxy(ureg.Quantity(Decimal("1e10"), "gram"), converter)
        small_proxy = PintFieldProxy(ureg.Quantity(Decimal("1e-10"), "gram"), converter)

        large_kg = large_proxy.kilogram
        small_kg = small_proxy.kilogram

        assert float(large_kg.magnitude) == pytest.approx(1e7)
        assert float(small_kg.magnitude) == pytest.approx(1e-13)


class TestIsAggregateExpression:
    """Test the is_aggregate_expression function."""

    def test_pint_aggregate(self):
        """Test with object having is_pint_aggregate attribute."""

        class MockAggregate:
            """Mock aggregate class."""

            is_pint_aggregate = True

        assert is_aggregate_expression(MockAggregate())

    def test_constructor_attribute(self):
        """Test with object having _constructor attribute."""

        class MockAggregate:
            """Mock aggregate class."""

            _constructor = True

        assert is_aggregate_expression(MockAggregate())

    def test_django_pint_field_module(self):
        """Test with object from django_pint_field.aggregates module."""

        class MockAggregate:
            """Mock aggregate class."""

        MockAggregate.__module__ = "django_pint_field.aggregates"

        assert is_aggregate_expression(MockAggregate())

    def test_django_aggregates_module(self):
        """Test with object from django.db.models.aggregates module."""

        class MockAggregate:
            """Mock aggregate class."""

        MockAggregate.__module__ = "django.db.models.aggregates"

        assert is_aggregate_expression(MockAggregate())

    def test_non_aggregate(self):
        """Test with non-aggregate object."""

        class MockNonAggregate:
            """Mock aggregate class."""

        MockNonAggregate.__module__ = "some.other.module"

        assert not is_aggregate_expression(MockNonAggregate())


class TestPintFieldConverter:
    """Test the PintFieldConverter class."""

    @pytest.fixture
    def field_instance(self):
        """Create a field instance for testing."""
        return DecimalPintField(default_unit="gram", display_decimal_places=2)

    @pytest.fixture
    def converter(self, field_instance):
        """Create a converter instance for testing."""
        return PintFieldConverter(field_instance)

    def test_convert_to_unit_valid(self, converter):
        """Test converting to a valid unit."""
        quantity = ureg.Quantity(1000, "gram")
        converted = converter.convert_to_unit(quantity, "kilogram")
        assert converted.magnitude == 1
        assert str(converted.units) == "kilogram"

    def test_convert_to_unit_none_value(self, converter):
        """Test converting None value returns None."""
        assert converter.convert_to_unit(None, "kilogram") is None

    def test_convert_to_unit_invalid_unit(self, converter):
        """Test converting to invalid unit returns None."""
        quantity = ureg.Quantity(1000, "gram")
        assert converter.convert_to_unit(quantity, "invalid_unit") is None

    def test_convert_to_unit_incompatible_unit(self, converter):
        """Test converting to incompatible unit returns None."""
        quantity = ureg.Quantity(1000, "gram")
        with pytest.raises(DimensionalityError):
            converter.convert_to_unit(quantity, "second")
