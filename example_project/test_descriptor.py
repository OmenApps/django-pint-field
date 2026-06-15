"""Tests for PintField attribute access via the descriptor.

Focus: attribute-style unit conversion (``obj.field.unit``) must work
consistently on UNSAVED instances, not only on rows loaded from the database.
Also guards the descriptor's interaction with Django machinery that the change
touches: assignment, deferred loading (.only()/.defer()), refresh_from_db,
save round-trips, pickling, and None handling.
"""

import copy
import pickle
from decimal import Decimal

import pytest

from django_pint_field.helpers import PintFieldProxy
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import HayBale
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


class TestUnsavedAttributeAccess:
    """An unsaved instance exposes the same proxy API as a loaded one."""

    def test_unsaved_integer_instance_returns_proxy(self):
        """Building (not saving) an IntegerPintField instance yields a proxy."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert isinstance(obj.weight, PintFieldProxy)

    def test_unsaved_integer_attribute_conversion(self):
        """obj.field.unit converts on an unsaved IntegerPintField instance."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert obj.weight.kilogram.magnitude == Decimal("1")
        assert str(obj.weight.kilogram.units) == "kilogram"

    def test_unsaved_decimal_attribute_conversion(self):
        """obj.field.unit converts on an unsaved DecimalPintField instance."""
        obj = DecimalPintFieldSaveModel(name="u", weight=Quantity(Decimal("1000"), "gram"))
        assert isinstance(obj.weight, PintFieldProxy)
        assert obj.weight.kilogram.magnitude == Decimal("1")

    def test_unsaved_magnitude_and_units_still_work(self):
        """Raw .magnitude/.units access keeps working on an unsaved instance."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert obj.weight.magnitude == 1000
        assert str(obj.weight.units) == "gram"

    def test_unsaved_comparison_and_math(self):
        """Comparisons and arithmetic work against the unsaved proxy."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert obj.weight == Quantity(1000, "gram")
        assert obj.weight < Quantity(2, "kilogram")
        assert (obj.weight + Quantity(500, "gram")) == Quantity(1500, "gram")

    def test_unsaved_double_underscore_property_still_works(self):
        """The class-level ``field__unit`` property keeps working unsaved."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert obj.weight__kilogram == Quantity(1, "kilogram")

    def test_repeated_unsaved_access_returns_same_proxy(self):
        """Two reads of an unsaved obj.weight return the identical proxy."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1000, "gram"))
        assert obj.weight is obj.weight


class TestAssignmentSemantics:
    """Direct assignment is wrapped once and never double-wrapped."""

    def test_assigning_quantity_wraps_in_proxy(self):
        """Assigning a Quantity after construction still yields a proxy."""
        obj = IntegerPintFieldSaveModel(name="u", weight=Quantity(1, "gram"))
        obj.weight = Quantity(2000, "gram")
        assert isinstance(obj.weight, PintFieldProxy)
        assert obj.weight.kilogram.magnitude == Decimal("2")

    def test_assigning_a_proxy_does_not_double_wrap(self):
        """Assigning an existing proxy stores a single, un-nested proxy."""
        source = IntegerPintFieldSaveModel(name="s", weight=Quantity(1000, "gram"))
        proxy = source.weight
        assert isinstance(proxy, PintFieldProxy)

        target = IntegerPintFieldSaveModel(name="t", weight=Quantity(1, "gram"))
        target.weight = proxy
        assert isinstance(target.weight, PintFieldProxy)
        # The wrapped value is a Quantity, not another proxy.
        assert isinstance(target.weight.quantity, Quantity)
        assert not isinstance(target.weight.quantity, PintFieldProxy)


@pytest.mark.django_db
class TestNoneHandling:
    """Nullable fields round-trip None cleanly through the descriptor."""

    def test_unsaved_none_stays_none(self):
        """Assigning None to a nullable field reads back as None."""
        obj = HayBale(name="n", weight_int=None, weight_decimal=None)
        assert obj.weight_int is None
        assert obj.weight_decimal is None

    def test_saved_none_loads_as_none(self):
        """A persisted NULL loads back as None, not a proxy wrapping None."""
        HayBale.objects.create(name="n", weight_int=None, weight_decimal=None)
        obj = HayBale.objects.get(name="n")
        assert obj.weight_int is None
        assert obj.weight_decimal is None


@pytest.mark.django_db
class TestPersistenceRoundTrips:
    """Saving and reloading keeps the proxy API working (risk areas)."""

    def test_save_then_access_unsaved_then_loaded(self):
        """An instance built in Python saves and reloads with a working proxy."""
        obj = DecimalPintFieldSaveModel(name="r", weight=Quantity(Decimal("1000"), "gram"))
        # Works before save:
        assert obj.weight.kilogram.magnitude == Decimal("1")
        obj.save()
        # Works after save (same in-memory instance):
        assert obj.weight.kilogram.magnitude == Decimal("1")
        # Works after reload:
        loaded = DecimalPintFieldSaveModel.objects.get(name="r")
        assert isinstance(loaded.weight, PintFieldProxy)
        assert loaded.weight.kilogram.magnitude == Decimal("1")

    def test_refresh_from_db_returns_working_proxy(self):
        """refresh_from_db repopulates the field with a usable proxy."""
        obj = DecimalPintFieldSaveModel.objects.create(name="rf", weight=Quantity(Decimal("1000"), "gram"))
        obj.refresh_from_db()
        assert isinstance(obj.weight, PintFieldProxy)
        assert obj.weight.kilogram.magnitude == Decimal("1")

    def test_deferred_field_lazy_loads_proxy(self):
        """A field excluded via .only() lazy-loads into a working proxy.

        This exercises Django's DeferredAttribute path, which the descriptor
        must preserve.
        """
        DecimalPintFieldSaveModel.objects.create(name="df", weight=Quantity(Decimal("1000"), "gram"))
        obj = DecimalPintFieldSaveModel.objects.only("name").get(name="df")
        # Accessing the deferred field triggers a DB load:
        assert isinstance(obj.weight, PintFieldProxy)
        assert obj.weight.kilogram.magnitude == Decimal("1")

    def test_defer_field_lazy_loads_proxy(self):
        """A field excluded via .defer() lazy-loads into a working proxy."""
        DecimalPintFieldSaveModel.objects.create(name="dd", weight=Quantity(Decimal("1000"), "gram"))
        obj = DecimalPintFieldSaveModel.objects.defer("weight").get(name="dd")
        assert isinstance(obj.weight, PintFieldProxy)
        assert obj.weight.kilogram.magnitude == Decimal("1")


class TestSerialization:
    """The proxy survives pickling/deepcopy from an unsaved instance."""

    def test_deepcopy_unsaved_instance_keeps_proxy(self):
        """Deep-copying an unsaved instance preserves the working proxy."""
        obj = IntegerPintFieldSaveModel(name="c", weight=Quantity(1000, "gram"))
        clone = copy.deepcopy(obj)
        assert isinstance(clone.weight, PintFieldProxy)
        assert clone.weight.kilogram.magnitude == Decimal("1")

    def test_pickle_unsaved_instance_keeps_proxy(self):
        """Pickling an unsaved instance preserves the working proxy.

        Pickle round-trip of test-created data only (Django's cache backends
        pickle model instances, so the proxy must stay pickle-friendly).
        """
        obj = IntegerPintFieldSaveModel(name="p", weight=Quantity(1000, "gram"))
        restored = pickle.loads(pickle.dumps(obj))  # noqa: S301 - trusted, test-created
        assert isinstance(restored.weight, PintFieldProxy)
        assert restored.weight.kilogram.magnitude == Decimal("1")


def test_class_level_access_does_not_return_field_value():
    """Accessing the attribute on the class returns the descriptor itself.

    Field introspection must still go through ``_meta.get_field``.
    """
    from django_pint_field.models import IntegerPintField

    descriptor = IntegerPintFieldSaveModel.__dict__["weight"]
    assert hasattr(descriptor, "__get__")
    assert hasattr(descriptor, "__set__")
    assert isinstance(IntegerPintFieldSaveModel._meta.get_field("weight"), IntegerPintField)
