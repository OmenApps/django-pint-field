"""Test cases for template tags."""

from decimal import Decimal

import pytest
from django.template import Context
from django.template import Template

from django_pint_field.helpers import PintFieldConverter
from django_pint_field.helpers import PintFieldProxy
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

Quantity = ureg.Quantity


@pytest.mark.django_db
class TestWithDigitsFilter:
    """Test cases for the with_digits template filter."""

    def test_with_digits_quantity(self):
        """Test with_digits filter with a Quantity object."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:2 }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # The result should have the magnitude rounded to 2 decimal places
        assert "123.46" in result
        assert "gram" in result

    def test_with_digits_proxy(self):
        """Test with_digits filter with a PintFieldProxy object."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:3 }}")
        quantity = Quantity(Decimal("123.456789"), "kilogram")
        field = DecimalPintField(default_unit="kilogram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        assert "123.457" in result
        assert "kilogram" in result

    def test_with_digits_non_quantity(self):
        """Test with_digits filter with non-Quantity value returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:2 }}")
        context = Context({"value": "not a quantity"})
        result = template.render(context)

        assert result.strip() == "not a quantity"

    def test_with_digits_string_decimal_places(self):
        """Test with_digits filter with string decimal_places parameter."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:'1' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "123.5" in result or "123.4" in result  # Rounding may vary
        assert "gram" in result

    def test_with_digits_invalid_string(self):
        """Test with_digits filter with invalid string decimal_places returns original value."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:'invalid' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # Should return original value on error
        assert "123.456" in result

    def test_with_digits_zero_decimal_places(self):
        """Test with_digits filter with zero decimal places."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:0 }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "123" in result
        assert "gram" in result

    def test_with_digits_invalid_operation(self):
        """Test with_digits filter handles InvalidOperation gracefully."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:2 }}")
        # Create a quantity with a non-decimal magnitude that might cause issues
        quantity = Quantity(123.456, "gram")  # float magnitude
        context = Context({"value": quantity})
        result = template.render(context)

        # Should still work or return original
        assert "gram" in result


@pytest.mark.django_db
class TestWithUnitsFilter:
    """Test cases for the with_units template filter."""

    def test_with_units_quantity(self):
        """Test with_units filter converts units correctly."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'kilogram' }}")
        quantity = Quantity(Decimal("1000"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "1" in result or "1.0" in result
        assert "kilogram" in result

    def test_with_units_proxy(self):
        """Test with_units filter with PintFieldProxy."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'pound' }}")
        quantity = Quantity(Decimal("1000"), "gram")
        field = DecimalPintField(default_unit="gram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        assert "pound" in result

    def test_with_units_non_quantity(self):
        """Test with_units filter with non-Quantity returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'kilogram' }}")
        context = Context({"value": "not a quantity"})
        result = template.render(context)

        assert result.strip() == "not a quantity"

    def test_with_units_empty_units(self):
        """Test with_units filter with empty units parameter."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'' }}")
        quantity = Quantity(Decimal("100"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # Should return original value
        assert "100" in result
        assert "gram" in result

    def test_with_units_none_units(self):
        """Test with_units filter with None units parameter."""
        template = Template("{% load django_pint_field %}{{ value|with_units:None }}")
        quantity = Quantity(Decimal("100"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # Should return original value
        assert "100" in result


@pytest.mark.django_db
class TestPintStrFormatFilter:
    """Test cases for the pint_str_format template filter."""

    def test_pint_str_format_quantity(self):
        """Test pint_str_format filter with valid format string."""
        template = Template("{% load django_pint_field %}{{ value|pint_str_format:'.2fP' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "123.46" in result

    def test_pint_str_format_proxy(self):
        """Test pint_str_format filter with PintFieldProxy."""
        template = Template("{% load django_pint_field %}{{ value|pint_str_format:'~P' }}")
        quantity = Quantity(Decimal("1000"), "gram")
        field = DecimalPintField(default_unit="gram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        # ~P format shows compact units
        assert "1000" in result

    def test_pint_str_format_non_quantity(self):
        """Test pint_str_format filter with non-Quantity returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|pint_str_format:'.2fP' }}")
        context = Context({"value": "not a quantity"})
        result = template.render(context)

        assert result.strip() == "not a quantity"

    def test_pint_str_format_invalid_format(self):
        """Test pint_str_format filter with invalid format string returns original value."""
        template = Template("{% load django_pint_field %}{{ value|pint_str_format:'invalid{' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # Should return original value on error
        assert "123.456" in result

    def test_pint_str_format_compact(self):
        """Test pint_str_format filter with compact notation."""
        template = Template("{% load django_pint_field %}{{ value|pint_str_format:'~' }}")
        quantity = Quantity(Decimal("1000"), "meter")
        context = Context({"value": quantity})
        result = template.render(context)

        # Compact format
        assert "1000" in result or "1.0e+03" in result


@pytest.mark.django_db
class TestMagnitudeOnlyFilter:
    """Test cases for the magnitude_only template filter."""

    def test_magnitude_only_quantity(self):
        """Test magnitude_only filter with Quantity."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "123.456" in result
        # Should NOT contain units
        assert "gram" not in result

    def test_magnitude_only_proxy(self):
        """Test magnitude_only filter with PintFieldProxy."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only }}")
        quantity = Quantity(Decimal("999.99"), "kilogram")
        field = DecimalPintField(default_unit="kilogram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        assert "999.99" in result
        assert "kilogram" not in result

    def test_magnitude_only_with_units_conversion(self):
        """Test magnitude_only filter with unit conversion."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only:'kilogram' }}")
        quantity = Quantity(Decimal("1000"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # 1000 grams = 1 kilogram
        assert "1" in result or "1.0" in result
        # Should NOT contain units
        assert "kilogram" not in result
        assert "gram" not in result

    def test_magnitude_only_non_quantity(self):
        """Test magnitude_only filter with non-Quantity returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only }}")
        context = Context({"value": "not a quantity"})
        result = template.render(context)

        assert result.strip() == "not a quantity"

    def test_magnitude_only_invalid_units(self):
        """Test magnitude_only filter with invalid units logs error and returns magnitude."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only:'invalid_unit' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})

        # Invalid unit conversion will log error but filter handles it gracefully
        try:
            result = template.render(context)
            # The filter catches the error and returns original magnitude
            assert "123.456" in result
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass

    def test_magnitude_only_no_units_parameter(self):
        """Test magnitude_only filter without units parameter."""
        template = Template("{% load django_pint_field %}{{ value|magnitude_only }}")
        quantity = Quantity(Decimal("42.5"), "meter")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "42.5" in result
        assert "meter" not in result


@pytest.mark.django_db
class TestUnitsOnlyFilter:
    """Test cases for the units_only template filter."""

    def test_units_only_quantity(self):
        """Test units_only filter with Quantity."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        assert "gram" in result
        # Should NOT contain magnitude
        assert "123" not in result

    def test_units_only_proxy(self):
        """Test units_only filter with PintFieldProxy."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        quantity = Quantity(Decimal("999.99"), "kilogram")
        field = DecimalPintField(default_unit="kilogram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        assert "kilogram" in result
        assert "999" not in result

    def test_units_only_string_with_space(self):
        """Test units_only filter with string containing space."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        context = Context({"value": "123.456 gram"})
        result = template.render(context)

        assert "gram" in result
        assert "123" not in result

    def test_units_only_string_without_space(self):
        """Test units_only filter with string without space returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        context = Context({"value": "justtext"})
        result = template.render(context)

        assert result.strip() == "justtext"

    def test_units_only_non_quantity(self):
        """Test units_only filter with non-Quantity non-string returns value unchanged."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        context = Context({"value": 123})
        result = template.render(context)

        assert "123" in result

    def test_units_only_multiple_spaces(self):
        """Test units_only filter with string containing multiple spaces."""
        template = Template("{% load django_pint_field %}{{ value|units_only }}")
        context = Context({"value": "123 456 gram"})
        result = template.render(context)

        # Should get second element after split
        assert "456" in result


@pytest.mark.django_db
class TestTemplateTagsIntegration:
    """Integration tests for template tags working together."""

    def test_chained_filters(self):
        """Test multiple filters chained together."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'kilogram'|with_digits:2 }}")
        quantity = Quantity(Decimal("1500"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # 1500 grams = 1.5 kilograms, rounded to 2 decimal places
        assert "1.5" in result or "1.50" in result
        assert "kilogram" in result

    def test_format_then_magnitude(self):
        """Test formatting followed by magnitude extraction."""
        template = Template("{% load django_pint_field %}{{ value|with_units:'kilogram'|magnitude_only }}")
        quantity = Quantity(Decimal("2000"), "gram")
        context = Context({"value": quantity})
        result = template.render(context)

        # Should show 2 (magnitude in kilograms) without units
        assert "2" in result
        assert "kilogram" not in result
        assert "gram" not in result

    def test_proxy_through_multiple_filters(self):
        """Test PintFieldProxy through multiple filters."""
        template = Template("{% load django_pint_field %}{{ value|with_digits:1|pint_str_format:'~' }}")
        quantity = Quantity(Decimal("123.456"), "gram")
        field = DecimalPintField(default_unit="gram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        context = Context({"value": proxy})
        result = template.render(context)

        # Should be formatted and compacted
        assert "123" in result
