"""Tests for proxy/converter caching and typing metadata."""

import copy
import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest

from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestConverterCaching:
    """The field reuses a single converter instance."""

    def test_field_exposes_cached_converter(self):
        """The same converter object is returned on repeated access."""
        field = DecimalPintFieldSaveModel._meta.get_field("weight")
        first = field.get_cached_converter()
        second = field.get_cached_converter()
        assert first is second

    def test_from_db_value_uses_cached_converter(self):
        """Proxies loaded from the DB share the field's cached converter."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("500"), ureg.gram), name="x")
        obj = DecimalPintFieldSaveModel.objects.get(name="x")
        field = DecimalPintFieldSaveModel._meta.get_field("weight")
        proxy = obj.__dict__["weight"]  # raw stored proxy, not via descriptor
        assert proxy.converter is field.get_cached_converter()
        # Behavior unchanged
        assert proxy.quantity == Quantity(Decimal("500"), ureg.gram)

    def test_cached_converter_rebuilt_after_field_deepcopy(self):
        """A deepcopied field gets its own converter, not the original's.

        Django deepcopies field instances (model inheritance, migration state).
        The cache must rebind to the copy rather than keep the original's
        converter (which references the original field).
        """
        field = DecimalPintFieldSaveModel._meta.get_field("weight")
        original = field.get_cached_converter()
        copied = copy.deepcopy(field)
        copied_converter = copied.get_cached_converter()
        assert copied_converter is not original
        assert copied_converter.field is copied


@pytest.mark.django_db
class TestProxyIdentity:
    """A DB-loaded instance stores one proxy, so repeated access is stable."""

    def test_repeated_access_returns_same_proxy(self):
        """Two reads of a loaded obj.weight return the identical proxy object.

        ``from_db_value`` wraps the value once and stores it in the instance
        ``__dict__``; attribute access returns that stored object, so no proxy
        is rebuilt per access (no per-row reconstruction to optimize away).
        """
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("500"), ureg.gram), name="x")
        obj = DecimalPintFieldSaveModel.objects.get(name="x")
        first = obj.weight
        second = obj.weight
        assert first is second
        assert first.quantity == Quantity(Decimal("500"), ureg.gram)


def test_py_typed_marker_is_packaged():
    """The py.typed marker ships alongside the package source."""
    spec = importlib.util.find_spec("django_pint_field")
    package_dir = Path(spec.origin).parent
    assert (package_dir / "py.typed").exists()


def test_convert_to_unit_is_annotated():
    """PintFieldConverter.convert_to_unit advertises its return type."""
    from django_pint_field.helpers import PintFieldConverter

    hints = PintFieldConverter.convert_to_unit.__annotations__
    assert "return" in hints
