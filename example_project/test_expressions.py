"""Tests for SQL-native Pint query expressions."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models import F

from django_pint_field.expressions import PintComparator
from django_pint_field.expressions import PintConvert
from django_pint_field.expressions import PintMagnitude
from django_pint_field.expressions import _affine_constants
from django_pint_field.units import ureg
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import EmptyHayBaleDecimal
from example_project.example.models import IntegerPintFieldSaveModel
from example_project.example.models import TemperatureReadingModel


Quantity = ureg.Quantity


@pytest.mark.django_db
class TestPintComparator:
    """Tests for the PintComparator accessor expression."""

    def test_comparator_annotation_returns_base_unit_magnitude(self):
        """Annotating with PintComparator exposes the base-unit (kilogram) magnitude."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("500"), ureg.gram), name="half-kilo")
        row = DecimalPintFieldSaveModel.objects.annotate(cmp=PintComparator("weight")).get()
        # 500 gram == 0.5 kilogram (the base unit)
        assert row.cmp == Decimal("0.5")


@pytest.mark.django_db
class TestPintMagnitude:
    """Tests for the PintMagnitude accessor expression."""

    def test_magnitude_annotation_returns_stored_magnitude(self):
        """Annotating with PintMagnitude exposes the original stored magnitude."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("500"), ureg.gram), name="half-kilo")
        row = DecimalPintFieldSaveModel.objects.annotate(mag=PintMagnitude("weight")).get()
        # The original magnitude was stored in grams
        assert row.mag == Decimal("500")


@pytest.mark.django_db
class TestPintConvert:
    """Tests for the PintConvert conversion expression."""

    def test_convert_grams_field_to_kilograms(self):
        """PintConvert returns the magnitude in the requested unit, computed in SQL."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2500"), ureg.gram), name="heavy")
        row = DecimalPintFieldSaveModel.objects.annotate(kg=PintConvert("weight", "kilogram")).get()
        assert row.kg == Decimal("2.5")

    def test_convert_grams_field_to_grams_is_identity(self):
        """Converting to the stored display unit returns the original magnitude."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2500"), ureg.gram), name="heavy")
        row = DecimalPintFieldSaveModel.objects.annotate(g=PintConvert("weight", "gram")).get()
        assert row.g == Decimal("2500")

    def test_accepts_f_expression_source(self):
        """A pre-built F() source produces the same result as the string shorthand."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2500"), ureg.gram), name="heavy")
        row = DecimalPintFieldSaveModel.objects.annotate(
            kg_str=PintConvert("weight", "kilogram"),
            kg_f=PintConvert(F("weight"), "kilogram"),
        ).get()
        assert row.kg_str == row.kg_f == Decimal("2.5")

    def test_empty_unit_raises_at_construction(self):
        """An empty/whitespace target unit fails fast rather than silently."""
        with pytest.raises(ValueError):
            PintConvert("weight", "")

    def test_undefined_unit_raises_at_construction(self):
        """A typo'd target unit fails at expression construction, not query time."""
        with pytest.raises(Exception):
            PintConvert("weight", "not_a_unit")


@pytest.mark.django_db
class TestPintConvertOffsetUnits:
    """Offset units (temperature) must convert correctly, not just linearly."""

    def test_kelvin_field_converts_to_celsius(self):
        """300 K stored == 26.85 °C, computed in SQL via the affine formula."""
        TemperatureReadingModel.objects.create(temperature=Quantity(Decimal("300"), ureg.kelvin), name="warm")
        row = TemperatureReadingModel.objects.annotate(c=PintConvert("temperature", "degC")).get()
        # 300 K - 273.15 = 26.85 °C
        assert abs(row.c - Decimal("26.85")) < Decimal("0.0001")

    def test_kelvin_field_converts_to_fahrenheit(self):
        """300 K stored == 80.33 °F."""
        TemperatureReadingModel.objects.create(temperature=Quantity(Decimal("300"), ureg.kelvin), name="warm")
        row = TemperatureReadingModel.objects.annotate(f=PintConvert("temperature", "degF")).get()
        assert abs(row.f - Decimal("80.33")) < Decimal("0.01")


@pytest.mark.django_db
class TestPintConvertQuerying:
    """PintConvert annotations support set-based filter/order in SQL."""

    @pytest.fixture
    def three_weights(self):
        """Create three rows: 1 g, 1000 g, 2500 g."""
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1"), ureg.gram), name="light")
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1000"), ureg.gram), name="mid")
        DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("2500"), ureg.gram), name="heavy")

    def test_filter_on_converted_annotation(self, three_weights):
        """Filter rows whose weight is >= 1 kilogram, computed in SQL."""
        names = set(
            DecimalPintFieldSaveModel.objects.annotate(kg=PintConvert("weight", "kilogram"))
            .filter(kg__gte=Decimal("1"))
            .values_list("name", flat=True)
        )
        assert names == {"mid", "heavy"}

    def test_order_by_converted_annotation(self, three_weights):
        """Order rows by the converted magnitude, descending."""
        ordered = list(
            DecimalPintFieldSaveModel.objects.annotate(kg=PintConvert("weight", "kilogram"))
            .order_by("-kg")
            .values_list("name", flat=True)
        )
        assert ordered == ["heavy", "mid", "light"]


@pytest.mark.django_db
class TestExpressionsWithIntegerField:
    """The expressions work against IntegerPintField, not only DecimalPintField."""

    def test_integer_field_conversion_and_accessors(self):
        """Integer-backed magnitudes coerce cleanly at the SQL boundary."""
        IntegerPintFieldSaveModel.objects.create(weight=Quantity(500, ureg.gram), name="int-row")
        row = IntegerPintFieldSaveModel.objects.annotate(
            kg=PintConvert("weight", "kilogram"),
            cmp=PintComparator("weight"),
            mag=PintMagnitude("weight"),
        ).get()
        assert row.kg == Decimal("0.5")
        assert row.cmp == Decimal("0.5")
        assert row.mag == 500


@pytest.mark.django_db
class TestExpressionsNullPropagation:
    """A NULL composite field propagates to Python None through every expression."""

    def test_comparator_null_field_returns_none(self):
        """PintComparator on a NULL field yields None."""
        EmptyHayBaleDecimal.objects.create(name="null-row", weight=None)
        row = EmptyHayBaleDecimal.objects.annotate(cmp=PintComparator("weight")).get()
        assert row.cmp is None

    def test_convert_null_field_returns_none(self):
        """PintConvert on a NULL field yields None."""
        EmptyHayBaleDecimal.objects.create(name="null-row", weight=None)
        row = EmptyHayBaleDecimal.objects.annotate(kg=PintConvert("weight", "kilogram")).get()
        assert row.kg is None


@pytest.mark.django_db
def test_convert_dimensionally_incompatible_unit_raises():
    """Converting a field to a dimensionally-incompatible unit raises at resolve time."""
    DecimalPintFieldSaveModel.objects.create(weight=Quantity(Decimal("1000"), ureg.gram), name="x")
    with pytest.raises(ValidationError):
        list(DecimalPintFieldSaveModel.objects.annotate(bad=PintConvert("weight", "meter")))


@pytest.mark.django_db
def test_convert_temperature_field_to_mass_unit_raises():
    """Dimensional validation also fires for offset-unit (temperature) fields."""
    TemperatureReadingModel.objects.create(temperature=Quantity(Decimal("300"), ureg.kelvin), name="warm")
    with pytest.raises(ValidationError):
        list(TemperatureReadingModel.objects.annotate(bad=PintConvert("temperature", "kilogram")))


def test_affine_constants_multiplicative_unit():
    """A multiplicative unit yields b == 0 and m == the base-unit factor."""
    b, m = _affine_constants("gram")
    assert b == Decimal("0")
    assert m == Decimal("0.001")  # 1 gram == 0.001 kilogram


def test_affine_constants_offset_unit_celsius():
    """An offset unit yields a non-zero b (the zero-point shift)."""
    b, m = _affine_constants("degC")
    assert b == Decimal("273.15")
    assert m == Decimal("1")


def test_expressions_are_exported_from_package_root():
    """The new expressions are importable from the package root."""
    import django_pint_field

    assert hasattr(django_pint_field, "PintConvert")
    assert hasattr(django_pint_field, "PintComparator")
    assert hasattr(django_pint_field, "PintMagnitude")
