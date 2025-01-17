"""Test cases for model fields."""

from decimal import ROUND_DOWN
from decimal import ROUND_HALF_UP
from decimal import Decimal
from decimal import getcontext

import pytest
from django.core.exceptions import ValidationError
from django.forms import DecimalField
from django.forms import IntegerField
from pint import UnitRegistry

from django_pint_field.models import BasePintField
from django_pint_field.models import BigIntegerPintField
from django_pint_field.models import DecimalPintField
from django_pint_field.models import IntegerPintField
from django_pint_field.models import create_quantity_from_composite
from django_pint_field.units import ureg


@pytest.mark.django_db
class TestBasePintFieldInitialization:
    """Test initialization of BasePintField."""

    def test_invalid_default_unit_type(self):
        """Test that initializing with non-string default_unit raises ValueError."""
        with pytest.raises(ValidationError, match="Django Pint Fields must be defined with a default_unit"):
            BasePintField(default_unit=123)

    def test_invalid_unit(self):
        """Test that initializing with invalid unit raises ValueError."""
        with pytest.raises(ValidationError):
            BasePintField(default_unit="invalid_unit")

    def test_valid_unit_choices(self):
        """Test initializing with valid unit choices."""
        field = BasePintField(default_unit="gram", unit_choices=["kilogram", "pound"])
        assert len(field.unit_choices) == 3  # Including default unit
        assert field.unit_choices[0] == ("gram", "gram")

    def test_default_unit_added_to_choices(self):
        """Test that default_unit is added to unit_choices if not present."""
        field = BasePintField(default_unit="gram", unit_choices=["kilogram", "pound"])
        assert ("gram", "gram") in field.unit_choices
        assert field.unit_choices[0] == ("gram", "gram")  # Default unit should be first

    def test_dimensionality_check(self):
        """Test that unit choices must have same dimensionality as default unit."""
        with pytest.raises(ValidationError):
            BasePintField(default_unit="gram", unit_choices=["meter", "gram"])


@pytest.mark.django_db
class TestFieldValidation:
    """Test field validation."""

    def test_decimal_field_validation(self):
        """Test decimal field precision validation."""
        field = DecimalPintField(default_unit="gram", display_decimal_places=2)
        value = ureg.Quantity(Decimal("1234.567"), "gram")

        # Test with a model instance that's being added (not loaded from DB)
        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": True})()})

        # This should pass since we're no longer enforcing max_digits/decimal_places
        field.validate(value, validate_obj)


@pytest.mark.django_db
class TestValueConversion:
    """Test value conversion methods."""

    @pytest.mark.parametrize(
        "field_class,input_value,expected_type",
        [
            (IntegerPintField, 100, int),
            (BigIntegerPintField, 100, int),
            (DecimalPintField, Decimal("100.00"), Decimal),
        ],
    )
    def test_to_python_conversion(self, field_class, input_value, expected_type):
        """Test conversion of various input types to python values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        value = field.to_python(input_value)
        assert isinstance(value, ureg.Quantity)
        assert isinstance(value.magnitude, expected_type)


@pytest.mark.django_db
class TestUnitConversion:
    """Test unit conversion functionality."""


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.parametrize(
        "field_class,invalid_value",
        [
            (IntegerPintField, "not a number"),
            (BigIntegerPintField, "not a number"),
            (DecimalPintField, "not a number"),
        ],
    )
    def test_invalid_input_values(self, field_class, invalid_value):
        """Test handling of invalid input values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean(invalid_value, None)

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_none_value_handling(self, field_class):
        """Test handling of None values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2, null=True)
        else:
            field = field_class(default_unit="gram", null=True)

        assert field.clean(None, None) is None

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_none_value_handling_fails(self, field_class):
        """Test handling of None values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean(None, None)

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_empty_string_handling(self, field_class):
        """Test handling of empty strings."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean("", None)


@pytest.mark.django_db
class TestDecimalPintFieldSpecifics:
    """Test DecimalPintField specific functionality."""

    def test_decimal_precision_validation(self):
        """Test validation of decimal precision against context precision."""
        field = DecimalPintField(default_unit="gram", display_decimal_places=2)
        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": True})()})

        # Test value within context precision
        value = ureg.Quantity(Decimal("123.45"), "gram")
        field.validate(value, validate_obj)

        # Test value exceeding context precision
        large_value = ureg.Quantity(Decimal("1" + "0" * getcontext().prec), "gram")
        with pytest.raises(ValidationError):
            field.validate(large_value, validate_obj)


@pytest.mark.django_db
class TestUnitRegistryHandling:
    """Test handling of different unit registries."""

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_quantity_conversion_maintains_value(self, field_class):
        """Test that quantity conversion maintains the value correctly."""
        field = field_class(default_unit="gram")

        # Test with a direct quantity
        if field_class == DecimalPintField:
            value = ureg.Quantity(Decimal("100.00"), "gram")
        else:
            value = ureg.Quantity(100, "gram")

        converted = field.to_python(value)
        assert converted == value
        assert converted._REGISTRY is ureg

    def test_composite_factory_function(self):
        """Test the create_quantity_from_composite factory function."""
        result = create_quantity_from_composite("==", "100.0", "gram")
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("100.0")
        assert result.units == ureg.gram

        # Test with different unit
        result = create_quantity_from_composite("==", "1.5", "kilogram")
        assert result.magnitude == Decimal("1.5")
        assert result.units == ureg.kilogram


@pytest.mark.django_db
class TestFormFieldGeneration:
    """Test form field generation."""

    @pytest.mark.parametrize(
        "field_class,expected_form_field",
        [
            (IntegerPintField, IntegerField),
            (BigIntegerPintField, IntegerField),
            (DecimalPintField, DecimalField),
        ],
    )
    def test_formfield_generation(self, field_class, expected_form_field):
        """Test that correct form fields are generated."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2, unit_choices=["gram", "kilogram"])
        else:
            field = field_class(default_unit="gram", unit_choices=["gram", "kilogram"])

        form_field = field.formfield()
        assert form_field is not None
        assert isinstance(form_field.widget.widgets[1].choices, list)
        assert len(form_field.widget.widgets[1].choices) == 2

    def test_formfield_custom_kwargs(self):
        """Test passing custom kwargs to formfield."""
        field = DecimalPintField(default_unit="gram", display_decimal_places=2)
        form_field = field.formfield(help_text="Custom help", label="Custom label")
        assert form_field.help_text == "Custom help"
        assert form_field.label == "Custom label"


@pytest.mark.django_db
class TestFieldDeconstructionAndCloning:
    """Test field deconstruction and cloning capabilities."""

    @pytest.mark.parametrize(
        "field_class,extra_kwargs",
        [
            (IntegerPintField, {}),
            (BigIntegerPintField, {}),
            (DecimalPintField, {"display_decimal_places": 2}),
        ],
    )
    def test_field_deconstruction(self, field_class, extra_kwargs):
        """Test that fields can be deconstructed properly."""
        kwargs = {"default_unit": "gram", "unit_choices": [("gram", "gram"), ("kilogram", "kilogram")], **extra_kwargs}
        field = field_class(**kwargs)

        name, path, args, new_kwargs = field.deconstruct()

        assert "default_unit" in new_kwargs
        assert new_kwargs["default_unit"] == "gram"
        assert "unit_choices" in new_kwargs
        assert len(new_kwargs["unit_choices"]) == 2
        assert ("gram", "gram") in new_kwargs["unit_choices"]
        assert ("kilogram", "kilogram") in new_kwargs["unit_choices"]

        if field_class == DecimalPintField:
            assert "display_decimal_places" in new_kwargs


@pytest.mark.django_db
class TestAdditionalEdgeCases:
    """Test additional edge cases and error conditions."""

    @pytest.mark.parametrize(
        "field_class,value,expected_error",
        [
            (DecimalPintField, {"magnitude": "not_a_number", "units": "gram"}, ValidationError),
            (DecimalPintField, {"magnitude": "100", "units": None}, ValidationError),
            (IntegerPintField, {"magnitude": 100, "units": "invalid_unit"}, ValidationError),
        ],
    )
    def test_invalid_dictionary_values(self, field_class, value, expected_error):
        """Test handling of invalid dictionary input values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(expected_error):
            field.get_prep_value(value)

    @pytest.mark.parametrize(
        "field_class,value",
        [
            (IntegerPintField, []),
            (BigIntegerPintField, ()),
            (DecimalPintField, {}),
        ],
    )
    def test_empty_container_values(self, field_class, value):
        """Test handling of empty container values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        result = field.get_prep_value(value)
        assert result == value

    def test_with_digits_formatting(self):
        """Test decimal display formatting with different display_decimal_places settings."""
        # Test with 2 decimal places
        field = DecimalPintField(default_unit="gram", display_decimal_places=2)

        value = ureg.Quantity(Decimal("123.4564"), "gram")
        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": True})()})

        # Should pass validation
        field.validate(value, validate_obj)

        # Verify display formatting
        assert str(field.format_value(value)) == "123.46 gram"

        # Test with 3 decimal places
        field_three = DecimalPintField(default_unit="gram", display_decimal_places=3)
        assert str(field_three.format_value(value)) == "123.456 gram"

    def test_with_digits_without_decimal_places(self):
        """Test decimal display formatting without specifying display_decimal_places."""
        field = DecimalPintField(default_unit="gram")

        value = ureg.Quantity(Decimal("123.4564"), "gram")
        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": True})()})

        # Should pass validation
        field.validate(value, validate_obj)

        # Without display_decimal_places, should show full precision
        assert str(field.format_value(value)) == "123.4564 gram"


@pytest.mark.django_db
class TestDatabaseOperations:
    """Test database-related operations."""

    @pytest.mark.parametrize(
        "field_class,test_values",
        [
            (IntegerPintField, [100, 200, 300]),
            (BigIntegerPintField, [1000000, 2000000, 3000000]),
            (DecimalPintField, [Decimal("100.00"), Decimal("200.00"), Decimal("300.00")]),
        ],
    )
    def test_db_type_and_value_conversion(self, field_class, test_values):
        """Test database type and value conversion."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", display_decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        # Test db_type
        assert field.db_type(connection=None) == "pint_field"

        # Test conversion for each value
        for value in test_values:
            quantity = ureg.Quantity(value, "gram")
            db_value = field.get_prep_value(quantity)
            assert isinstance(db_value, ureg.Quantity)

    def test_decimal_field_db_prep_save(self):
        """Test DecimalPintField's get_db_prep_save method."""
        field = DecimalPintField(default_unit="gram", display_decimal_places=2, rounding_method=ROUND_HALF_UP)

        # Test with a high-precision value
        value = ureg.Quantity(Decimal("100.456"), "gram")
        result = field.get_prep_value(value)

        # Should preserve full precision in the database
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("100.456")

        # Test with None
        assert field.get_db_prep_save(None, connection=None) is None


@pytest.mark.django_db
class TestDecimalValidationBehavior:
    """Test the decimal validation behavior in different contexts."""

    def test_form_input_validation(self):
        """Test that form input respects context precision."""
        field = DecimalPintField(default_unit="acre_feet", display_decimal_places=2)

        # Create a value that exceeds context precision
        value = ureg.Quantity(Decimal("1" + "0" * getcontext().prec), "acre_feet")

        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": True})()})

        with pytest.raises(ValidationError) as exc_info:
            field.validate(value, validate_obj)
        assert "maximum precision" in str(exc_info.value)

    def test_model_load_bypasses_validation(self):
        """Test that loading values from the database bypasses validation."""
        field = DecimalPintField(default_unit="acre_feet", display_decimal_places=2)
        value = ureg.Quantity(Decimal("123.45678"), "acre_feet")

        # Create a model instance state indicating it's from the database
        validate_obj = type("ValidateObj", (), {"_state": type("State", (), {"adding": False})()})

        # This should not raise ValidationError despite having more decimal places
        field.validate(value, validate_obj)

    def test_new_instance_validation(self):
        """Test validation for new model instances."""
        field = DecimalPintField(default_unit="acre_feet", display_decimal_places=2)

        # Create a value that exceeds context precision
        value = ureg.Quantity(Decimal("1" + "0" * getcontext().prec), "acre_feet")

        class ModelState:
            adding = True

        class ModelInstance:
            _state = ModelState()

        with pytest.raises(ValidationError) as exc_info:
            field.validate(value, ModelInstance())
        assert "maximum precision" in str(exc_info.value)

    def test_prep_value_bypasses_validation(self):
        """Test that get_prep_value allows full precision for database operations."""
        field = DecimalPintField(default_unit="acre_feet", display_decimal_places=2)

        # Create a quantity with more decimal places than allowed
        value = ureg.Quantity(Decimal("123.45678"), "acre_feet")

        # get_prep_value should not validate decimal places
        try:
            result = field.get_prep_value(value)
            assert result.magnitude == value.magnitude
        except ValidationError as e:
            pytest.fail(f"get_prep_value should not validate decimals but raised: {e}")
