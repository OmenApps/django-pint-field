"""Test Django admin functionality for pint fields."""

from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from django_pint_field.units import ureg
from example_project.example.admin import IntegerPintFieldSaveModelAdmin
from example_project.example.admin import ReadOnlyEditing
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import HayBale
from example_project.example.models import IntegerPintFieldSaveModel


pytestmark = pytest.mark.django_db


@pytest.fixture
def site():
    """Create admin site instance."""
    return AdminSite()


@pytest.fixture
def integer_admin(site):
    """Create IntegerPintFieldSaveModelAdmin instance."""
    return IntegerPintFieldSaveModelAdmin(IntegerPintFieldSaveModel, site)


@pytest.fixture
def integer_model():
    """Create test IntegerPintFieldSaveModel instance."""
    return IntegerPintFieldSaveModel.objects.create(name="Test Integer", weight=ureg.Quantity(1000, "gram"))


@pytest.fixture
def decimal_model():
    """Create test DecimalPintFieldSaveModel instance."""
    return DecimalPintFieldSaveModel.objects.create(
        name="Test Decimal", weight=ureg.Quantity(Decimal("1000.50"), "gram")
    )


class TestAdminListDisplay:
    """Test admin list display functionality."""

    def test_integer_list_display(self, admin_client, integer_model):
        """Test integer field list display shows correct values."""
        response = admin_client.get(reverse("admin:example_integerpintfieldsavemodel_changelist"))
        assert response.status_code == 200

        content = response.content.decode()
        # Check primary value display
        assert str(integer_model.weight.magnitude) in content
        # Check only compatible unit conversions
        kilo_mag = str(integer_model.weight.to("kilogram").magnitude)
        assert kilo_mag in content


class TestAdminFormHandling:
    """Test admin form submission handling."""

    @pytest.mark.parametrize(
        "test_data",
        [
            pytest.param(
                {
                    "name": "Test Add Integer",
                    "weight_0": "500",
                    "weight_1": "gram",
                    "expected_magnitude": 500,
                    "expected_unit": "gram",
                },
                id="gram-input",
            ),
            pytest.param(
                {
                    "name": "Test Add Kilo",
                    "weight_0": "2",
                    "weight_1": "kilogram",
                    "expected_magnitude": 2000,
                    "expected_unit": "gram",
                },
                id="kilogram-input",
            ),
        ],
    )
    def test_add_integer_model(self, admin_client, test_data):
        """Test adding models with different units."""
        # Prepare form data
        form_data = {
            "name": test_data["name"],
            "weight_0": test_data["weight_0"],
            "weight_1": test_data["weight_1"],
        }

        response = admin_client.post(reverse("admin:example_integerpintfieldsavemodel_add"), data=form_data)
        assert response.status_code == 302  # Successful redirect after save

        # Verify object was created
        model = IntegerPintFieldSaveModel.objects.get(name=test_data["name"])
        assert isinstance(model.weight.quantity.magnitude, (int, Decimal))

        # Verify the stored value matches expected
        weight_in_base = model.weight.quantity.to(test_data["expected_unit"])
        assert int(weight_in_base.magnitude) == test_data["expected_magnitude"]

    def test_validation_errors(self, admin_client):
        """Test form validation errors."""
        # Test invalid unit
        response = admin_client.post(
            reverse("admin:example_integerpintfieldsavemodel_add"),
            data={"name": "Invalid Unit", "weight_0": "100", "weight_1": "invalid_unit"},
        )
        assert response.status_code == 200  # Returns to form
        content = response.content.decode()
        assert "errorlist" in content  # Django admin error list class
        assert "weight" in content  # Field with error

        # Test invalid magnitude
        response = admin_client.post(
            reverse("admin:example_integerpintfieldsavemodel_add"),
            data={"name": "Invalid Magnitude", "weight_0": "not_a_number", "weight_1": "gram"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "errorlist" in content
        assert "weight" in content


class TestReadOnlyAdmin:
    """Test ReadOnlyEditing admin class."""

    def test_readonly_all_fields(self, site):
        """Test that all fields are readonly in edit mode."""
        model = HayBale.objects.create(
            name="Test Hay",
            weight_int=ureg.Quantity(1000, "gram"),
            weight_decimal=ureg.Quantity(Decimal("1000.50"), "gram"),
        )

        admin_class = ReadOnlyEditing(HayBale, site)
        readonly_fields = admin_class.get_readonly_fields(None, obj=model)

        # All fields should be readonly when editing
        expected_fields = ["name", "weight_int", "weight_decimal"]
        assert all(field in readonly_fields for field in expected_fields)

        # Fields should not be readonly when adding
        assert not admin_class.get_readonly_fields(None, obj=None)


class TestWidgetComparison:
    """Test widget form functionality."""

    def test_widget_form_rendering(self, admin_client):
        """Test widget form renders with expected elements."""
        response = admin_client.get(reverse("admin:example_djangopintfieldwidgetcomparisonmodel_add"))
        assert response.status_code == 200
        content = response.content.decode()

        # Check for expected form elements
        assert "weight_int" in content
        assert "tabled_weight_int" in content
        assert "<table" in content

        # Verify unit choices
        assert all(unit in content for unit in ["gram", "kilogram", "pound"])

    def test_integer_widget_submission(self, admin_client):
        """Test integer field widgets in form submission."""
        data = {
            # Required fields with values
            "weight_int_0": "1000",
            "weight_int_1": "gram",
            "tabled_weight_int_0": "4000",
            "tabled_weight_int_1": "gram",
            # Other fields with defaults
            "weight_bigint_0": None,
            "weight_bigint_1": "gram",
            "weight_decimal_0": None,
            "weight_decimal_1": "gram",
            "tabled_weight_decimal_0": None,
            "tabled_weight_decimal_1": "gram",
            "tabled_weight_bigint_0": None,
            "tabled_weight_bigint_1": "gram",
        }

        # Filter out None values
        data = {k: v for k, v in data.items() if v is not None}

        response = admin_client.get(reverse("admin:example_djangopintfieldwidgetcomparisonmodel_changelist"))
        assert response.status_code == 200

        response = admin_client.post(
            reverse("admin:example_djangopintfieldwidgetcomparisonmodel_add"), data=data, follow=True
        )
        assert response.status_code == 200  # Follows redirect after success

    def test_decimal_widget_submission(self, admin_client):
        """Test decimal field widgets in form submission."""
        data = {
            # Required fields with values
            "weight_decimal_0": "3000.50",
            "weight_decimal_1": "gram",
            "tabled_weight_decimal_0": "6000.50",
            "tabled_weight_decimal_1": "gram",
            # Other fields with defaults
            "weight_int_0": None,
            "weight_int_1": "gram",
            "weight_bigint_0": None,
            "weight_bigint_1": "gram",
            "tabled_weight_int_0": None,
            "tabled_weight_int_1": "gram",
            "tabled_weight_bigint_0": None,
            "tabled_weight_bigint_1": "gram",
        }

        # Filter out None values
        data = {k: v for k, v in data.items() if v is not None}

        response = admin_client.get(reverse("admin:example_djangopintfieldwidgetcomparisonmodel_changelist"))
        assert response.status_code == 200

        response = admin_client.post(
            reverse("admin:example_djangopintfieldwidgetcomparisonmodel_add"), data=data, follow=True
        )
        assert response.status_code == 200  # Follows redirect after success
