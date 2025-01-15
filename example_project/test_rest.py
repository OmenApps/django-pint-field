"""Test cases for REST framework integration."""

from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from django_pint_field.helpers import PintFieldProxy
from django_pint_field.rest import DecimalPintRestField
from django_pint_field.rest import IntegerPintRestField
from django_pint_field.rest import PintRestField
from django_pint_field.units import ureg
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestPintRestField:
    """Test cases for the PintRestField (dictionary-based serialization)."""

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
    def test_serializer_to_representation(self):
        """Test dictionary representation of Quantity objects."""
        quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        serializer = PintRestField()
        result = serializer.to_representation(quantity)

        assert isinstance(result, dict)
        assert result["magnitude"] == self.DEFAULT_WEIGHT
        assert result["units"] == self.DEFAULT_UNIT

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_serializer_to_internal_value_valid(self):
        """Test conversion from valid dictionary to Quantity."""
        input_data = {"magnitude": self.DEFAULT_WEIGHT, "units": self.DEFAULT_UNIT}
        serializer = PintRestField()
        result = serializer.to_internal_value(input_data)

        assert isinstance(result, Quantity)
        assert result.magnitude == self.DEFAULT_WEIGHT
        assert str(result.units) == self.DEFAULT_UNIT

    @pytest.mark.parametrize("setup_class", ["integer", "big_integer", "decimal"], indirect=True)
    def test_serializer_none_value(self):
        """Test handling of None values."""
        serializer = PintRestField()
        result = serializer.to_representation(None)
        assert result is None


@pytest.mark.django_db
class TestIntegerPintRestField:
    """Test cases for the IntegerPintRestField (string-based serialization)."""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        """Set up test parameters."""
        self.DEFAULT_WEIGHT = 100
        self.DEFAULT_UNIT = "gram"
        self.serializer = IntegerPintRestField()

    def test_to_representation(self):
        """Test string representation of integer Quantity."""
        quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        result = self.serializer.to_representation(quantity)
        assert result == f"{self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT}"

    def test_to_representation_wrapped(self):
        """Test string representation of integer Quantity."""
        quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        serializer = IntegerPintRestField(wrap=True)
        result = serializer.to_representation(quantity)
        assert result == f"Quantity({self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT})"

    def test_to_internal_value_from_string(self):
        """Test conversion from string to Quantity."""
        input_str = f"{self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT}"
        result = self.serializer.to_internal_value(input_str)

        assert isinstance(result, Quantity)
        assert result.magnitude == self.DEFAULT_WEIGHT
        assert str(result.units) == self.DEFAULT_UNIT

    def test_to_internal_value_from_quantity(self):
        """Test handling of Quantity input."""
        input_quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        result = self.serializer.to_internal_value(input_quantity)

        assert result == input_quantity

    def test_float_to_int_conversion(self):
        """Test that float values are properly converted to integers."""
        input_str = "100.6 gram"
        result = self.serializer.to_internal_value(input_str)

        assert isinstance(result.magnitude, int)
        assert result.magnitude == 100  # Rounds down

    def test_invalid_string_format(self):
        """Test handling of invalid string formats."""
        invalid_inputs = [
            "100",  # Missing unit
            "gram",  # Missing magnitude
            "100 gram extra",  # Extra content
            " gram",  # Missing magnitude
            "abc gram",  # Invalid magnitude
            "100 ",  # Missing unit
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                self.serializer.to_internal_value(invalid_input)

    def test_invalid_units(self):
        """Test handling of invalid units."""
        with pytest.raises(ValidationError):
            self.serializer.to_internal_value("100 invalid_unit")

    def test_none_value(self):
        """Test handling of None values."""
        result = self.serializer.to_representation(None)
        assert result is None


@pytest.mark.django_db
class TestDecimalPintRestField:
    """Test cases for the DecimalPintRestField (string-based serialization with Quantity wrapper)."""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        """Set up test parameters."""
        self.DEFAULT_WEIGHT = Decimal("100.5")
        self.DEFAULT_UNIT = "gram"
        self.serializer = DecimalPintRestField()

    def test_to_representation(self):
        """Test string representation of decimal Quantity."""
        quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        result = self.serializer.to_representation(quantity)
        assert result == f"{self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT}"

    def test_to_representation_wrapped(self):
        """Test string representation of decimal Quantity."""
        quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        serializer = DecimalPintRestField(wrap=True)
        result = serializer.to_representation(quantity)
        assert result == f"Quantity({self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT})"

    def test_to_internal_value_from_string(self):
        """Test conversion from string to Quantity."""
        test_cases = [
            f"{self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT}",
            f"Quantity({self.DEFAULT_WEIGHT} {self.DEFAULT_UNIT})",
        ]

        for input_str in test_cases:
            result = self.serializer.to_internal_value(input_str)
            assert isinstance(result, Quantity)
            assert result.magnitude == self.DEFAULT_WEIGHT
            assert str(result.units) == self.DEFAULT_UNIT

    def test_to_internal_value_from_quantity(self):
        """Test handling of Quantity input."""
        input_quantity = Quantity(self.DEFAULT_WEIGHT, self.DEFAULT_UNIT)
        result = self.serializer.to_internal_value(input_quantity)
        assert result == input_quantity

    def test_decimal_precision(self):
        """Test that decimal precision is maintained."""
        precise_value = Decimal("100.12345")
        quantity = Quantity(precise_value, self.DEFAULT_UNIT)
        result = self.serializer.to_internal_value(self.serializer.to_representation(quantity))

        assert result.magnitude == precise_value
        assert isinstance(result.magnitude, Decimal)

    def test_invalid_string_format(self):
        """Test handling of invalid string formats."""
        invalid_inputs = [
            "100.5",  # Missing unit
            "gram",  # Missing magnitude
            "100.5 gram extra",  # Extra content
            " gram",  # Missing magnitude
            "abc gram",  # Invalid magnitude
            "100.5 ",  # Missing unit
            "Quantity()",  # Empty Quantity
            "Quantity(100.5)",  # Missing unit in Quantity
            "Quantity(gram)",  # Missing magnitude in Quantity
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                self.serializer.to_internal_value(invalid_input)

    def test_invalid_units(self):
        """Test handling of invalid units."""
        with pytest.raises(ValidationError):
            self.serializer.to_internal_value("100.5 invalid_unit")

    def test_none_value(self):
        """Test handling of None values."""
        result = self.serializer.to_representation(None)
        assert result is None

    def test_constructor_ignores_decimal_kwargs(self):
        """Test that decimal-specific kwargs are properly ignored."""
        serializer = DecimalPintRestField(max_digits=10, decimal_places=2)
        quantity = Quantity(Decimal("100.5"), self.DEFAULT_UNIT)
        result = serializer.to_representation(quantity)
        assert result == f"{quantity}"

    def test_wrapped_constructor_ignores_decimal_kwargs(self):
        """Test that decimal-specific kwargs are properly ignored in wrapped representation."""
        serializer = DecimalPintRestField(max_digits=10, decimal_places=2, wrap=True)
        quantity = Quantity(Decimal("100.5"), self.DEFAULT_UNIT)
        result = serializer.to_representation(quantity)
        assert result == f"Quantity({quantity})"


@pytest.mark.django_db
class TestErrorMessages:
    """Test error messages for all serializer types."""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        """Set up test parameters."""
        self.dict_serializer = PintRestField()
        self.int_serializer = IntegerPintRestField()
        self.decimal_serializer = DecimalPintRestField()

    def test_pintfield_serializer_errors(self):
        """Test error messages from PintRestField."""
        with pytest.raises(ValidationError, match="Invalid format"):
            self.dict_serializer.to_internal_value("not a dict")

        with pytest.raises(ValidationError, match="Both magnitude and units are required"):
            self.dict_serializer.to_internal_value({"magnitude": 100})

    def test_integer_field_errors(self):
        """Test error messages from IntegerPintRestField."""
        with pytest.raises(ValidationError, match="Invalid magnitude"):
            self.int_serializer.to_internal_value("invalid format")

        with pytest.raises(ValidationError, match="Expected string or Quantity"):
            self.int_serializer.to_internal_value(123)

    def test_decimal_field_errors(self):
        """Test error messages from DecimalPintRestField."""
        with pytest.raises(ValidationError, match="Invalid magnitude"):
            self.decimal_serializer.to_internal_value("invalid format")

        with pytest.raises(ValidationError, match="Expected string or Quantity"):
            self.decimal_serializer.to_internal_value(123.45)


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases for all serializer types."""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        """Set up test parameters."""
        self.dict_serializer = PintRestField()
        self.int_serializer = IntegerPintRestField()
        self.decimal_serializer = DecimalPintRestField()

    def test_zero_values(self):
        """Test handling of zero values."""
        quantity = Quantity(0, "gram")

        assert self.dict_serializer.to_representation(quantity) == {"magnitude": 0, "units": "gram"}
        assert self.int_serializer.to_representation(quantity) == "0 gram"
        assert self.decimal_serializer.to_representation(quantity) == "0 gram"

    def test_negative_values(self):
        """Test handling of negative values."""
        quantity = Quantity(-100, "gram")

        assert self.dict_serializer.to_representation(quantity) == {"magnitude": -100, "units": "gram"}
        assert self.int_serializer.to_representation(quantity) == "-100 gram"
        assert self.decimal_serializer.to_representation(quantity) == "-100 gram"

    def test_very_large_values(self):
        """Test handling of very large values."""
        large_value = 10**20
        quantity = Quantity(large_value, "gram")

        assert self.dict_serializer.to_representation(quantity)["magnitude"] == large_value
        assert self.int_serializer.to_representation(quantity) == f"{large_value} gram"
        assert self.decimal_serializer.to_representation(quantity) == f"{large_value} gram"


@pytest.mark.django_db
class TestPintRestFieldAdvanced:
    """Additional test cases for PintRestField focusing on advanced scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test parameters."""
        self.serializer = PintRestField()
        self.unit_choices = ["gram", "kilogram", "pound"]

    def test_proxy_handling(self):
        """Test handling of PintFieldProxy objects."""
        quantity = Quantity(100, "gram")
        proxy = PintFieldProxy(quantity, None)  # Mock converter
        result = self.serializer.to_representation(proxy)

        assert isinstance(result, dict)
        assert result["magnitude"] == 100
        assert result["units"] == "gram"

    def test_dimensionality_conversion(self):
        """Test handling quantities with different but compatible units."""
        test_cases = [
            ({"magnitude": 1000, "units": "gram"}, "kilogram", 1),
            ({"magnitude": 1, "units": "kilogram"}, "gram", 1000),
            ({"magnitude": 453.59237, "units": "gram"}, "pound", 1),
        ]

        for input_data, target_unit, expected_magnitude in test_cases:
            quantity = self.serializer.to_internal_value(input_data)
            converted = quantity.to(target_unit)
            assert pytest.approx(converted.magnitude, rel=1e-5) == expected_magnitude

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"magnitude": "not_a_number", "units": "gram"},
            {"magnitude": None, "units": "gram"},
            {"units": "gram"},  # Missing magnitude
            {"magnitude": 100},  # Missing units
            {},  # Empty dict
        ],
    )
    def test_invalid_dictionary_formats(self, invalid_data):
        """Test various invalid dictionary formats."""
        with pytest.raises(ValidationError):
            self.serializer.to_internal_value(invalid_data)


@pytest.mark.django_db
class TestDjangoNinjaIntegration:
    """Test cases for Django Ninja integration."""

    @pytest.fixture
    def integer_model(self):
        """Create a test model instance."""
        return IntegerPintFieldSaveModel.objects.create(name="Test Integer", weight=Quantity(100, "gram"))

    def test_schema_serialization(self, client, integer_model):
        """Test Django Ninja schema serialization."""
        # Test list endpoint
        response = client.get("/api_ninja/integers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["weight"] == "100 gram"

        # Test detail endpoint
        response = client.get(f"/api_ninja/integers/{integer_model.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == "100 gram"

    def test_schema_not_found(self, client):
        """Test 404 handling in Django Ninja endpoints."""
        response = client.get("/api_ninja/integers/999")
        assert response.status_code == 404


@pytest.mark.django_db
class TestRestFrameworkViewsets:
    """Test cases for DRF ViewSets."""

    @pytest.fixture
    def decimal_model(self):
        """Create a test model instance."""
        return DecimalPintFieldSaveModel.objects.create(name="Test Decimal", weight=Quantity(Decimal("100.50"), "gram"))

    @pytest.fixture
    def bigint_model(self):
        """Create a test model instance."""
        return BigIntegerPintFieldSaveModel.objects.create(name="Test BigInt", weight=Quantity(1000, "gram"))

    def test_viewset_list(self, client, decimal_model):
        """Test DRF ViewSet list endpoints."""
        # Test decimal viewset
        response = client.get("/api/decimals/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["weight"] == "100.50 gram"

    def test_viewset_detail(self, client, bigint_model):
        """Test DRF ViewSet detail endpoints."""
        response = client.get(f"/api/big_integers/{bigint_model.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == "1000 gram"

    def test_viewset_pagination(self, client):
        """Test DRF ViewSet pagination."""
        # Create multiple test objects
        for i in range(5):
            IntegerPintFieldSaveModel.objects.create(name=f"Test {i}", weight=Quantity(100 + i, "gram"))

        # Test paginated response
        response = client.get("/api/integers/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5
        # Verify the data is in order
        for i, item in enumerate(data):
            assert item["weight"] == f"{100 + i} gram"

    def test_general_viewset_format(self, client):
        """Test dictionary format in general integer viewset."""
        # Create test data
        model = IntegerPintFieldSaveModel.objects.create(name="Test General", weight=Quantity(100, "gram"))

        # Test that response uses dictionary format
        response = client.get(f"/api/general_integers/{model.id}/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["weight"], dict)
        assert data["weight"]["magnitude"] == 100
        assert data["weight"]["units"] == "gram"
