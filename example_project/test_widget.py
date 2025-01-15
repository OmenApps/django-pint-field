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
    def test_decompress_none_value(self):
        """Test decompress method with None value."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT)
        result = widget.decompress(None)
        assert result == [None, None]

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_decompress_quantity_value(self):
        """Test decompress method with Quantity value."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT)
        quantity = Quantity(100, "gram")
        result = widget.decompress(quantity)
        assert result == [quantity.magnitude, str(quantity.units)]

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
    def test_create_table_with_numeric(self):
        """Test create_table method with a numeric value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        values_list = widget.create_table(test_quantity)

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
    def test_create_table_with_custom_value(self):
        """Test create_table method with a custom Quantity value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(1000, "gram")
        values_list = widget.create_table(test_quantity)

        # Test conversion to all units (except current)
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        for value in values_list:
            assert isinstance(value, Quantity)
            assert value.dimensionality == test_quantity.dimensionality

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_tuple_value(self):
        """Test create_table method with a tuple value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_tuple = (1000, "gram")
        values_list = widget.create_table(test_tuple)

        # Test conversion to all units (except current)
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(isinstance(value, Quantity) for value in values_list)

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
    def test_create_table_with_zero_value(self):
        """Test create_table method with zero value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(0, "gram")
        values_list = widget.create_table(test_quantity)

        # Should have conversions for all units except current
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(value.magnitude == 0 for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_decimal_value(self):
        """Test create_table method with decimal value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(Decimal("100.5"), "gram")
        values_list = widget.create_table(test_quantity)

        # Should have conversions for all units except current
        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(isinstance(value.magnitude, (Decimal, float, int)) for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_negative_value(self):
        """Test create_table method with negative value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(-100, "gram")
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(value.magnitude < 0 for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_large_value(self):
        """Test create_table method with large value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(Decimal("1e6"), "gram")  # Use Decimal for large values
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(value.magnitude > 0 for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_small_value(self):
        """Test create_table method with small value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = Quantity(Decimal("1e-6"), "gram")  # Use Decimal for small values
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(value.magnitude > 0 for value in values_list)

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
