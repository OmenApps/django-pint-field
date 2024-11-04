"""Models for testing django_pint_field."""

from decimal import Decimal

from django.db import models
from django.db.models import DecimalField

from django_pint_field.models import BigIntegerPintField
from django_pint_field.models import DecimalPintField
from django_pint_field.models import IntegerPintField


unit_choices_list = ["kilogram", "milligram", "pounds"]


class FieldSaveModel(models.Model):
    """Abstract model for testing django_pint_field."""

    name = models.CharField(max_length=20)

    objects = models.Manager()

    class Meta:
        """Meta class for FieldSaveModel."""

        abstract = True

    def __str__(self):
        return str(self.name)


class IntegerPintFieldSaveModel(FieldSaveModel):
    """Model for testing IntegerPintField."""

    weight = IntegerPintField(default_unit="gram")


class BigIntegerPintFieldSaveModel(FieldSaveModel):
    """Model for testing BigIntegerPintField."""

    weight = BigIntegerPintField(default_unit="gram")


class DecimalPintFieldSaveModel(FieldSaveModel):
    """Model for testing DecimalPintField."""

    weight = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2)


class HayBale(FieldSaveModel):
    """Model for testing IntegerPintField, BigIntegerPintField, and DecimalPintField."""

    name = models.CharField(max_length=20)
    weight_int = IntegerPintField(default_unit="gram", blank=True, null=True)
    weight_bigint = BigIntegerPintField(default_unit="gram", blank=True, null=True)
    weight_decimal = DecimalPintField(default_unit="gram", blank=True, null=True, max_digits=10, decimal_places=2)


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
    weight = DecimalPintField(default_unit="gram", null=True, max_digits=10, decimal_places=2)
    # Value to compare with default implementation
    compare = DecimalField(max_digits=10, decimal_places=2, null=True)


class CustomUregHayBale(models.Model):
    """Model for testing custom ureg."""

    # Custom is defined in settings in conftest.py
    custom_int = IntegerPintField(default_unit="custom")
    custom_bigint = BigIntegerPintField(default_unit="custom")
    custom_decimal = DecimalPintField(default_unit="custom", max_digits=10, decimal_places=2)


class ChoicesDefinedInModel(models.Model):
    """Model for testing choices defined in model."""

    weight_int = IntegerPintField(default_unit="kilogram", unit_choices=unit_choices_list)
    weight_bigint = BigIntegerPintField(default_unit="kilogram", unit_choices=unit_choices_list)
    weight_decimal = DecimalPintField(
        default_unit="kilogram",
        unit_choices=unit_choices_list,
        max_digits=10,
        decimal_places=2,
    )


class DefaultsInModel(models.Model):
    """Model for testing default values defined in model."""

    name = models.CharField(max_length=20)
    weight_int = IntegerPintField(default_unit="gram", blank=True, null=True, default=1)
    weight_bigint = BigIntegerPintField(default_unit="gram", blank=True, null=True, default=1)
    weight_decimal = DecimalPintField(
        default_unit="gram", blank=True, null=True, max_digits=10, decimal_places=2, default=Decimal("1.0")
    )


class IntegerPintFieldCachedModel(FieldSaveModel):
    """Model for testing IntegerPintField with cached value."""

    weight = IntegerPintField(default_unit="gram")


class BigIntegerPintFieldCachedModel(FieldSaveModel):
    """Model for testing BigIntegerPintField with cached value."""

    weight = BigIntegerPintField(default_unit="gram")


class DecimalPintFieldCachedModel(FieldSaveModel):
    """Model for testing DecimalPintField with cached value."""

    weight = DecimalPintField(default_unit="gram", max_digits=5, decimal_places=2)


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
        max_digits=10,
        decimal_places=2,
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
        max_digits=10,
        decimal_places=2,
        unit_choices=unit_choices_list,
    )
