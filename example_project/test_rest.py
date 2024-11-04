"""Test the rest framework integration."""

from collections import OrderedDict
from decimal import Decimal

import pytest
from pint import UndefinedUnitError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django_pint_field.rest import DecimalPintRestField
from django_pint_field.rest import IntegerPintRestField
from django_pint_field.units import ureg
from example_project.example.models import EmptyHayBaleBigInteger
from example_project.example.models import EmptyHayBaleDecimal
from example_project.example.models import EmptyHayBaleInteger


# Constants
INTEGER_QUANTITY = ureg.Quantity(1 * ureg.ounce)
DECIMAL_QUANTITY = ureg.Quantity(Decimal("1.0") * ureg.ounce)


@pytest.fixture
def serializer_class():
    """Create a basic serializer class for testing."""

    def _create_serializer(field_class, model=None):
        if model:

            class TestSerializer(serializers.ModelSerializer):
                """Test serializer."""

                weight = field_class()

                class Meta:
                    """Meta class."""

                    model = model
                    fields = ["name", "weight"]

        else:

            class TestSerializer(serializers.Serializer):
                """Test serializer."""

                weight = field_class()

        return TestSerializer

    return _create_serializer


@pytest.fixture
def field_params():
    """Parameters for different field types."""
    return {
        "integer": {
            "model": EmptyHayBaleInteger,
            "field": IntegerPintRestField,
            "quantity": INTEGER_QUANTITY,
            "expected_repr": "1 ounce",
        },
        "biginteger": {
            "model": EmptyHayBaleBigInteger,
            "field": IntegerPintRestField,
            "quantity": INTEGER_QUANTITY,
            "expected_repr": "1 ounce",
        },
        "decimal": {
            "model": EmptyHayBaleDecimal,
            "field": DecimalPintRestField,
            "quantity": DECIMAL_QUANTITY,
            "expected_repr": "Quantity(1.0 ounce)",
        },
    }


class TestPintFieldSerializer:
    """Test the PintField serializers."""

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_blank_field(self, serializer_class, field_params, field_type):
        """Test serializer with blank field."""
        params = field_params[field_type]
        TestSerializer = serializer_class(params["field"], params["model"])

        data = {"name": "any"}
        serializer = TestSerializer(data=data)

        assert not serializer.is_valid()
        assert serializer.data == {"name": "any"}

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_quantity(self, serializer_class, field_params, field_type):
        """Test serializer with quantity."""
        params = field_params[field_type]
        TestSerializer = serializer_class(params["field"])

        data = {"name": "any", "weight": params["quantity"]}
        serializer = TestSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == OrderedDict([("weight", params["quantity"])])

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_empty_required(self, field_params, field_type):
        """Test serializer with empty required field."""
        params = field_params[field_type]

        class TestSerializer(serializers.Serializer):
            weight = params["field"](allow_null=False)

        serializer = TestSerializer(data={"name": "any", "weight": None})
        assert not serializer.is_valid()
        assert serializer.validated_data == {}

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_empty_optional(self, field_params, field_type):
        """Test serializer with empty optional field."""
        params = field_params[field_type]

        class TestSerializer(serializers.Serializer):
            """Test serializer."""

            weight = params["field"](allow_null=True)

        serializer = TestSerializer(data={"name": "any", "weight": None})
        assert serializer.is_valid()

    @pytest.mark.parametrize(
        "field_type,input_data,expected",
        [
            ("integer", "1 ounce", INTEGER_QUANTITY),
            ("biginteger", "1 ounce", INTEGER_QUANTITY),
            ("decimal", "1 ounce", DECIMAL_QUANTITY),
        ],
    )
    def test_good_data_to_internal_value(self, field_params, field_type, input_data, expected):
        """Test to_internal_value with good data."""
        params = field_params[field_type]
        field = params["field"]()
        assert field.to_internal_value(input_data) == expected

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_bad_units_to_internal_value(self, field_params, field_type):
        """Test to_internal_value with bad units."""
        field = field_params[field_type]["field"]()
        with pytest.raises(UndefinedUnitError):
            field.to_internal_value("1 elephants")

    @pytest.mark.parametrize(
        "field_type,bad_value",
        [
            ("integer", "large ounce"),
            ("biginteger", "large ounce"),
            ("decimal", "large ounce"),
        ],
    )
    def test_bad_magnitude_to_internal_value(self, field_params, field_type, bad_value):
        """Test to_internal_value with bad magnitude."""
        field = field_params[field_type]["field"]()
        with pytest.raises(ValidationError):
            field.to_internal_value(bad_value)

    @pytest.mark.parametrize("field_type", ["integer", "biginteger", "decimal"])
    def test_good_to_representation(self, field_params, field_type):
        """Test to_representation with good data."""
        params = field_params[field_type]
        field = params["field"]()

        representation = field.to_representation(params["quantity"])
        assert representation == params["expected_repr"]

    @pytest.mark.parametrize(
        "field_type,bad_value",
        [
            ("integer", "string"),
            ("biginteger", "string"),
            ("decimal", "string"),
            ("integer", 1),
            ("biginteger", 1),
            ("decimal", 1),
        ],
    )
    def test_bad_value_to_representation(self, field_params, field_type, bad_value):
        """Test to_representation with bad values."""
        field = field_params[field_type]["field"]()
        with pytest.raises(ValidationError):
            field.to_representation(bad_value)

    def test_decimal_field_with_parameters(self, field_params):
        """Test DecimalPintRestField with decimal parameters."""
        field = DecimalPintRestField(max_digits=3, decimal_places=1)
        value = ureg.Quantity(Decimal("1.0"), ureg.ounce)
        representation = field.to_representation(value)
        assert representation == "Quantity(1.0 ounce)"
