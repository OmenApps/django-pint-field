"""Tests for bulk_update() and expression-based updates of Pint fields.

``bulk_update`` and conditional ``update(... = Case(When(...)))`` build query
expressions that arrive at ``Field.get_db_prep_save`` already resolved. The
field must pass those expressions through (their inner ``Value(Quantity)`` nodes
serialize on their own) rather than trying to coerce the expression itself into
a Quantity.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models import Case
from django.db.models import F
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Cast

from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import EmptyHayBaleDecimal
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestBulkUpdate:
    """bulk_update of Pint fields with Quantity values."""

    def test_decimal_bulk_update(self):
        """bulk_update writes the assigned Quantity values across rows."""
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        b = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("200"), ureg.gram), name="b")

        a.weight = Quantity(Decimal("90"), ureg.gram)
        b.weight = Quantity(Decimal("180"), ureg.gram)
        DecimalPintFieldSaveModel.objects.bulk_update([a, b], ["weight"])

        a.refresh_from_db()
        b.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("90"), ureg.gram)
        assert b.weight.quantity == Quantity(Decimal("180"), ureg.gram)

    def test_integer_bulk_update(self):
        """bulk_update works for IntegerPintField too."""
        a = IntegerPintFieldSaveModel.objects.create(weight=Quantity(100, ureg.gram), name="a")
        b = IntegerPintFieldSaveModel.objects.create(weight=Quantity(200, ureg.gram), name="b")

        a.weight = Quantity(90, ureg.gram)
        b.weight = Quantity(180, ureg.gram)
        IntegerPintFieldSaveModel.objects.bulk_update([a, b], ["weight"], batch_size=500)

        a.refresh_from_db()
        b.refresh_from_db()
        assert a.weight.quantity == Quantity(90, ureg.gram)
        assert b.weight.quantity == Quantity(180, ureg.gram)

    def test_bulk_update_preserves_cross_unit_value(self):
        """A value assigned in a non-default unit round-trips correctly."""
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        a.weight = Quantity(Decimal("1"), ureg.kilogram)  # 1000 gram
        DecimalPintFieldSaveModel.objects.bulk_update([a], ["weight"])

        a.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("1000"), ureg.gram)

    def test_bulk_update_mixed_units_across_rows(self):
        """Each row's value is converted independently within one bulk_update call."""
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        b = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="b")
        a.weight = Quantity(Decimal("500"), ureg.gram)
        b.weight = Quantity(Decimal("1"), ureg.kilogram)  # 1000 gram
        DecimalPintFieldSaveModel.objects.bulk_update([a, b], ["weight"])

        a.refresh_from_db()
        b.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("500"), ureg.gram)
        assert b.weight.quantity == Quantity(Decimal("1000"), ureg.gram)

    def test_bulk_update_null_value(self):
        """bulk_update can clear a nullable Pint field to None."""
        obj = EmptyHayBaleDecimal.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        obj.weight = None
        EmptyHayBaleDecimal.objects.bulk_update([obj], ["weight"])

        obj.refresh_from_db()
        assert obj.weight is None

    def test_conditional_update_with_cast_case_when(self):
        """update() with Case/When over Value(Quantity) is supported.

        A bare Case compiles to ``text``; PostgreSQL needs it cast to the
        composite type, so wrap it in ``Cast(..., output_field=field)`` - the
        same cast Django's own bulk_update applies.
        """
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        b = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("200"), ureg.gram), name="b")
        weight_field = DecimalPintFieldSaveModel._meta.get_field("weight")

        DecimalPintFieldSaveModel.objects.update(
            weight=Cast(
                Case(
                    When(name="a", then=Value(Quantity(Decimal("11"), ureg.gram))),
                    default=Value(Quantity(Decimal("22"), ureg.gram)),
                ),
                output_field=weight_field,
            )
        )

        a.refresh_from_db()
        b.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("11"), ureg.gram)
        assert b.weight.quantity == Quantity(Decimal("22"), ureg.gram)


@pytest.mark.django_db
class TestFArithmeticUnsupported:
    """F() arithmetic on the composite column is unsupported by design.

    The composite ``pint_field`` type has no scalar +/- operator, so arithmetic
    against it has no meaning. The field detects the CombinedExpression and
    raises a clear ValidationError instead of letting it fail as an opaque
    database operator error.
    """

    def test_decimal_f_arithmetic_raises_clear_error(self):
        """F('weight') - Quantity on a DecimalPintField raises a clear ValidationError."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        with pytest.raises(ValidationError, match="Arithmetic on a PintField is not supported"):
            DecimalPintFieldSaveModel.objects.update(weight=F("weight") - Quantity(Decimal("10"), ureg.gram))

    def test_integer_f_arithmetic_raises_clear_error(self):
        """The same clear error is raised for IntegerPintField (inherits the base guard)."""
        IntegerPintFieldSaveModel.objects.create(weight=Quantity(100, ureg.gram), name="a")
        with pytest.raises(ValidationError, match="Arithmetic on a PintField is not supported"):
            IntegerPintFieldSaveModel.objects.update(weight=F("weight") + Quantity(10, ureg.gram))

    def test_f_multiplication_also_rejected(self):
        """Multiplying the column by a scalar is arithmetic too, and rejected."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        with pytest.raises(ValidationError, match="Arithmetic on a PintField is not supported"):
            DecimalPintFieldSaveModel.objects.update(weight=F("weight") * 2)

    def test_plain_f_reference_is_not_blocked(self):
        """A bare F() column reference (no arithmetic) still works - we only block arithmetic."""
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        # Self-copy is a no-op but must compile and run without raising.
        DecimalPintFieldSaveModel.objects.update(weight=F("weight"))
        a.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("100"), ureg.gram)


@pytest.mark.django_db
class TestBulkUpdateReplacesFArithmetic:
    """bulk_update is the supported alternative to the unsupported F() arithmetic.

    The recommended pattern: fetch the rows, compute the new Quantity in Python,
    and write them back with bulk_update. These tests prove that pattern produces
    exactly the result the (unsupported) ``F('balance') - loss`` would have.
    """

    def test_subtract_loss_from_every_row(self):
        """Decrement every row by a fixed loss, the way a caller would replace F() - loss."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("100"), ureg.gram), name="a")
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("250"), ureg.gram), name="b")
        loss = Quantity(Decimal("10"), ureg.gram)

        objs = list(DecimalPintFieldSaveModel.objects.order_by("pk"))
        for obj in objs:
            obj.weight = obj.weight - loss  # proxy arithmetic returns a Quantity
        DecimalPintFieldSaveModel.objects.bulk_update(objs, ["weight"])

        result = {o.name: o.weight.quantity for o in DecimalPintFieldSaveModel.objects.all()}
        assert result["a"] == Quantity(Decimal("90"), ureg.gram)
        assert result["b"] == Quantity(Decimal("240"), ureg.gram)

    def test_subtract_cross_unit_loss(self):
        """The Python-side loss can be in a different unit than the stored value."""
        a = DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2"), ureg.kilogram), name="a")
        loss = Quantity(Decimal("500"), ureg.gram)  # 0.5 kg

        a.weight = a.weight - loss  # 2 kg - 500 g = 1500 g
        DecimalPintFieldSaveModel.objects.bulk_update([a], ["weight"])

        a.refresh_from_db()
        assert a.weight.quantity == Quantity(Decimal("1500"), ureg.gram)
