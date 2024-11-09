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
        # Check converted unit displays defined in list_display
        assert str(integer_model.weight.to("kilogram").magnitude) in content
        assert str(integer_model.weight.to("pound").magnitude)[:4] in content

    def test_readonly_fields(self, admin_client, integer_model):
        """Test readonly fields in change view."""
        response = admin_client.get(reverse("admin:example_integerpintfieldsavemodel_change", args=[integer_model.pk]))
        assert response.status_code == 200

        # In edit mode, fields should be editable
        content = response.content.decode()
        assert 'type="number"' in content
        assert "select" in content


class TestAdminFormHandling:
    """Test admin form submission handling."""

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "Test Add Integer",
                "weight_0": "500",
                "weight_1": "gram",
                "expected_grams": 500,
            },
            {
                "name": "Test Add Kilo",
                "weight_0": "2",
                "weight_1": "kilogram",
                "expected_grams": 2000,
            },
        ],
    )
    def test_add_integer_model(self, admin_client, data):
        """Test adding models with different units."""
        response = admin_client.post(reverse("admin:example_integerpintfieldsavemodel_add"), data=data)
        assert response.status_code == 302  # Successful redirect after save

        # Verify object was created
        model = IntegerPintFieldSaveModel.objects.get(name=data["name"])

        # Convert to base unit (gram) for comparison
        weight = ureg.Quantity(float(data["weight_0"]), data["weight_1"])
        weight_in_grams = weight.to("gram")

        assert weight_in_grams.magnitude == data["expected_grams"]
        assert str(model.weight.units) == data["weight_1"]  # Stored in unit specified in form

    def test_validation_errors(self, admin_client):
        """Test form validation errors."""
        # Test invalid unit
        response = admin_client.post(
            reverse("admin:example_integerpintfieldsavemodel_add"),
            data={"name": "Invalid Unit", "weight_0": "100", "weight_1": "invalid_unit"},
        )
        assert response.status_code == 200  # Returns to form
        assert "error" in response.content.decode().lower()

        # Test invalid magnitude
        response = admin_client.post(
            reverse("admin:example_integerpintfieldsavemodel_add"),
            data={"name": "Invalid Magnitude", "weight_0": "not_a_number", "weight_1": "gram"},
        )
        assert response.status_code == 200
        assert "error" in response.content.decode().lower()


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
        assert all(field in readonly_fields for field in ["name", "weight_int", "weight_decimal"])

        # Fields should not be readonly when adding
        assert not admin_class.get_readonly_fields(None, obj=None)


class TestWidgetComparison:
    """Test DjangoPintFieldWidgetComparisonAdmin functionality."""

    def test_widget_form(self, admin_client):
        """Test that the custom widget form renders correctly."""
        response = admin_client.get(reverse("admin:example_djangopintfieldwidgetcomparisonmodel_add"))
        assert response.status_code == 200
        content = response.content.decode()

        # Check for presence of both standard and tabled widgets
        assert "weight_int" in content
        assert "tabled_weight_int" in content
        assert "<table" in content  # Tabled widget should render a table

        # Verify unit choices are present
        for unit in ["gram", "kilogram", "pound"]:
            assert unit in content

    def test_widget_data_handling(self, admin_client):
        """Test that both widget types handle data correctly."""
        data = {
            "weight_int_0": 1000,
            "weight_int_1": "gram",
            "weight_bigint_0": 2000,
            "weight_bigint_1": "gram",
            "weight_decimal_0": Decimal("3000.50"),
            "weight_decimal_1": "gram",
            "tabled_weight_int_0": 4000,
            "tabled_weight_int_1": "gram",
            "tabled_weight_bigint_0": 5000,
            "tabled_weight_bigint_1": "gram",
            "tabled_weight_decimal_0": Decimal("6000.50"),
            "tabled_weight_decimal_1": "gram",
        }

        response = admin_client.post(reverse("admin:example_djangopintfieldwidgetcomparisonmodel_add"), data=data)

        # Form should be valid and save
        assert response.status_code == 302  # Redirect after successful save
