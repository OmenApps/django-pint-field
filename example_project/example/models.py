"""Models for testing django_pint_field."""

from decimal import Decimal

from django.db import models
from django.db.models import DecimalField
from django.db.models import F
from django.db.models import Q

from django_pint_field.indexes import PintFieldComparatorIndex
from django_pint_field.models import BigIntegerPintField
from django_pint_field.models import DecimalPintField
from django_pint_field.models import IntegerPintField


unit_choices_list = ["kilogram", "milligram", "pound"]
unit_choices_tuple = ("kilogram", "milligram", "pound")
unit_choices_nested_list = [["kilogram", "kilogram"], ["milligram", "milligram"], ["pound", "pound"]]
unit_choices_nested_tuple = (("kilogram", "kilogram"), ("milligram", "milligram"), ("pound", "pound"))


class FieldSaveModel(models.Model):
    """Abstract model for testing django_pint_field."""

    name = models.CharField(max_length=20)

    objects = models.Manager()

    class Meta:
        """Meta class for FieldSaveModel."""

        abstract = True

    def __str__(self):
        """Return the name of the model."""
        return str(self.name)


class IntegerPintFieldSaveModel(FieldSaveModel):
    """Model for testing IntegerPintField."""

    weight = IntegerPintField(default_unit="gram")

    def __str__(self):
        return self.get_weight_display("~#P")


class IntegerPintFieldSaveWithIndexModel(FieldSaveModel):
    """Model for testing IntegerPintField."""

    weight = IntegerPintField(default_unit="gram")
    weight_two = IntegerPintField(default_unit="kilogram")

    def __str__(self):
        return self.get_weight_display("~#P")

    class Meta:
        """Meta class for IntegerPintFieldSaveWithIndexModel."""

        indexes = [
            PintFieldComparatorIndex(fields=["weight"], name="weight_idx"),
            PintFieldComparatorIndex(fields=["weight", "weight_two"], name="weight_weight_two_idx"),
        ]


class BigIntegerPintFieldSaveModel(FieldSaveModel):
    """Model for testing BigIntegerPintField."""

    weight = BigIntegerPintField(default_unit="gram")

    def __str__(self):
        return self.get_weight_display("~#P")


class DecimalPintFieldSaveModel(FieldSaveModel):
    """Model for testing DecimalPintField."""

    weight = DecimalPintField(default_unit="gram", display_decimal_places=2)

    def __str__(self):
        return self.get_weight_display("~#P")


class HayBale(FieldSaveModel):
    """Model for testing IntegerPintField, BigIntegerPintField, and DecimalPintField."""

    name = models.CharField(max_length=20)
    weight_int = IntegerPintField(default_unit="gram", blank=True, null=True)
    weight_bigint = BigIntegerPintField(default_unit="gram", blank=True, null=True)
    weight_decimal = DecimalPintField(default_unit="gram", blank=True, null=True, display_decimal_places=2)

    def __str__(self):
        return self.get_weight_int_display("~#P")


class EmptyHayBaleInteger(FieldSaveModel):
    """Model for testing IntegerPintField."""

    name = models.CharField(max_length=20)
    weight = IntegerPintField(default_unit="gram", null=True)


class EmptyHayBaleBigInteger(FieldSaveModel):
    """Model for testing BigIntegerPintField."""

    name = models.CharField(max_length=20)
    weight = BigIntegerPintField(default_unit="gram", null=True)


class EmptyHayBaleDecimal(FieldSaveModel):
    """Model for testing DecimalPintField."""

    name = models.CharField(max_length=20)
    weight = DecimalPintField(default_unit="gram", null=True, display_decimal_places=2)
    # Value to compare with default implementation
    compare = DecimalField(max_digits=10, decimal_places=2, null=True)


class CustomUregHayBale(models.Model):
    """Model for testing custom ureg."""

    # Custom is defined in settings in conftest.py
    custom_int = IntegerPintField(default_unit="custom")
    custom_bigint = BigIntegerPintField(default_unit="custom")
    custom_decimal = DecimalPintField(default_unit="custom", display_decimal_places=2)


class ChoicesDefinedInModel(models.Model):
    """Model for testing choices defined in model."""

    weight_int = IntegerPintField(default_unit="kilogram", unit_choices=unit_choices_list)
    weight_bigint = BigIntegerPintField(default_unit="kilogram", unit_choices=unit_choices_list)
    weight_decimal = DecimalPintField(
        default_unit="kilogram",
        unit_choices=unit_choices_list,
        display_decimal_places=2,
    )


class DefaultsInModel(models.Model):
    """Model for testing default values defined in model."""

    name = models.CharField(max_length=20)
    weight_int = IntegerPintField(default_unit="gram", blank=True, null=True, default=1)
    weight_bigint = BigIntegerPintField(default_unit="gram", blank=True, null=True, default=1)
    weight_decimal = DecimalPintField(
        default_unit="gram", blank=True, null=True, display_decimal_places=2, default=Decimal("1.0")
    )


class IntegerPintFieldCachalotModel(FieldSaveModel):
    """Model for testing IntegerPintField with value cached by django-cachalot."""

    weight = IntegerPintField(default_unit="gram")


class BigIntegerPintFieldCachalotModel(FieldSaveModel):
    """Model for testing BigIntegerPintField with value cached by django-cachalot."""

    weight = BigIntegerPintField(default_unit="gram")


class DecimalPintFieldCachalotModel(FieldSaveModel):
    """Model for testing DecimalPintField with value cached by django-cachalot."""

    weight = DecimalPintField(default_unit="gram", display_decimal_places=2)


class IntegerPintFieldCachopsModel(FieldSaveModel):
    """Model for testing IntegerPintField with value cached by django-cachops."""

    weight = IntegerPintField(default_unit="gram")


class BigIntegerPintFieldCacheopsModel(FieldSaveModel):
    """Model for testing BigIntegerPintField with value cached by django-cacheops."""

    weight = BigIntegerPintField(default_unit="gram")


class DecimalPintFieldCacheopsModel(FieldSaveModel):
    """Model for testing DecimalPintField with value cached by django-cacheops."""

    weight = DecimalPintField(default_unit="gram", display_decimal_places=2)


class DjangoPintFieldWidgetComparisonModel(models.Model):
    """Model for testing DjangoPintFieldWidgetComparison."""

    weight_int = IntegerPintField(
        default_unit="gram",
        blank=True,
        null=True,
        unit_choices=unit_choices_list,
    )
    weight_bigint = BigIntegerPintField(
        default_unit="gram",
        blank=True,
        null=True,
        unit_choices=unit_choices_list,
    )
    weight_decimal = DecimalPintField(
        default_unit="gram",
        blank=True,
        null=True,
        display_decimal_places=2,
        unit_choices=unit_choices_list,
    )
    tabled_weight_int = IntegerPintField(
        default_unit="gram",
        blank=True,
        null=True,
        unit_choices=unit_choices_list,
    )
    tabled_weight_bigint = BigIntegerPintField(
        default_unit="gram",
        blank=True,
        null=True,
        unit_choices=unit_choices_list,
    )
    tabled_weight_decimal = DecimalPintField(
        default_unit="gram",
        blank=True,
        null=True,
        display_decimal_places=2,
        unit_choices=unit_choices_list,
    )


class DjangoPintFieldUnitChoicesComparrisonModel(models.Model):
    """Model for testing unit_choices as list/tuple/nested list/nested tuple for each field type."""

    weight_int_list = IntegerPintField(default_unit="gram", unit_choices=unit_choices_list)
    weight_int_tuple = IntegerPintField(default_unit="gram", unit_choices=unit_choices_tuple)
    weight_int_nested_list = IntegerPintField(default_unit="gram", unit_choices=unit_choices_nested_list)
    weight_int_nested_tuple = IntegerPintField(default_unit="gram", unit_choices=unit_choices_nested_tuple)

    weight_bigint_list = BigIntegerPintField(default_unit="gram", unit_choices=unit_choices_list)
    weight_bigint_tuple = BigIntegerPintField(default_unit="gram", unit_choices=unit_choices_tuple)
    weight_bigint_nested_list = BigIntegerPintField(default_unit="gram", unit_choices=unit_choices_nested_list)
    weight_bigint_nested_tuple = BigIntegerPintField(default_unit="gram", unit_choices=unit_choices_nested_tuple)

    weight_decimal_list = DecimalPintField(default_unit="gram", unit_choices=unit_choices_list)
    weight_decimal_tuple = DecimalPintField(default_unit="gram", unit_choices=unit_choices_tuple)
    weight_decimal_nested_list = DecimalPintField(default_unit="gram", unit_choices=unit_choices_nested_list)
    weight_decimal_nested_tuple = DecimalPintField(default_unit="gram", unit_choices=unit_choices_nested_tuple)


class PintFieldWithCheckConstraint(models.Model):
    """Model for testing CheckConstraint with PintField and F expressions."""

    name = models.CharField(max_length=50)
    min_weight = DecimalPintField(
        default_unit="gram",
        default=Decimal("0.0"),
        display_decimal_places=2,
    )
    max_weight = DecimalPintField(
        default_unit="gram",
        default=Decimal("1000.0"),
        display_decimal_places=2,
    )

    class Meta:
        """Meta class with check constraint."""

        constraints = [
            models.CheckConstraint(
                check=Q(min_weight__lte=F("max_weight")),
                name="min_weight_lte_max_weight",
            ),
        ]
