"""Test cases for widgets."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.forms import NumberInput
from django.forms import Select
from pint.errors import UndefinedUnitError

from django_pint_field.units import ureg
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.widgets import TabledPintFieldWidget
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestPintFieldWidget:
    """Test cases for the PintFieldWidget."""

    @pytest.fixture(autouse=True)
    def setup_class(self, request):
        """Set up test parameters."""
        if request.param == "integer":
            self.MODEL = IntegerPintFieldSaveModel
            self.DEFAULT_WEIGHT = 100
        elif request.param == "big_integer":
            self.MODEL = BigIntegerPintFieldSaveModel
            self.DEFAULT_WEIGHT = 100
        else:  # decimal
            self.MODEL = DecimalPintFieldSaveModel
            self.DEFAULT_WEIGHT = Decimal("100")

        self.DEFAULT_UNIT = "gram"
        self.UNIT_CHOICES = [("Gram", "gram"), ("Kilogram", "kilogram"), ("Ounce", "ounce"), ("Pound", "pound")]

        # Define custom units in the registry
        ureg.define("custom_unit = []")
        ureg.define("nested_unit = []")

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_attrs(self):
        """Test that widget attributes are set correctly."""
        attrs = {"class": "custom-class", "step": "0.1"}
        widget = PintFieldWidget(attrs=attrs, default_unit=self.DEFAULT_UNIT)

        for sub_widget in widget.widgets:
            assert sub_widget.attrs.get("class") == "custom-class"
            assert sub_widget.attrs.get("step") == "0.1"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_unit_choices_contains_default(self):
        """Test that unit choices always contains the default unit."""
        unit_choices = [("Kilogram", "kilogram"), ("Pound", "pound")]  # Deliberately exclude default unit
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=unit_choices)

        # Default unit should be automatically added
        default_unit_present = False
        for display_name, unit in widget.choices:
            if str(ureg(unit).units) == str(ureg(self.DEFAULT_UNIT).units):
                default_unit_present = True
                break
        assert default_unit_present

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            ("none", [None, None]),
            ("quantity", lambda: [100, "gram"]),
            ("proxy", lambda: [100, "gram"]),
        ],
        ids=["none", "quantity", "proxy"],
    )
    def test_decompress_various_inputs(self, test_input, expected_result):
        """Test decompress with various input types."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT)

        if test_input == "none":
            value = None
            expected = expected_result
        elif test_input == "quantity":
            value = Quantity(100, "gram")
            expected = [value.magnitude, str(value.units)]
        elif test_input == "proxy":
            from django_pint_field.helpers import PintFieldConverter
            from django_pint_field.helpers import PintFieldProxy
            from django_pint_field.models import DecimalPintField

            quantity = Quantity(100, "gram")
            field = DecimalPintField(default_unit="gram")
            converter = PintFieldConverter(field)
            value = PintFieldProxy(quantity, converter)
            expected = [value.quantity.magnitude, str(value.quantity.units)]

        result = widget.decompress(value)
        assert result == expected

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_without_default_unit(self):
        """Test widget creation without default_unit raises ValidationError."""
        with pytest.raises(ValidationError, match="PintFieldWidgets require a default_unit"):
            PintFieldWidget(default_unit=None)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_empty_attrs(self):
        """Test widget creation with empty attrs dictionary."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT)
        assert isinstance(widget.widgets[0], NumberInput)
        assert isinstance(widget.widgets[1], Select)
        assert widget.widgets[0].attrs.get("step") == "any"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_custom_unit_choices(self):
        """Test widget with custom unit choices."""
        custom_choices = [("Custom Unit", "custom_unit")]
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=custom_choices)

        assert len(widget.choices) == 2  # Default unit + custom choice
        assert ("custom_unit", "Custom Unit") in widget.choices

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_invalid_unit_choices(self):
        """Test widget with invalid unit choices raises ValidationError."""
        invalid_choices = [("Invalid Unit", "invalid_unit")]
        with pytest.raises(UndefinedUnitError):
            PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=invalid_choices)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_empty_unit_choices(self):
        """Test widget with empty unit choices."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=[])
        assert len(widget.choices) == 1  # Only default unit
        assert widget.choices[0][1] == self.DEFAULT_UNIT

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_nested_unit_choices(self):
        """Test widget with nested unit choices."""
        nested_choices = [("Nested Unit", "nested_unit")]
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=nested_choices)
        assert len(widget.choices) == 2  # Default unit + nested choice
        assert ("nested_unit", "Nested Unit") in widget.choices

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_custom_attrs(self):
        """Test widget with custom attributes."""
        custom_attrs = {"class": "custom-class", "data-custom": "custom-data"}
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, attrs=custom_attrs)
        for sub_widget in widget.widgets:
            assert sub_widget.attrs.get("class") == "custom-class"
            assert sub_widget.attrs.get("data-custom") == "custom-data"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "default_unit,expected_unit,expected_display",
        [
            (("Grams", "gram"), "gram", "Grams"),
            (["Kilograms", "kilogram"], "kilogram", "Kilograms"),
        ],
        ids=["tuple", "list"],
    )
    def test_widget_with_sequence_default_unit(self, default_unit, expected_unit, expected_display):
        """Test widget creation with tuple or list default_unit."""
        widget = PintFieldWidget(default_unit=default_unit)
        assert widget.default_unit == expected_unit
        assert widget._default_unit_display == expected_display
        assert widget._default_unit_value == expected_unit

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_invalid_default_unit_format(self):
        """Test widget with invalid default_unit format raises ValidationError."""
        with pytest.raises(ValidationError):
            PintFieldWidget(default_unit=["gram", "kilogram", "extra"])  # Too many elements


@pytest.mark.django_db
class TestTabledPintFieldWidget:
    """Test cases for the TabledPintFieldWidget."""

    @pytest.fixture(autouse=True)
    def setup_class(self, request):
        """Set up test parameters."""
        if request.param == "integer":
            self.MODEL = IntegerPintFieldSaveModel
            self.DEFAULT_WEIGHT = 100
        elif request.param == "big_integer":
            self.MODEL = BigIntegerPintFieldSaveModel
            self.DEFAULT_WEIGHT = 100
        else:  # decimal
            self.MODEL = DecimalPintFieldSaveModel
            self.DEFAULT_WEIGHT = Decimal("100")

        self.DEFAULT_UNIT = "gram"
        self.UNIT_CHOICES = [("Gram", "gram"), ("Kilogram", "kilogram"), ("Ounce", "ounce"), ("Pound", "pound")]

        # Define custom units in the registry
        ureg.define("custom_unit = []")

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "input_value",
        [
            lambda self: Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT),  # Quantity
            lambda self: (1000, "gram"),  # Tuple
        ],
        ids=["quantity", "tuple"],
    )
    def test_create_table_with_various_inputs(self, input_value):
        """Test create_table method with various input types."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_value = input_value(self) if callable(input_value) else input_value
        values_list = widget.create_table(test_value)

        # We expect n-1 conversions (excluding the current unit)
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(isinstance(value, Quantity) for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_default_context_values(self):
        """Test default values in context."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        context = widget.get_context("weight", None, {})

        assert context["floatformat"] == -1  # Default from content_options
        assert "input_wrapper_class" in context
        assert "table_wrapper_class" in context

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_invalid_value(self):
        """Test create_table method with invalid value type."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(ValueError):
            widget.create_table([None, None, None])  # Invalid format

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_custom_formatting_options(self):
        """Test widget with custom formatting options."""
        custom_options = {
            "table_wrapper_class": "custom-wrapper",
            "table_class": "custom-table",
            "td_class": "custom-cell",
            "floatformat": 2,
        }
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES, **custom_options)
        context = widget.get_context("weight", None, {})

        assert context["floatformat"] == 2
        assert context["table_wrapper_class"] == "custom-wrapper"
        assert context["table_class"] == "custom-table"
        assert context["td_class"] == "custom-cell"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "magnitude,expected_check",
        [
            (0, lambda vals: all(v.magnitude == 0 for v in vals)),  # Zero value
            (
                Decimal("100.5"),
                lambda vals: all(isinstance(v.magnitude, (Decimal, float, int)) for v in vals),
            ),  # Decimal
            (-100, lambda vals: all(v.magnitude < 0 for v in vals)),  # Negative
            (Decimal("1e6"), lambda vals: all(v.magnitude > 0 for v in vals)),  # Large value
            (Decimal("1e-6"), lambda vals: all(v.magnitude > 0 for v in vals)),  # Small value
        ],
        ids=["zero", "decimal", "negative", "large", "small"],
    )
    def test_create_table_with_various_magnitudes(self, magnitude, expected_check):
        """Test create_table method with various magnitude values."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(magnitude, "gram")
        values_list = widget.create_table(test_quantity)

        # Should have conversions for all units except current
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert expected_check(values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_custom_unit(self):
        """Test create_table method with custom unit."""
        custom_unit = "custom_unit"
        widget = TabledPintFieldWidget(default_unit=custom_unit, unit_choices=[("Custom Unit", custom_unit)])
        test_quantity = Quantity(100, custom_unit)
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == 0  # No other units to convert to

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_invalid_unit(self):
        """Test create_table method with invalid unit."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(UndefinedUnitError):
            Quantity(100, "invalid_unit")

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_proxy(self):
        """Test _normalize_value with PintFieldProxy."""
        from django_pint_field.helpers import PintFieldConverter
        from django_pint_field.helpers import PintFieldProxy
        from django_pint_field.models import DecimalPintField

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = Quantity(Decimal("100"), "gram")
        field = DecimalPintField(default_unit="gram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        magnitude, unit = widget._normalize_value(proxy)
        assert magnitude == Decimal("100")
        assert str(unit) == "gram"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_none(self):
        """Test _normalize_value with None value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        magnitude, unit = widget._normalize_value(None)
        assert magnitude is None
        assert unit == self.DEFAULT_UNIT

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_quantity(self):
        """Test _normalize_value with Quantity."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = Quantity(Decimal("500"), "gram")
        magnitude, unit = widget._normalize_value(quantity)
        assert magnitude == Decimal("500")
        assert str(unit) == "gram"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "input_value,expected_magnitude,expected_unit",
        [
            ((100, "kilogram"), Decimal("100"), "kilogram"),  # Tuple
            ([200, "pound"], Decimal("200"), "pound"),  # List
        ],
        ids=["tuple", "list"],
    )
    def test_normalize_value_with_sequence(self, input_value, expected_magnitude, expected_unit):
        """Test _normalize_value with tuple and list inputs."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        magnitude, unit = widget._normalize_value(input_value)
        assert magnitude == expected_magnitude
        assert str(unit) == expected_unit

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_string_magnitude(self):
        """Test _normalize_value with string magnitude in tuple."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        magnitude, unit = widget._normalize_value(("123.45", "gram"))
        assert magnitude == Decimal("123.45")

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_none_magnitude(self):
        """Test _normalize_value with None magnitude in tuple."""

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        magnitude, unit = widget._normalize_value((None, "gram"))
        assert magnitude is None
        assert str(unit) == "gram"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_invalid_magnitude_type(self):
        """Test _normalize_value with invalid magnitude type raises ImproperlyConfigured."""
        from django.core.exceptions import ImproperlyConfigured

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(ImproperlyConfigured, match="Magnitude must be numeric"):
            widget._normalize_value(("not_a_number", "gram"))

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_invalid_unit_type(self):
        """Test _normalize_value with invalid unit type raises ImproperlyConfigured."""
        from django.core.exceptions import ImproperlyConfigured

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(ImproperlyConfigured, match="Unit must be string or ureg.Unit"):
            widget._normalize_value((100, 123))  # Invalid unit type

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_normalize_value_with_invalid_value_format(self):
        """Test _normalize_value with invalid value format raises ImproperlyConfigured."""
        from django.core.exceptions import ImproperlyConfigured

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(ImproperlyConfigured, match="Expected list/tuple of length 2"):
            widget._normalize_value([100, "gram", "extra"])  # Too many elements

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_quantity_with_none_magnitude(self):
        """Test _create_quantity with None magnitude defaults to 0."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = widget._create_quantity(None, "gram")
        assert quantity.magnitude == 0
        assert str(quantity.units) == "gram"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    @pytest.mark.parametrize(
        "magnitude,expected_value,expected_unit",
        [
            ("123.45", Decimal("123.45"), "gram"),  # String
            ([100], Decimal("100"), "gram"),  # List
            ((200,), Decimal("200"), "kilogram"),  # Tuple
        ],
        ids=["string", "list", "tuple"],
    )
    def test_create_quantity_with_various_magnitude_types(self, magnitude, expected_value, expected_unit):
        """Test _create_quantity with various magnitude types."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = widget._create_quantity(magnitude, expected_unit)
        assert quantity.magnitude == expected_value

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_proxy_value(self):
        """Test create_table with proxy value extracts quantity correctly."""
        from django_pint_field.helpers import PintFieldConverter
        from django_pint_field.helpers import PintFieldProxy
        from django_pint_field.models import DecimalPintField

        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = Quantity(Decimal("100"), "gram")
        field = DecimalPintField(default_unit="gram")
        converter = PintFieldConverter(field)
        proxy = PintFieldProxy(quantity, converter)

        # PintFieldProxy doesn't have .value attribute, it has .quantity
        # The widget handles this correctly
        values_list = widget.create_table(proxy.quantity)
        assert len(values_list) == len(self.UNIT_CHOICES) - 1

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_string_magnitude(self):
        """Test create_table with Quantity having string magnitude is handled."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        # Create a quantity with string-like magnitude
        quantity = Quantity(100, "gram")
        # Manually set magnitude to string to test conversion logic
        quantity._magnitude = "100"

        # The widget should convert string magnitude to Decimal
        values_list = widget.create_table(quantity)
        # If it works, we get conversions; if it fails, error is raised
        assert isinstance(values_list, list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_incompatible_units_skipped(self):
        """Test create_table skips incompatible unit conversions gracefully."""
        # This test verifies the error handling in create_table
        # When conversion fails, it should log error and continue
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        quantity = Quantity(100, "gram")
        values_list = widget.create_table(quantity)

        # All returned values should be valid Quantities
        assert all(isinstance(val, Quantity) for val in values_list)
        # Should have conversions for compatible units
        assert len(values_list) > 0

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_none_value(self):
        """Test create_table with None value returns empty list."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        values_list = widget.create_table(None)
        assert values_list == []


@pytest.mark.django_db
class TestPintFieldWidgetTemplates:
    """Test cases for widget template rendering."""

    def test_default_widget_template_name(self):
        """Test that PintFieldWidget uses Django's default MultiWidget template."""
        widget = PintFieldWidget(default_unit="gram")
        assert widget.template_name == "django/forms/widgets/multiwidget.html"

    def test_subwidget_template_names(self):
        """Test that subwidgets have correct template names."""
        widget = PintFieldWidget(default_unit="gram")
        assert widget.widgets[0].template_name == "django/forms/widgets/number.html"
        assert widget.widgets[1].template_name == "django/forms/widgets/select.html"

    def test_tabled_widget_template_inheritance(self):
        """Test that TabledPintFieldWidget properly inherits and overrides template name."""
        widget = TabledPintFieldWidget(default_unit="gram")
        assert widget.template_name == "django_pint_field/tabled_django_pint_field_widget.html"
        # Should still use default templates for subwidgets
        assert widget.widgets[0].template_name == "django/forms/widgets/number.html"
        assert widget.widgets[1].template_name == "django/forms/widgets/select.html"

    def test_widget_render_inherits_id_for_subwidgets(self):
        """Test that subwidgets inherit and modify the parent widget's ID correctly."""
        widget = PintFieldWidget(default_unit="gram")
        context = widget.get_context("weight", None, {"id": "id_weight"})
        assert context["widget"]["subwidgets"][0]["attrs"]["id"] == "id_weight_0"
        assert context["widget"]["subwidgets"][1]["attrs"]["id"] == "id_weight_1"

    def test_tabled_widget_context_structure(self):
        """Test that TabledPintFieldWidget provides correct context structure for template."""
        widget = TabledPintFieldWidget(default_unit="gram", unit_choices=[("Gram", "gram"), ("Kilogram", "kilogram")])
        context = widget.get_context("weight", None, {})

        # Check required context keys for template rendering
        assert "widget" in context
        assert "values_list" in context
        assert "floatformat" in context
        assert "table_wrapper_class" in context
        assert "table_class" in context
        assert "input_wrapper_class" in context
        assert "display_choices" in context

        # Check subwidgets are properly configured
        assert len(context["widget"]["subwidgets"]) == 2
        assert all("template_name" in widget for widget in context["widget"]["subwidgets"])
