"""Test cases for database constraints with PintFields."""

from decimal import Decimal

import pytest
from django.db import IntegrityError

from django_pint_field.units import ureg
from example_project.example.models import PintFieldWithCheckConstraint


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestPintFieldCheckConstraints:
    """Test CheckConstraint functionality with PintField and F expressions."""

    def test_valid_constraint_min_lte_max(self):
        """Test that valid data (min <= max) is accepted."""
        obj = PintFieldWithCheckConstraint.objects.create(
            name="Valid Range",
            min_weight=Quantity(Decimal("10.0"), "gram"),
            max_weight=Quantity(Decimal("100.0"), "gram"),
        )
        assert obj.id is not None
        assert obj.min_weight.magnitude == Decimal("10.0")
        assert obj.max_weight.magnitude == Decimal("100.0")

    def test_valid_constraint_min_equals_max(self):
        """Test that valid data (min == max) is accepted."""
        obj = PintFieldWithCheckConstraint.objects.create(
            name="Equal Range",
            min_weight=Quantity(Decimal("50.0"), "gram"),
            max_weight=Quantity(Decimal("50.0"), "gram"),
        )
        assert obj.id is not None
        assert obj.min_weight.magnitude == obj.max_weight.magnitude

    def test_invalid_constraint_min_gt_max(self):
        """Test that invalid data (min > max) is rejected."""
        with pytest.raises(IntegrityError, match="min_weight_lte_max_weight"):
            PintFieldWithCheckConstraint.objects.create(
                name="Invalid Range",
                min_weight=Quantity(Decimal("100.0"), "gram"),
                max_weight=Quantity(Decimal("10.0"), "gram"),
            )

    def test_constraint_with_different_units_same_dimensionality(self):
        """Test constraint works when comparing values with different units."""
        obj = PintFieldWithCheckConstraint.objects.create(
            name="Different Units",
            min_weight=Quantity(Decimal("1.0"), "gram"),
            max_weight=Quantity(Decimal("1.0"), "kilogram"),  # 1 kg = 1000 g
        )
        assert obj.id is not None
        # Both should be stored in default unit (gram) and 1g < 1000g

    def test_constraint_uses_comparator_field(self):
        """Test that constraint properly compares using comparator values."""
        # Create object with values in different units
        obj = PintFieldWithCheckConstraint.objects.create(
            name="Unit Conversion Test",
            min_weight=Quantity(Decimal("500.0"), "gram"),
            max_weight=Quantity(Decimal("1.0"), "kilogram"),
        )

        # Verify the constraint compared base units correctly
        # 500g < 1000g (1 kg converted to base units)
        assert obj.id is not None

    def test_default_values_respect_constraint(self):
        """Test that default values (0.0 and 1000.0) respect the constraint."""
        obj = PintFieldWithCheckConstraint.objects.create(name="Defaults")
        assert obj.id is not None
        # Note: Default values might be returned as plain Decimals or Quantities
        # depending on how they're stored. The important thing is they respect the constraint.
        # Refresh from database to get the actual stored values
        obj.refresh_from_db()
        assert obj.min_weight.magnitude == Decimal("0.0")
        assert obj.max_weight.magnitude == Decimal("1000.0")
