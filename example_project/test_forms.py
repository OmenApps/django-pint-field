"""Test cases for form fields."""

from decimal import Decimal
from decimal import getcontext

import pytest
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from django_pint_field.forms import BasePintFormField
from django_pint_field.forms import DecimalPintFormField
from django_pint_field.forms import IntegerPintFormField
from django_pint_field.units import ureg
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.widgets import TabledPintFieldWidget
from example_project.example.forms import DefaultFormDecimal
from example_project.example.forms import DefaultFormInteger
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


class TestBasePintFormField:
    """Test the base form field functionality."""

    def test_init_with_invalid_default_unit(self):
        """Test initialization with invalid default unit raises error."""
        from pint.errors import UndefinedUnitError

        with pytest.raises(UndefinedUnitError):
            BasePintFormField(default_unit="invalid_unit")

    def test_init_with_invalid_unit_choices(self):
        """Test initialization with incompatible unit choices raises error."""
        with pytest.raises(ValidationError):
            BasePintFormField(default_unit="gram", unit_choices=["meter", "gram"])

    def test_widget_initialization(self):
        """Test widget is properly initialized."""
        field = BasePintFormField(default_unit="gram")
        assert isinstance(field.widget, PintFieldWidget)
        assert field.widget.default_unit == "gram"
        assert ("gram", "gram") in field.widget.choices

    @pytest.mark.parametrize(
        "value,expected_result",
        [
            (Quantity(100, "gram"), [100, "gram"]),
            ([50, "gram"], [50, "gram"]),
            (None, [None, "gram"]),
        ],
    )
    def test_prepare_value(self, value, expected_result):
        """Test prepare_value method with different input types."""
        field = BasePintFormField(default_unit="gram")
        result = field.prepare_value(value)
        assert result == expected_result

    @pytest.mark.parametrize(
        "required,value,expected_valid",
        [
            (True, ["", "gram"], False),  # Required field, empty value
            (False, ["", "gram"], True),  # Optional field, empty value
            (False, None, True),  # Optional field, None value
            (True, None, False),  # Required field, None value
        ],
    )
    def test_required_validation(self, required, value, expected_valid):
        """Test required field validation."""
        field = BasePintFormField(default_unit="gram", required=required)
        if value is not None:
            if expected_valid:
                form_value = field.clean(value)
                assert form_value is None
            else:
                with pytest.raises(ValidationError):
                    field.clean(value)

    def test_field_renders_with_standard_widget(self):
        """Test that field renders correctly with standard PintFieldWidget."""
        field = BasePintFormField(default_unit="gram")
        html = field.widget.render("weight", None, {"id": "id_weight"})
        assert 'id="id_weight_0"' in html
        assert 'id="id_weight_1"' in html
        assert 'name="weight_0"' in html
        assert 'name="weight_1"' in html

    def test_field_renders_with_tabled_widget(self):
        """Test that field renders correctly with TabledPintFieldWidget."""
        field = BasePintFormField(
            default_unit="gram",
            widget=TabledPintFieldWidget(
                default_unit="gram", unit_choices=[["gram", "gram"], ["kilogram", "kilogram"]]
            ),
        )

        # Test empty value rendering - should only show inputs
        html = field.widget.render("weight", None, {"id": "id_weight"})
        assert 'name="weight_0"' in html
        assert 'name="weight_1"' in html

        # Test with value - should show table
        value = Quantity(100, "gram")
        html = field.widget.render("weight", value, {"id": "id_weight"})
        assert 'name="weight_0"' in html
        assert 'name="weight_1"' in html
        assert "<table" in html
        assert "<th" in html


@pytest.mark.django_db
class TestIntegerPintFormField:
    """Test the integer form field functionality."""

    @pytest.fixture
    def integer_form(self):
        """Create a form instance for testing."""

        class TestForm(ModelForm):
            """Test form with IntegerPintFormField."""

            weight = IntegerPintFormField(default_unit="gram", unit_choices=["gram", "kilogram", "ounce"])

            class Meta:
                """Meta class for TestForm."""

                model = IntegerPintFieldSaveModel
                fields = ["weight"]

        return TestForm

    def test_valid_integer_input(self, integer_form):
        """Test valid integer input is properly handled."""
        form = integer_form(data={"weight_0": "100", "weight_1": "gram"})
        assert form.is_valid()
        assert isinstance(form.cleaned_data["weight"], Quantity)
        assert form.cleaned_data["weight"].magnitude == 100
        assert str(form.cleaned_data["weight"].units) == "gram"

    def test_float_input_converts_to_integer(self, integer_form):
        """Test float input is properly converted to integer."""
        form = integer_form(data={"weight_0": "100.7", "weight_1": "gram"})
        assert form.is_valid()
        assert isinstance(form.cleaned_data["weight"].magnitude, int)
        assert form.cleaned_data["weight"].magnitude == 100

    def test_unit_conversion(self, integer_form):
        """Test unit conversion is properly handled."""
        form = integer_form(data={"weight_0": "1", "weight_1": "kilogram"})
        assert form.is_valid()
        assert form.cleaned_data["weight"].to("gram").magnitude == 1000

    def test_default_form_integer(self):
        """Test the DefaultFormInteger form."""
        form = DefaultFormInteger(data={"name": "test", "weight_0": "100", "weight_1": "gram"})
        assert form.is_valid()
        instance = form.save()
        assert instance.weight.magnitude == 100
        assert str(instance.weight.units) == "gram"


@pytest.mark.django_db
class TestDecimalPintFormField:
    """Test the decimal form field functionality."""

    @pytest.fixture
    def decimal_form(self):
        """Create a form instance for testing."""

        class TestForm(ModelForm):
            """Test form with DecimalPintFormField."""

            weight = DecimalPintFormField(
                default_unit="gram", unit_choices=["gram", "kilogram", "ounce"], display_decimal_places=2
            )

            class Meta:
                """Meta class for TestForm."""

                model = DecimalPintFieldSaveModel
                fields = ["weight"]

        return TestForm

    def test_valid_decimal_input(self, decimal_form):
        """Test valid decimal input is properly handled."""
        form = decimal_form(data={"weight_0": "100.55", "weight_1": "gram"})
        assert form.is_valid()
        assert isinstance(form.cleaned_data["weight"], Quantity)
        assert form.cleaned_data["weight"].magnitude == Decimal("100.55")
        assert str(form.cleaned_data["weight"].units) == "gram"

    def test_decimal_adds_missing_decimal_places(self, decimal_form):
        """Test that missing decimal places are added."""
        form = decimal_form(data={"weight_0": "100", "weight_1": "gram"})
        assert form.is_valid()
        assert form.cleaned_data["weight"].magnitude == Decimal("100")

    def test_default_form_decimal(self):
        """Test the DefaultFormDecimal form."""
        form = DefaultFormDecimal(data={"name": "test", "weight_0": "100.55", "weight_1": "gram"})
        assert form.is_valid()
        instance = form.save()
        assert instance.weight.magnitude == Decimal("100.55")
        assert str(instance.weight.units) == "gram"

    @pytest.mark.parametrize(
        "invalid_value",
        [
            {"weight_0": "abc", "weight_1": "gram"},  # Non-numeric value
            {"weight_0": "", "weight_1": "gram"},  # Empty value
            {"weight_0": "100.55", "weight_1": ""},  # Missing unit
            {"weight_0": "100.55", "weight_1": "meter"},  # Incompatible unit
        ],
    )
    def test_invalid_input(self, decimal_form, invalid_value):
        """Test various invalid inputs."""
        form = decimal_form(data=invalid_value)
        assert not form.is_valid()

    def test_decimal_precision_validation(self):
        """Test that values exceeding decimal precision are rejected."""
        field = DecimalPintFormField(default_unit="gram", display_decimal_places=2)
        # Try to create a value that exceeds the current decimal precision
        with pytest.raises(ValidationError):
            value = ["9" * (getcontext().prec + 1), "gram"]
            field.clean(value)

    def test_custom_display_precision(self):
        """Test custom display_decimal_places setting."""
        field = DecimalPintFormField(default_unit="gram", display_decimal_places=1)
        assert field.display_decimal_places == 1
        assert field.widget.widgets[0].attrs["step"] == "0.1"

    def test_display_precision_validation(self):
        """Test validation of display_decimal_places."""
        with pytest.raises(ValidationError, match="display_decimal_places must be a positive integer or zero"):
            DecimalPintFormField(default_unit="gram", display_decimal_places=-1)

    @pytest.mark.parametrize(
        "value,display_places,expected_display",
        [
            (Decimal("123.456"), 2, "123.46"),  # Round up
            (Decimal("123.454"), 2, "123.45"),  # Round down
            (Decimal("123.000"), 1, "123.0"),  # Trailing zeros
            (Decimal("123.456"), 0, "123"),  # No decimals
        ],
    )
    def test_value_display_formatting(self, value, display_places, expected_display):
        """Test that values are formatted correctly for display."""
        field = DecimalPintFormField(default_unit="gram", display_decimal_places=display_places)
        quantity = ureg.Quantity(value, "gram")
        formatted = field.prepare_value(quantity)
        assert str(formatted[0]) == expected_display
        assert formatted[1] == "gram"

    def test_precision_preservation(self):
        """Test that full precision is preserved when saving, regardless of display setting."""
        field = DecimalPintFormField(default_unit="gram", display_decimal_places=1)

        # Create a value with full precision
        value = ["123.456", "gram"]

        # The value should display with reduced precision
        display_value = field.prepare_value(field.to_python(value))
        assert str(display_value[0]) == "123.5"

        # But the full precision should be preserved in the Python object
        python_value = field.to_python(value)
        assert str(python_value.magnitude) == "123.456"


@pytest.mark.django_db
class TestFormFieldEdgeCases:
    """Test edge cases and error handling in form fields."""

    def test_default_unit_none_raises_error(self):
        """Test that missing default_unit raises ValidationError."""
        with pytest.raises(ValidationError, match="requires a default_unit"):
            IntegerPintFormField(default_unit=None)

    def test_default_unit_invalid_format_raises_error(self):
        """Test that invalid default_unit format raises ValidationError."""
        with pytest.raises(ValidationError, match="must be either a string or a 2-tuple"):
            IntegerPintFormField(default_unit=["gram", "kilogram", "extra"])

    def test_prepare_value_with_three_element_tuple(self):
        """Test prepare_value with 3-element tuple (comparator, magnitude, units)."""
        field = IntegerPintFormField(default_unit="gram")
        # Simulate database composite type format
        value = (Decimal("100"), 100, "gram")
        result = field.prepare_value(value)
        assert result == [100, "gram"]

    def test_prepare_value_with_invalid_three_element_tuple(self):
        """Test prepare_value with invalid 3-element tuple falls back gracefully."""
        field = IntegerPintFormField(default_unit="gram")
        # Invalid tuple that can't be unpacked properly
        value = (None, None, None)
        result = field.prepare_value(value)
        # When all values are None, returns [None, None]
        assert result == [None, None]

    def test_prepare_value_with_string_composite_format(self):
        """Test prepare_value with string in PostgreSQL composite format."""
        field = DecimalPintFormField(default_unit="gram")
        # Simulate string from database: "(comparator,magnitude,units)"
        value = "(100.0, 100, gram)"
        result = field.prepare_value(value)
        assert result[0] == Decimal("100")
        assert result[1] == "gram"

    def test_prepare_value_with_invalid_string_format(self):
        """Test prepare_value with invalid string format falls back to default."""
        field = IntegerPintFormField(default_unit="gram")
        value = "invalid_format_string"
        result = field.prepare_value(value)
        assert result[1] == "gram"  # Should use default unit

    def test_decimal_field_with_deprecated_max_digits_param(self):
        """Test DecimalPintFormField with deprecated max_digits parameter."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = DecimalPintFormField(default_unit="gram", max_digits=10)
            # Should still work but may warn
            assert field is not None

    def test_decimal_field_with_deprecated_decimal_places_param(self):
        """Test DecimalPintFormField with deprecated decimal_places parameter."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = DecimalPintFormField(default_unit="gram", decimal_places=2)
            # Should still work but may warn
            assert field is not None

    def test_to_python_with_none(self):
        """Test to_python with None value."""
        field = IntegerPintFormField(default_unit="gram")
        result = field.to_python(None)
        assert result is None

    def test_to_python_with_empty_string(self):
        """Test to_python with empty string."""
        field = IntegerPintFormField(default_unit="gram", required=False)
        result = field.to_python("")
        assert result is None

    def test_to_python_with_quantity_raises_error(self):
        """Test to_python with Quantity object raises ValidationError."""
        field = IntegerPintFormField(default_unit="gram")
        quantity = ureg.Quantity(100, "gram")
        # Form fields don't accept Quantity objects directly
        with pytest.raises(ValidationError, match="Value type.*is invalid"):
            field.to_python(quantity)
