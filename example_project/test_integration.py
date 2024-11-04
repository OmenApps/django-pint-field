"""Test the integration of the widget with the model."""

from decimal import Decimal

import pytest
from django import forms

from django_pint_field.units import ureg
from example_project.example.forms import DefaultFormBigInteger
from example_project.example.forms import DefaultFormDecimal
from example_project.example.forms import DefaultFormInteger
from example_project.example.forms import DjangoPintFieldWidgetComparisonAdminForm


@pytest.fixture
def default_form_data():
    """Base form data used across tests."""
    return {
        "name": "testing",
        "weight_0": "10.3",
        "weight_1": "gram",
    }


@pytest.fixture
def default_decimal_form_data(default_form_data):
    """Form data for decimal tests."""
    data = default_form_data.copy()
    data["weight_0"] = "10"
    return data


@pytest.fixture
def default_int_form_data(default_form_data):
    """Form data for integer tests."""
    data = default_form_data.copy()
    data["weight_0"] = "10"
    return data


@pytest.fixture
def form_data_variants():
    """Provide various valid form data combinations."""
    return [
        {"weight_0": "10", "weight_1": "gram", "expected": 10},
        {"weight_0": "0.1", "weight_1": "kilogram", "expected": 100},
        {"weight_0": "1000", "weight_1": "milligram", "expected": 1},
        {"weight_0": "1", "weight_1": "pound", "expected": 453.59237},
    ]


@pytest.fixture
def invalid_form_data():
    """Provide various invalid form data combinations."""
    return [
        {"weight_0": "abc", "weight_1": "gram", "error": "Enter a number"},
        {"weight_0": "-1", "weight_1": "invalid", "error": "Invalid unit"},
        {"weight_0": "", "weight_1": "gram", "error": "required"},
        {"weight_0": "1e99999", "weight_1": "gram", "error": "too large"},
    ]


class TestFormIntegrationBase:
    """Base class for testing the integration of the widget with the model."""

    default_form = DefaultFormInteger
    input_str = "10.3"
    output_magnitude = 10.3

    def check_form_and_saved_object(self, form: forms.ModelForm, has_magnitude: bool):
        """Check the form and the saved object."""
        assert form.is_valid(), f"Form errors: {form.errors}"

        if has_magnitude:
            assert pytest.approx(form.cleaned_data["weight"].magnitude) == self.output_magnitude
            assert str(form.cleaned_data["weight"].units) == "gram"
        else:
            assert pytest.approx(form.cleaned_data["weight"]) == self.output_magnitude

        form.save()
        obj = form.Meta.model.objects.last()
        assert str(obj.weight.units) == "gram"

        if isinstance(self.output_magnitude, float):
            assert pytest.approx(obj.weight.magnitude) == self.output_magnitude
        else:
            assert obj.weight.magnitude == self.output_magnitude

        assert isinstance(obj.weight.magnitude, type(self.output_magnitude))

    @pytest.mark.django_db
    def test_widget_valid_inputs_with_units(self, default_form_data):
        """Ensure valid inputs and units are saved correctly."""
        form_data = default_form_data.copy()
        form_data["weight_0"] = self.input_str

        form = self.default_form(data=form_data)
        self.check_form_and_saved_object(form, True)

    @pytest.mark.django_db
    def test_valid_input_combinations(self, form_data_variants):
        """Test various valid input combinations."""
        for variant in form_data_variants:
            form = self.default_form(
                data={"name": "test", "weight_0": variant["weight_0"], "weight_1": variant["weight_1"]}
            )
            assert form.is_valid(), f"Form errors: {form.errors}"
            saved_obj = form.save()
            assert saved_obj.weight.to("gram").magnitude == pytest.approx(variant["expected"])

    @pytest.mark.django_db
    def test_invalid_input_combinations(self, invalid_form_data):
        """Test various invalid input combinations."""
        for invalid_data in invalid_form_data:
            form = self.default_form(
                data={"name": "test", "weight_0": invalid_data["weight_0"], "weight_1": invalid_data["weight_1"]}
            )
            assert not form.is_valid()
            assert any(invalid_data["error"] in error for error in form.errors.get("weight", []))

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "unit_conversion",
        [
            ("gram", "kilogram", 0.001),
            ("kilogram", "gram", 1000),
            ("pound", "gram", 453.59237),
            ("ounce", "gram", 28.3495231),
        ],
    )
    def test_unit_conversions(self, unit_conversion):
        """Test unit conversions are handled correctly."""
        from_unit, to_unit, factor = unit_conversion
        form = self.default_form(data={"name": "test", "weight_0": "1", "weight_1": from_unit})
        assert form.is_valid()
        obj = form.save()
        converted = obj.weight.to(to_unit)
        assert converted.magnitude == pytest.approx(factor)


class TestDecimalFieldWidgetIntegration(TestFormIntegrationBase):
    """Test the DecimalField widget integration."""

    default_form = DefaultFormDecimal
    input_str = "10"
    output_magnitude = Decimal("10")

    @pytest.mark.django_db
    def test_widget_valid_inputs_with_units(self, default_decimal_form_data):
        """Ensure valid decimal inputs and units are saved correctly."""
        form = self.default_form(data=default_decimal_form_data)
        self.check_form_and_saved_object(form, True)


class TestIntFieldWidgetIntegration(TestFormIntegrationBase):
    """Test the IntegerField widget integration."""

    input_str = "10"
    output_magnitude = 10
    default_form = DefaultFormInteger

    @pytest.mark.django_db
    def test_widget_valid_inputs_with_units(self, default_int_form_data):
        """Ensure valid integer inputs and units are saved correctly."""
        form = self.default_form(data=default_int_form_data)
        self.check_form_and_saved_object(form, True)


class TestBigIntFieldWidgetIntegration(TestFormIntegrationBase):
    """Test the BigIntegerField widget integration."""

    input_str = "10"
    output_magnitude = 10
    default_form = DefaultFormBigInteger

    @pytest.mark.django_db
    def test_widget_valid_inputs_with_units(self, default_int_form_data):
        """Ensure valid big integer inputs and units are saved correctly."""
        form = self.default_form(data=default_int_form_data)
        self.check_form_and_saved_object(form, True)


class TestFormRendering:
    """Test form rendering scenarios."""

    def test_initial_value_rendering(self):
        """Test rendering with initial values."""
        initial = {"name": "test", "weight": ureg.Quantity(100, "gram")}
        form = DefaultFormInteger(initial=initial)
        html = str(form)
        assert 'value="100"' in html
        assert "selected>gram</option>" in html

    @pytest.mark.parametrize(
        "form_class,expected_step",
        [
            (DefaultFormInteger, "1"),
            (DefaultFormBigInteger, "1"),
            (DefaultFormDecimal, "0.01"),
        ],
    )
    def test_step_attribute_rendering(self, form_class, expected_step):
        """Test step attribute rendering for different field types."""
        form = form_class()
        html = str(form)
        assert f'step="{expected_step}"' in html

    def test_disabled_field_rendering(self):
        """Test rendering of disabled fields."""

        class DisabledForm(DefaultFormInteger):
            """Form with disabled weight field."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["weight"].disabled = True

        form = DisabledForm()
        html = str(form)
        assert "disabled" in html


class TestTabledWidgetIntegration:
    """Test integration of TabledPintFieldWidget."""

    def test_tabled_widget_rendering(self):
        """Test rendering of tabled widget."""
        form = DjangoPintFieldWidgetComparisonAdminForm()
        html = str(form)
        assert 'class="p-5 m-5"' in html  # Default table class
        assert 'class="text-end"' in html  # Default td class

    @pytest.mark.django_db
    def test_tabled_widget_data_saving(self):
        """Test saving data from tabled widget."""
        form = DjangoPintFieldWidgetComparisonAdminForm(
            data={
                "name": "test",
                "tabled_weight_int_0": "100",
                "tabled_weight_int_1": "gram",
                "tabled_weight_bigint_0": "100",
                "tabled_weight_bigint_1": "gram",
                "tabled_weight_decimal_0": "100.00",
                "tabled_weight_decimal_1": "gram",
            }
        )
        assert form.is_valid()
        obj = form.save()
        assert obj.tabled_weight_int.magnitude == 100
        assert obj.tabled_weight_bigint.magnitude == 100
        assert obj.tabled_weight_decimal.magnitude == Decimal("100.00")

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "field_name,value,expected_error",
        [
            ("tabled_weight_int", "abc", "Enter a number"),
            ("tabled_weight_bigint", "1e99", "number too large"),
            ("tabled_weight_decimal", "100.999", "Ensure that there are no more"),
        ],
    )
    def test_tabled_widget_validation(self, field_name, value, expected_error):
        """Test validation in tabled widget."""
        form_data = {
            "name": "test",
            f"{field_name}_0": value,
            f"{field_name}_1": "gram",
        }
        form = DjangoPintFieldWidgetComparisonAdminForm(data=form_data)
        assert not form.is_valid()
        assert any(expected_error in error for error in form.errors[field_name])


class TestEdgeCaseIntegration:
    """Test edge cases in form integration."""

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "value,unit,expected_error",
        [
            ("1e-20", "gram", "Value too small"),
            ("1e20", "gram", "Value too large"),
            ("0.1234567890", "gram", "decimal places"),
            ("-0", "gram", None),  # Should be valid
            ("0.0", "gram", None),  # Should be valid
        ],
    )
    def test_decimal_field_limits(self, value, unit, expected_error):
        """Test decimal field limits."""
        form = DefaultFormDecimal(
            data={
                "name": "test",
                "weight_0": value,
                "weight_1": unit,
            }
        )
        if expected_error:
            assert not form.is_valid()
            assert any(expected_error in error for error in form.errors["weight"])
        else:
            assert form.is_valid()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "form_class,test_data",
        [
            (DefaultFormInteger, {"max": 2147483647, "min": -2147483648}),
            (DefaultFormBigInteger, {"max": 9223372036854775807, "min": -9223372036854775808}),
        ],
    )
    def test_integer_field_bounds(self, form_class, test_data):
        """Test integer field bounds."""
        for value in [test_data["max"], test_data["min"]]:
            form = form_class(
                data={
                    "name": "test",
                    "weight_0": str(value),
                    "weight_1": "gram",
                }
            )
            assert form.is_valid()
