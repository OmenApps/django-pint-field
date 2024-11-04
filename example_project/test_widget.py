"""Tests for the widgets of the django-pint-field package."""

from decimal import Decimal

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from pint import DimensionalityError
from pint import UndefinedUnitError

from django_pint_field.forms import DecimalPintFormField
from django_pint_field.forms import IntegerPintFormField
from django_pint_field.units import ureg
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.widgets import TabledPintFieldWidget
from example_project.example.models import ChoicesDefinedInModel
from example_project.example.models import HayBale


@pytest.fixture
def haybale_form():
    """Create a HayBale form with test fields."""

    class HayBaleForm(forms.ModelForm):
        """Form for testing HayBale model."""

        weight_int = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram", "kilogram"])
        weight_bigint = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram", "kilogram"])
        weight_decimal = DecimalPintFormField(
            default_unit="gram", unit_choices=["ounce", "gram", "kilogram"], max_digits=10, decimal_places=2
        )

        class Meta:
            """Meta class."""

            model = HayBale
            fields = ["weight_int", "weight_bigint", "weight_decimal"]

    return HayBaleForm


@pytest.fixture
def nullable_weight_form():
    """Create a form with nullable weight fields."""

    class NullableWeightForm(forms.Form):
        """Form with nullable weight fields."""

        weight_int = IntegerPintFormField(default_unit="gram", required=False)
        weight_decimal = DecimalPintFormField(default_unit="gram", required=False, max_digits=10, decimal_places=2)

    return NullableWeightForm


@pytest.fixture
def unit_choices_form():
    """Create a form with unit choices."""

    class UnitChoicesForm(forms.Form):
        """Form with fields for testing unit choices."""

        distance = IntegerPintFormField(default_unit="kilometer", unit_choices=["mile", "kilometer", "yard", "feet"])

    return UnitChoicesForm


@pytest.fixture
def model_choices_form():
    """Create a form with choices defined in model."""

    class UnitChoicesDefinedInModelFieldModelForm(forms.ModelForm):
        """Form with fields for testing choices defined in model."""

        class Meta:
            """Meta class."""

            model = ChoicesDefinedInModel
            fields = ["weight_int", "weight_bigint", "weight_decimal"]

    return UnitChoicesDefinedInModelFieldModelForm


@pytest.fixture
def extreme_values():
    """Provide extreme test values."""
    return {
        "very_small": 1e-10,
        "very_large": 1e10,
        "zero": 0,
        "negative": -100,
        "max_int": 2147483647,
        "min_int": -2147483648,
    }


@pytest.fixture
def edge_case_form():
    """Create a form with fields for testing edge cases."""

    class EdgeCaseForm(forms.Form):
        """Form with fields for testing edge cases."""

        weight = IntegerPintFormField(default_unit="gram", unit_choices=["gram", "kilogram", "milligram"])
        precise_weight = DecimalPintFormField(
            default_unit="gram", unit_choices=["gram", "kilogram", "milligram"], max_digits=20, decimal_places=10
        )

    return EdgeCaseForm


@pytest.fixture
def custom_widget_form():
    """Create a form with custom widget attributes."""

    class CustomWidgetForm(forms.Form):
        """Form with custom widget attributes."""

        weight = IntegerPintFormField(
            default_unit="gram",
            widget=PintFieldWidget(
                attrs={"class": "custom-input", "data-test": "test-value", "min": "0", "max": "1000"}
            ),
        )

    return CustomWidgetForm


class TestPintFieldWidget:
    """Test cases for PintFieldWidget."""

    def test_creates_correct_widget_for_modelform(self, haybale_form):
        """Test that the correct widget is created for model form fields."""
        form = haybale_form()
        assert isinstance(form.fields["weight_int"], IntegerPintFormField)
        assert isinstance(form.fields["weight_int"].widget, PintFieldWidget)
        assert isinstance(form.fields["weight_bigint"], IntegerPintFormField)
        assert isinstance(form.fields["weight_bigint"].widget, PintFieldWidget)
        assert isinstance(form.fields["weight_decimal"], DecimalPintFormField)
        assert isinstance(form.fields["weight_decimal"].widget, PintFieldWidget)

    @pytest.mark.parametrize(
        "initial_data",
        [
            {"weight_int": ureg.Quantity(100 * ureg.gram)},
            {"weight_int": ureg.Quantity(200 * ureg.gram)},
        ],
    )
    def test_displays_initial_data(self, haybale_form, initial_data):
        """Test initial data display in form."""
        form = haybale_form(initial=initial_data)
        assert isinstance(form.fields["weight_int"].initial, ureg.Quantity)
        assert form.fields["weight_int"].initial.magnitude == initial_data["weight_int"].magnitude
        assert form.fields["weight_int"].initial.units == "gram"

    def test_clean_yields_quantity(self, haybale_form):
        """Test that cleaned data produces Quantity objects."""
        form = haybale_form(
            data={
                "weight_int_0": 100,
                "weight_int_1": "gram",
                "weight_bigint_0": 100,
                "weight_bigint_1": "gram",
                "weight_decimal_0": 100,
                "weight_decimal_1": "gram",
                "name": "test",
            }
        )
        assert form.is_valid()
        assert isinstance(form.cleaned_data["weight_int"], ureg.Quantity)
        assert isinstance(form.cleaned_data["weight_bigint"], ureg.Quantity)
        assert isinstance(form.cleaned_data["weight_decimal"], ureg.Quantity)

    @pytest.mark.parametrize(
        "field_data",
        [
            {"field": "weight_int", "value": 1, "unit": "kilogram", "expected_magnitude": 1},
            {"field": "weight_bigint", "value": 1, "unit": "ounce", "expected_magnitude": 1},
            {"field": "weight_decimal", "value": 1.0, "unit": "pound", "expected_magnitude": Decimal("1.0")},
        ],
    )
    def test_clean_yields_correct_units(self, haybale_form, field_data):
        """Test that cleaned data has correct units and magnitudes."""
        form_data = {
            f"{field_data['field']}_0": field_data["value"],
            f"{field_data['field']}_1": field_data["unit"],
            "name": "test",
        }
        form = haybale_form(data=form_data)
        assert form.is_valid()
        assert str(form.cleaned_data[field_data["field"]].units) == field_data["unit"]
        assert form.cleaned_data[field_data["field"]].magnitude == field_data["expected_magnitude"]

    def test_clean_fails_with_incorrect_units(self, haybale_form):
        """Test form validation fails with incorrect units."""
        form = haybale_form(
            data={"weight_int_0": 1, "weight_int_1": "onuce", "name": "test"}  # intentional misspelling
        )
        assert not form.is_valid()

    @pytest.mark.parametrize(
        "input_data,expected_output",
        [
            ({"weight_int_0": 10.3, "weight_int_1": "gram"}, 10),
            ({"weight_bigint_0": 10.3, "weight_bigint_1": "gram"}, 10),
            ({"weight_decimal_0": 10.3, "weight_decimal_1": "gram"}, Decimal("10.3")),
        ],
    )
    def test_precision_handling(self, haybale_form, input_data, expected_output):
        """Test precision handling for different field types."""
        input_data["name"] = "test"
        form = haybale_form(data=input_data)
        assert form.is_valid()
        field_name = list(input_data.keys())[0].split("_")[0]
        assert form.cleaned_data[field_name].magnitude == expected_output


class TestFormValidation:
    """Test form validation scenarios."""

    def test_quantityfield_can_be_null(self, nullable_weight_form):
        """Test that QuantityField can be null when allowed."""
        form = nullable_weight_form(
            data={
                "weight_int_0": None,
                "weight_int_1": None,
                "weight_decimal_0": None,
                "weight_decimal_1": None,
            }
        )
        assert form.is_valid()

    def test_validate_units(self, unit_choices_form):
        """Test unit validation."""
        form = unit_choices_form(
            data={
                "distance_0": 100,
                "distance_1": "ounce",
            }
        )
        assert not form.is_valid()

    @pytest.mark.parametrize(
        "field_class,unit_choices,error",
        [
            (IntegerPintFormField, ["gunzu"], UndefinedUnitError),
            (DecimalPintFormField, ["meter", "ounces"], DimensionalityError),
        ],
    )
    def test_unit_choice_validation(self, field_class, unit_choices, error):
        """Test validation of unit choices."""
        with pytest.raises(error):
            if field_class == DecimalPintFormField:
                field_class(default_unit="gram", unit_choices=unit_choices, max_digits=10, decimal_places=2)
            else:
                field_class(default_unit="gram", unit_choices=unit_choices)


class TestTabledWidget:
    """Test the TabledPintFieldWidget."""

    def test_create_table(self):
        """Test table creation with valid inputs."""
        widget = TabledPintFieldWidget(default_unit="kilogram", unit_choices=["gram", "kilogram", "ounce"])
        value = ureg.Quantity(100, ureg.kilogram)
        table = widget.create_table(value)
        assert len(table) == 2
        assert round(table[0].magnitude) == 100000
        assert table[0].units == ureg.Quantity(100000, ureg.gram).units

    def test_create_table_invalid_input(self):
        """Test table creation with invalid input."""
        widget = TabledPintFieldWidget(default_unit="kilogram", unit_choices=["gram", "kilogram", "ounce"])
        with pytest.raises(ImproperlyConfigured):
            widget.create_table("invalid_value")

    def test_get_context(self):
        """Test context generation for widget."""
        widget = TabledPintFieldWidget(default_unit="gram", unit_choices=["gram", "kilogram", "ounce"])
        value = ureg.Quantity(100, ureg.gram)
        context = widget.get_context("weight", value, {})
        assert "values_list" in context
        assert "floatformat" in context
        assert "table_class" in context
        assert "td_class" in context


class TestEdgeCases:
    """Test edge cases for PintField widgets."""

    @pytest.mark.parametrize(
        "value,unit,expected_magnitude",
        [
            (1e-10, "gram", 0),  # Very small number should round to 0 for IntegerPintField
            (1e10, "gram", 1e10),  # Very large number
            (0, "gram", 0),  # Zero
            (-100, "gram", -100),  # Negative number
            (2147483647, "gram", 2147483647),  # Max int
            (-2147483648, "gram", -2147483648),  # Min int
        ],
    )
    def test_integer_field_edge_values(self, edge_case_form, value, unit, expected_magnitude):
        """Test handling of edge case values in IntegerPintField."""
        form = edge_case_form(
            data={
                "weight_0": value,
                "weight_1": unit,
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["weight"].magnitude == expected_magnitude
        assert str(form.cleaned_data["weight"].units) == unit

    @pytest.mark.parametrize(
        "value,unit",
        [
            ("1e-10", "gram"),  # Very small decimal
            ("1e10", "gram"),  # Very large decimal
            ("0.0000000001", "gram"),  # Many decimal places
            ("-0.0000000001", "gram"),  # Negative with many decimal places
            ("999999999999.9999999999", "gram"),  # Large with many decimal places
        ],
    )
    def test_decimal_field_precision(self, edge_case_form, value, unit):
        """Test precision handling in DecimalPintField."""
        form = edge_case_form(
            data={
                "precise_weight_0": value,
                "precise_weight_1": unit,
            }
        )
        assert form.is_valid()
        assert isinstance(form.cleaned_data["precise_weight"].magnitude, Decimal)
        assert Decimal(value) == form.cleaned_data["precise_weight"].magnitude

    @pytest.mark.parametrize(
        "value",
        [
            "inf",  # Infinity
            "-inf",  # Negative infinity
            "nan",  # Not a number
            "1/2",  # Fraction
            "1.2.3",  # Invalid number format
            "e",  # Invalid exponential
            "0x123",  # Hexadecimal
        ],
    )
    def test_invalid_number_formats(self, edge_case_form, value):
        """Test handling of invalid number formats."""
        form = edge_case_form(
            data={
                "weight_0": value,
                "weight_1": "gram",
            }
        )
        assert not form.is_valid()
        assert "weight" in form.errors


class TestWidgetScenarios:
    """Test various widget scenarios and configurations."""

    @pytest.mark.parametrize(
        "widget_attrs",
        [
            {"class": "custom-input"},
            {"min": "0", "max": "100", "step": "0.1"},
            {"required": True, "placeholder": "Enter weight"},
            {"data-test": "test-value", "aria-label": "Weight input"},
        ],
    )
    def test_custom_widget_attributes(self, widget_attrs):
        """Test widget with custom HTML attributes."""
        widget = PintFieldWidget(attrs=widget_attrs, default_unit="gram", unit_choices=["gram", "kilogram"])
        rendered = widget.render("weight", None, {})
        for attr, value in widget_attrs.items():
            assert attr in rendered
            assert str(value) in rendered

    def test_widget_with_custom_step(self, custom_widget_form):
        """Test widget with custom step attribute."""
        form = custom_widget_form()
        rendered = str(form)
        assert 'step="any"' in rendered
        assert 'class="custom-input"' in rendered
        assert 'data-test="test-value"' in rendered

    @pytest.mark.parametrize(
        "unit_choices,default_unit,expected_first",
        [
            (["gram", "kilogram"], "gram", "gram"),
            (["kilogram", "gram"], "gram", "kilogram"),
            (["pound", "ounce"], "pound", "pound"),
        ],
    )
    def test_unit_choices_ordering(self, unit_choices, default_unit, expected_first):
        """Test unit choices ordering in widget."""
        widget = PintFieldWidget(default_unit=default_unit, unit_choices=unit_choices)
        assert widget.choices[0][0] == str(ureg(expected_first).units)

    def test_tabled_widget_with_custom_formatting(self):
        """Test TabledPintFieldWidget with custom formatting options."""
        widget = TabledPintFieldWidget(
            default_unit="gram",
            unit_choices=["gram", "kilogram", "ounce"],
            floatformat=2,
            table_class="custom-table",
            td_class="custom-cell",
        )
        context = widget.get_context("weight", ureg.Quantity(100, "gram"), {})
        assert context["floatformat"] == 2
        assert context["table_class"] == "custom-table"
        assert context["td_class"] == "custom-cell"

    @pytest.mark.django_db
    def test_widget_bound_field_rendering(self, custom_widget_form):
        """Test rendering of bound field with widget."""
        form = custom_widget_form(data={"weight_0": "100", "weight_1": "gram"})
        assert form.is_valid()
        rendered = str(form["weight"])
        assert 'value="100"' in rendered
        assert "selected>gram</option>" in rendered

    @pytest.mark.parametrize(
        "value,unit_from,unit_to,expected_magnitude",
        [
            (1000, "milligram", "gram", 1),
            (1, "kilogram", "gram", 1000),
            (1, "pound", "gram", 453.59237),
        ],
    )
    def test_widget_unit_conversion_display(self, value, unit_from, unit_to, expected_magnitude):
        """Test display of converted units in TabledPintFieldWidget."""
        widget = TabledPintFieldWidget(default_unit=unit_from, unit_choices=[unit_from, unit_to])
        quantity = ureg.Quantity(value, unit_from)
        table = widget.create_table(quantity)
        converted = [v for v in table if str(v.units) == unit_to][0]
        assert pytest.approx(converted.magnitude, rel=1e-5) == expected_magnitude

    def test_widget_handling_none_value(self):
        """Test widget handling of None values."""
        widget = PintFieldWidget(default_unit="gram")
        result = widget.decompress(None)
        assert result == [None, "gram"]

        widget = TabledPintFieldWidget(default_unit="gram")
        table = widget.create_table(None)
        assert all(v.magnitude == 0 for v in table)


class TestWidgetValidation:
    """Test widget validation scenarios."""

    @pytest.mark.parametrize(
        "input_value,expected_error",
        [
            ("abc", "Enter a number"),
            ("12.34.56", "Enter a number"),
            ("", "This field is required"),
            (None, "This field is required"),
        ],
    )
    def test_number_input_validation(self, haybale_form, input_value, expected_error):
        """Test validation of number input."""
        form = haybale_form(data={"weight_int_0": input_value, "weight_int_1": "gram", "name": "test"})
        assert not form.is_valid()
        assert any(expected_error in error for error in form.errors["weight_int"])

    @pytest.mark.parametrize(
        "unit_value",
        [
            "",  # Empty unit
            "invalid_unit",  # Invalid unit name
            None,  # None value
            "123",  # Number instead of unit
        ],
    )
    def test_unit_select_validation(self, haybale_form, unit_value):
        """Test validation of unit selection."""
        form = haybale_form(data={"weight_int_0": "100", "weight_int_1": unit_value, "name": "test"})
        assert not form.is_valid()
        assert "weight_int" in form.errors
