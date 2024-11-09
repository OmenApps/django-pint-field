"""Test cases for widgets."""

from decimal import Decimal

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.forms import NumberInput
from django.forms import Select

from django_pint_field.units import ureg
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.widgets import TabledPintFieldWidget
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


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
        self.UNIT_CHOICES = ["gram", "kilogram", "ounce", "pound"]

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
        unit_choices = ["kilogram", "pound"]  # Deliberately exclude default unit
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=unit_choices)

        # Default unit should be automatically added
        assert any(self.DEFAULT_UNIT in choice for choice in widget.choices)

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
        quantity = ureg.Quantity(100, "gram")
        result = widget.decompress(quantity)
        assert result == quantity

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_without_default_unit(self):
        """Test widget creation without default_unit raises ValidationError."""
        with pytest.raises(ValidationError, match="PintFieldWidgets require a default_unit"):
            PintFieldWidget()

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_widget_with_empty_attrs(self):
        """Test widget creation with empty attrs dictionary."""
        widget = PintFieldWidget(default_unit=self.DEFAULT_UNIT)
        assert isinstance(widget.widgets[0], NumberInput)
        assert isinstance(widget.widgets[1], Select)
        assert widget.widgets[0].attrs.get("step") == "any"


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
        self.UNIT_CHOICES = ["gram", "kilogram", "ounce", "pound"]

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_numeric(self):
        """Test create_table method with a numeric value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        values_list = widget.create_table(self.DEFAULT_WEIGHT)

        assert len(values_list) == len(self.UNIT_CHOICES)
        assert all(isinstance(value, ureg.Quantity) for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_default_context_values(self):
        """Test default values in context."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        context = widget.get_context("weight", None, {})

        assert context["floatformat"] == 6
        assert context["table_class"] == "p-5 m-5"
        assert context["td_class"] == "text-end"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_custom_value(self):
        """Test create_table method with a custom Quantity value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = ureg.Quantity(1000, "gram")
        values_list = widget.create_table(test_quantity)

        # Test conversion to all units
        for value in values_list:
            assert isinstance(value, ureg.Quantity)
            assert value.dimensionality == test_quantity.dimensionality

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_tuple_value(self):
        """Test create_table method with a tuple value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_tuple = (1000, "gram")
        values_list = widget.create_table(test_tuple)

        assert len(values_list) == len(self.UNIT_CHOICES)
        assert all(isinstance(value, ureg.Quantity) for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_invalid_value(self):
        """Test create_table method with invalid value type."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        with pytest.raises(ImproperlyConfigured):
            widget.create_table([None, None])

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_custom_formatting_options(self):
        """Test widget with custom formatting options."""
        widget = TabledPintFieldWidget(
            default_unit=self.DEFAULT_UNIT,
            unit_choices=self.UNIT_CHOICES,
            floatformat=2,
            table_class="custom-table",
            td_class="custom-cell",
        )
        context = widget.get_context("weight", None, {})

        assert context["floatformat"] == 2
        assert context["table_class"] == "custom-table"
        assert context["td_class"] == "custom-cell"

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_zero_value(self):
        """Test create_table method with zero value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = ureg.Quantity(0, "gram")
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(value.magnitude == 0 for value in values_list)

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_create_table_with_decimal_value(self):
        """Test create_table method with decimal value."""
        widget = TabledPintFieldWidget(default_unit=self.DEFAULT_UNIT, unit_choices=self.UNIT_CHOICES)
        test_quantity = ureg.Quantity(Decimal("100.5"), "gram")
        values_list = widget.create_table(test_quantity)

        assert len(values_list) == len(self.UNIT_CHOICES) - 1
        assert all(isinstance(value.magnitude, (Decimal, float, int)) for value in values_list)