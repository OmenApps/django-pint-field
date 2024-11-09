"""Test cases for model fields."""

from decimal import ROUND_DOWN
from decimal import ROUND_HALF_UP
from decimal import Decimal

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
        field = BasePintField(default_unit="gram", unit_choices=["gram", "kilogram"])
        assert field.unit_choices == ["gram", "kilogram"]

    def test_default_unit_added_to_choices(self):
        """Test that default_unit is added to unit_choices if not present."""
        field = BasePintField(default_unit="gram", unit_choices=["kilogram", "pound"])
        assert "gram" in field.unit_choices
        assert field.unit_choices[0] == "gram"  # Default unit should be first

    def test_dimensionality_check(self):
        """Test that unit choices must have same dimensionality as default unit."""
        with pytest.raises(ValidationError):
            BasePintField(default_unit="gram", unit_choices=["meter", "gram"])


@pytest.mark.django_db
class TestFieldValidation:
    """Test field validation."""

    # def test_decimal_field_precision(self):
    #     """Test decimal field precision validation."""
    #     field = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2)
    #     with pytest.raises(ValidationError):
    #         # Value with too many digits
    #         field.clean(ureg.Quantity(Decimal('1234.567'), "gram"), None)


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
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
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
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean(invalid_value, None)

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_none_value_handling(self, field_class):
        """Test handling of None values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2, null=True)
        else:
            field = field_class(default_unit="gram", null=True)

        assert field.clean(None, None) is None

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_none_value_handling_fails(self, field_class):
        """Test handling of None values."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean(None, None)

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_empty_string_handling(self, field_class):
        """Test handling of empty strings."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        with pytest.raises(ValidationError):
            field.clean("", None)


@pytest.mark.django_db
class TestDecimalPintFieldSpecifics:
    """Test DecimalPintField specific functionality."""

    def test_invalid_decimal_places(self):
        """Test validation of decimal_places parameter."""
        with pytest.raises(ValidationError):
            DecimalPintField(default_unit="gram", max_digits=5, decimal_places=-1)

    def test_invalid_max_digits(self):
        """Test validation of max_digits parameter."""
        with pytest.raises(ValidationError):
            DecimalPintField(default_unit="gram", max_digits=0, decimal_places=2)

    def test_decimal_places_greater_than_max_digits(self):
        """Test validation when decimal_places > max_digits."""
        with pytest.raises(ValidationError):
            DecimalPintField(default_unit="gram", max_digits=2, decimal_places=3)

    @pytest.mark.parametrize(
        "value,max_digits,decimal_places,should_raise",
        [
            (Decimal("123.45"), 5, 2, False),
            (Decimal("1234.56"), 5, 2, True),
            (Decimal("123.456"), 5, 2, True),
            (Decimal("12.345"), 5, 3, False),
        ],
    )
    def test_decimal_precision_validation(self, value, max_digits, decimal_places, should_raise):
        """Test validation of decimal precision."""
        field = DecimalPintField(default_unit="gram", max_digits=max_digits, decimal_places=decimal_places)
        quantity = ureg.Quantity(value, "gram")

        if should_raise:
            with pytest.raises(ValidationError):
                field.clean(quantity, None)
        else:
            cleaned = field.clean(quantity, None)
            assert isinstance(cleaned, ureg.Quantity)
            assert isinstance(cleaned.magnitude, Decimal)


@pytest.mark.django_db
class TestUnitRegistryHandling:
    """Test handling of different unit registries."""

    @pytest.fixture
    def different_ureg(self):
        """Create a different unit registry for testing."""
        return UnitRegistry()

    @pytest.mark.parametrize("field_class", [IntegerPintField, BigIntegerPintField, DecimalPintField])
    def test_unit_registry_mismatch(self, field_class, different_ureg):
        """Test handling of quantities from different unit registries."""
        if field_class == DecimalPintField:
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
            value = different_ureg.Quantity(Decimal("100.00"), "gram")
        else:
            field = field_class(default_unit="gram")
            value = different_ureg.Quantity(100, "gram")

        # Should warn but not fail
        with pytest.warns(RuntimeWarning):
            result = field.fix_unit_registry(value)
            assert result.units == ureg.gram
            assert result._REGISTRY == ureg

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
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2, unit_choices=["gram", "kilogram"])
        else:
            field = field_class(default_unit="gram", unit_choices=["gram", "kilogram"])

        form_field = field.formfield()
        assert form_field is not None
        assert isinstance(form_field.widget.widgets[1].choices, list)
        assert len(form_field.widget.widgets[1].choices) == 2

    def test_formfield_custom_kwargs(self):
        """Test passing custom kwargs to formfield."""
        field = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2)
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
            (DecimalPintField, {"max_digits": 5, "decimal_places": 2}),
        ],
    )
    def test_field_deconstruction(self, field_class, extra_kwargs):
        """Test that fields can be deconstructed properly."""
        kwargs = {"default_unit": "gram", "unit_choices": ["gram", "kilogram"], **extra_kwargs}
        field = field_class(**kwargs)

        name, path, args, new_kwargs = field.deconstruct()

        assert "default_unit" in new_kwargs
        assert new_kwargs["default_unit"] == "gram"
        assert "unit_choices" in new_kwargs
        assert set(new_kwargs["unit_choices"]) == {"gram", "kilogram"}

        if field_class == DecimalPintField:
            assert "max_digits" in new_kwargs
            assert "decimal_places" in new_kwargs


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
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
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
            field = field_class(default_unit="gram", max_digits=5, decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        result = field.get_prep_value(value)
        assert result == value

    def test_decimal_rounding_methods(self):
        """Test different rounding methods for DecimalPintField."""
        field_up = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2, rounding_method=ROUND_HALF_UP)

        field_down = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2, rounding_method=ROUND_DOWN)

        value = ureg.Quantity(Decimal("123.4564"), "gram")

        result_up = field_up.clean(value, None)
        result_down = field_down.clean(value, None)

        assert result_up.magnitude == Decimal("123.46")
        assert result_down.magnitude == Decimal("123.45")

    def test_invalid_rounding_method(self):
        """Test that invalid rounding method raises ValueError."""
        with pytest.raises(ValidationError):
            DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2, rounding_method="INVALID_METHOD")


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
            field = field_class(default_unit="gram", max_digits=10, decimal_places=2)
        else:
            field = field_class(default_unit="gram")

        # Test db_type
        assert field.db_type(connection=None) == "pint_field"

        # Test conversion for each value
        for value in test_values:
            quantity = ureg.Quantity(value, "gram")
            db_value = field.get_prep_value(quantity)
            assert isinstance(db_value, ureg.Quantity)

    def test_decimal_field_db_prep_save_with_error(self):
        """Test DecimalPintField's get_db_prep_save method."""
        field = DecimalPintField(default_unit="gram", max_digits=10, decimal_places=2)

        # Test with Quantity
        value = ureg.Quantity(Decimal("100.456"), "gram")
        with pytest.raises(ValidationError):
            field.get_db_prep_save(value, connection=None)

        # Test with None
        assert field.get_db_prep_save(None, connection=None) is None

        # Test with dictionary
        dict_value = {"magnitude": "100.456", "units": "gram"}
        with pytest.raises(ValidationError):
            field.get_db_prep_save(dict_value, connection=None)

    def test_decimal_field_db_prep_save(self):
        """Test DecimalPintField's get_db_prep_save method."""
        field = DecimalPintField(
            default_unit="gram",
            max_digits=10,
            decimal_places=2,
            rounding_method=ROUND_HALF_UP,
        )

        # Test with Quantity
        value = ureg.Quantity(Decimal("100.456"), "gram")
        result = field.get_db_prep_save(value, connection=None)
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("100.46")  # Rounded to 2 decimal places

        # Test with None
        assert field.get_db_prep_save(None, connection=None) is None

        # # Test with dictionary
        # dict_value = {'magnitude': '100.456', 'units': 'gram'}  # ToDo: Handle situations where a number is passed as a string
        # result = field.get_db_prep_save(dict_value, connection=None)
        # assert isinstance(result, ureg.Quantity)
        # assert result.magnitude == Decimal('100.46')

        # Test with dictionary and Decimal
        dict_value = {"magnitude": Decimal("100.456"), "units": "gram"}
        result = field.get_db_prep_save(dict_value, connection=None)
        assert isinstance(result, ureg.Quantity)
        assert result.magnitude == Decimal("100.46")
