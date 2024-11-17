"""Test cases for form fields."""

from decimal import Decimal

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
        with pytest.raises(ValidationError):
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
        assert "gram" in field.widget.unit_choices

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

    def test_disabled_field(self):
        """Test disabled field behavior."""
        field = BasePintFormField(default_unit="gram", disabled=True)
        assert field.disabled
        assert field.widget.attrs.get("disabled") is True

    @pytest.mark.parametrize(
        "initial,expected",
        [
            (Quantity(100, "gram"), [100, "gram"]),
            (None, [None, "gram"]),
            (Quantity(1, "kilogram"), [1, "kilogram"]),
        ],
    )
    def test_initial_value(self, initial, expected):
        """Test initial value handling."""
        field = BasePintFormField(default_unit="gram", initial=initial)
        assert field.prepare_value(field.initial) == expected

    def test_help_text(self):
        """Test help text is properly set."""
        help_text = "Enter weight in grams"
        field = BasePintFormField(default_unit="gram", help_text=help_text)
        assert field.help_text == help_text

    def test_localized_field(self):
        """Test localized field behavior."""
        field = BasePintFormField(default_unit="gram", localize=True)
        assert field.localize
        assert field.widget.is_localized

    def test_base_field_template_name(self):
        """Test that BasePintFormField has correct template_name."""
        field = BasePintFormField(default_unit="gram")
        assert field.template_name == "django/forms/widgets/input.html"

    def test_base_field_with_tabled_widget_template(self):
        """Test template_name behavior with TabledPintFieldWidget."""
        field = BasePintFormField(default_unit="gram", widget=TabledPintFieldWidget(default_unit="gram"))
        assert field.template_name == "django/forms/widgets/input.html"
        assert field.widget.template_name == "django_pint_field/tabled_django_pint_field_widget.html"

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
            default_unit="gram", widget=TabledPintFieldWidget(default_unit="gram", unit_choices=["gram", "kilogram"])
        )
        html = field.widget.render("weight", None, {"id": "id_weight"})
        # Instead of checking for specific IDs (which may vary), check for essential elements
        assert 'name="weight_0"' in html
        assert 'name="weight_1"' in html
        assert '<table class="p-5 m-5">' in html
        assert '<td class="text-end">' in html
        assert "<th>Unit</th>" in html
        assert "<th>Value</th>" in html

    def test_field_media_requirements(self):
        """Test that field properly declares its media requirements."""
        field = BasePintFormField(default_unit="gram")
        assert hasattr(field.widget, "media")

        field_with_tabled = BasePintFormField(default_unit="gram", widget=TabledPintFieldWidget(default_unit="gram"))
        assert hasattr(field_with_tabled.widget, "media")

    def test_widget_class_attributes_in_rendering(self):
        """Test that widget class attributes are properly included in rendering."""
        field = BasePintFormField(
            default_unit="gram", widget=PintFieldWidget(default_unit="gram", attrs={"class": "custom-input"})
        )
        html = field.widget.render("weight", None, {})
        assert 'class="custom-input"' in html


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

    @pytest.mark.parametrize(
        "invalid_value",
        [
            {"weight_0": "abc", "weight_1": "gram"},  # Non-numeric value
            {"weight_0": "", "weight_1": "gram"},  # Empty value
            {"weight_0": "100", "weight_1": ""},  # Missing unit
            {"weight_0": "100", "weight_1": "invalid_unit"},  # Invalid unit
        ],
    )
    def test_invalid_input(self, integer_form, invalid_value):
        """Test various invalid inputs."""
        form = integer_form(data=invalid_value)
        assert not form.is_valid()

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

    @pytest.mark.parametrize(
        "value,unit,expected_error",
        [
            (2**31, "gram", "is less than or equal to"),  # Max int + 1
            (-(2**31) - 1, "gram", "is greater than or equal to"),  # Min int - 1
            (float("inf"), "gram", "is less than or equal to"),  # Infinity
            (float("-inf"), "gram", "is greater than or equal to"),  # Negative infinity
        ],
    )
    def test_integer_bounds(self, integer_form, value, unit, expected_error):
        """Test integer boundary values."""
        form = integer_form(data={"weight_0": str(value), "weight_1": unit})
        assert not form.is_valid()
        assert expected_error in str(form.errors)

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1e2", 100),  # Scientific notation
            ("100.0", 100),  # Float string
            ("100.7", 100),  # Rounded float
            (" 100 ", 100),  # Padded string
            ("-1 ", -1),  # Negative integer
        ],
    )
    def test_integer_input_formats(self, integer_form, value, expected):
        """Test various integer input formats."""
        form = integer_form(data={"weight_0": value, "weight_1": "gram"})
        assert form.is_valid()
        assert form.cleaned_data["weight"].magnitude == expected

    def test_integer_field_template_name(self):
        """Test that IntegerPintFormField inherits correct template_name."""
        field = IntegerPintFormField(default_unit="gram")
        assert field.template_name == "django/forms/widgets/input.html"

    def test_integer_field_with_tabled_widget_template(self):
        """Test template_name behavior with TabledPintFieldWidget."""
        field = IntegerPintFormField(default_unit="gram", widget=TabledPintFieldWidget(default_unit="gram"))
        assert field.template_name == "django/forms/widgets/input.html"
        assert field.widget.template_name == "django_pint_field/tabled_django_pint_field_widget.html"


@pytest.mark.django_db
class TestDecimalPintFormField:
    """Test the decimal form field functionality."""

    @pytest.fixture
    def decimal_form(self):
        """Create a form instance for testing."""

        class TestForm(ModelForm):
            """Test form with DecimalPintFormField."""

            weight = DecimalPintFormField(
                default_unit="gram", unit_choices=["gram", "kilogram", "ounce"], max_digits=10, decimal_places=2
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
        assert form.cleaned_data["weight"].magnitude == Decimal("100.00")

    def test_max_digits_validation(self, decimal_form):
        """Test max_digits validation."""
        form = decimal_form(data={"weight_0": "12345678.90", "weight_1": "gram"})
        assert not form.is_valid()
        assert "no more than 5 digits in total" in str(form.errors)

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

    def test_missing_max_digits(self):
        """Test initialization without max_digits raises error."""
        with pytest.raises(TypeError, match="max_digits"):
            DecimalPintFormField(default_unit="gram", decimal_places=2)  # pylint: disable=E1125

    def test_missing_decimal_places(self):
        """Test initialization without decimal_places raises error."""
        with pytest.raises(TypeError, match="decimal_places"):
            DecimalPintFormField(default_unit="gram", max_digits=5)  # pylint: disable=E1125

    @pytest.mark.parametrize(
        "max_digits,decimal_places,error_message",
        [
            (0, 0, "max_digits.+positive integer"),
            (2, 3, "decimal_places.+greater than max_digits"),
            (5, -1, "decimal_places.+non-negative"),
            (-3, -3, "max_digits.+non-negative"),
        ],
    )
    def test_invalid_digits_config(self, max_digits, decimal_places, error_message):
        """Test invalid max_digits and decimal_places configurations."""
        with pytest.raises(ValidationError, match=error_message):
            DecimalPintFormField(default_unit="gram", max_digits=max_digits, decimal_places=decimal_places)

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1.2e2", Decimal("120.00")),  # Scientific notation
            (" 100.55 ", Decimal("100.55")),  # Padded string
            ("100", Decimal("100.00")),  # Integer string
            ("-100", Decimal("-100.00")),  # Integer string
        ],
    )
    def test_decimal_input_formats(self, decimal_form, value, expected):
        """Test various decimal input formats."""
        form = decimal_form(data={"weight_0": value, "weight_1": "gram"})
        assert form.is_valid()
        assert form.cleaned_data["weight"].magnitude == expected

    def test_decimal_too_many_decimal_places(self, decimal_form):
        """Test too many decimal places causes form validation to fail."""
        form = decimal_form(data={"weight_0": "100.0000", "weight_1": "gram"})
        assert not form.is_valid()

    @pytest.mark.parametrize(
        "value,unit,error_type",
        [
            ("1" * 11, "gram", ValidationError),  # Too many digits
            ("1" * 10 + ".1", "gram", ValidationError),  # Too many digits
            ("1" * 10, "gram", None),  # Max digits
            ("1" * 10 + ".1", "gram", None),  # Max digits
            ("1" * 10 + ".01", "gram", ValidationError),  # Too many decimal places
            ("1" * 10 + ".0", "gram", None),  # Max decimal places
            ("1" * 10 + ".0" + "1", "gram", ValidationError),  # Too many decimal places
            ("1" * 10 + ".0" + "1", "gram", ValidationError),  # Too many decimal places
        ],
    )
    def test_decimal_validation_errors(self, decimal_form, value, unit, error_type):
        """Test decimal validation edge cases."""
        form = decimal_form(data={"weight_0": value, "weight_1": unit})
        assert not form.is_valid()

    def test_decimal_none_value_with_required(self):
        """Test handling of None value with required field."""

        class RequiredDecimalForm(ModelForm):
            """Form with required DecimalPintFormField."""

            weight = DecimalPintFormField(default_unit="gram", max_digits=10, decimal_places=2, required=True)

            class Meta:
                """Meta class for RequiredDecimalForm."""

                model = DecimalPintFieldSaveModel
                fields = ["weight"]

        form = RequiredDecimalForm(data={"weight_0": None, "weight_1": "gram"})
        assert not form.is_valid()
        assert "This field cannot be null" in str(form.errors["weight"])

    def test_default_display_precision(self):
        """Test that display_decimal_places defaults to decimal_places."""
        field = DecimalPintFormField(default_unit="gram", max_digits=5, decimal_places=2)
        assert field.display_decimal_places == 2
        assert field.widget.widgets[0].attrs["step"] == "0.01"

    def test_custom_display_precision(self):
        """Test custom display_decimal_places setting."""
        field = DecimalPintFormField(default_unit="gram", max_digits=5, decimal_places=3, display_decimal_places=1)
        assert field.display_decimal_places == 1
        assert field.widget.widgets[0].attrs["step"] == "0.1"

    def test_invalid_display_precision(self):
        """Test validation of display_decimal_places."""
        # Test negative value
        with pytest.raises(ValidationError, match="display_decimal_places must be a non-negative integer"):
            DecimalPintFormField(default_unit="gram", max_digits=5, decimal_places=2, display_decimal_places=-1)

        # Test exceeding decimal_places
        with pytest.raises(ValidationError, match="display_decimal_places cannot be greater than decimal_places"):
            DecimalPintFormField(default_unit="gram", max_digits=5, decimal_places=2, display_decimal_places=3)

    @pytest.mark.parametrize(
        "value,decimal_places,display_places,expected_display",
        [
            (Decimal("123.456"), 3, 2, "123.46"),  # Round up
            (Decimal("123.454"), 3, 2, "123.45"),  # Round down
            (Decimal("123.000"), 3, 1, "123.0"),  # Trailing zeros
            (Decimal("123.456"), 3, 0, "123"),  # No decimals
        ],
    )
    def test_value_display_formatting(self, value, decimal_places, display_places, expected_display):
        """Test that values are formatted correctly for display."""
        field = DecimalPintFormField(
            default_unit="gram", max_digits=6, decimal_places=decimal_places, display_decimal_places=display_places
        )
        quantity = ureg.Quantity(value, "gram")
        formatted = field.prepare_value(quantity)
        assert str(formatted[0]) == expected_display
        assert formatted[1] == "gram"

    def test_precision_preservation(self):
        """Test that full precision is preserved when saving, regardless of display setting."""
        field = DecimalPintFormField(default_unit="gram", max_digits=6, decimal_places=3, display_decimal_places=1)

        # Create a value with full precision
        value = ["123.456", "gram"]

        # The value should display with reduced precision
        display_value = field.prepare_value(field.to_python(value))
        assert str(display_value[0]) == "123.5"

        # But the full precision should be preserved in the Python object
        python_value = field.to_python(value)
        assert str(python_value.magnitude) == "123.456"

    def test_decimal_field_template_name(self):
        """Test that DecimalPintFormField inherits correct template_name."""
        field = DecimalPintFormField(default_unit="gram", max_digits=10, decimal_places=2)
        assert field.template_name == "django/forms/widgets/input.html"

    def test_decimal_field_with_tabled_widget_template(self):
        """Test template_name behavior with TabledPintFieldWidget."""
        field = DecimalPintFormField(
            default_unit="gram", max_digits=10, decimal_places=2, widget=TabledPintFieldWidget(default_unit="gram")
        )
        assert field.template_name == "django/forms/widgets/input.html"
        assert field.widget.template_name == "django_pint_field/tabled_django_pint_field_widget.html"
