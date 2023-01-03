from decimal import Decimal
from django.db import models
from django.db.models import DecimalField

from django_pint_field.models import (
    IntegerPintField,
    BigIntegerPintField,
    DecimalPintField,
)


class FieldSaveModel(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)


class IntegerPintFieldSaveModel(FieldSaveModel):
    weight = IntegerPintField("gram")


class BigIntegerPintFieldSaveModel(FieldSaveModel):
    weight = BigIntegerPintField("gram")


class DecimalPintFieldSaveModel(FieldSaveModel):
    weight = DecimalPintField("gram", max_digits=5, decimal_places=2)


class HayBale(FieldSaveModel):
    name = models.CharField(max_length=20)
    weight_int = IntegerPintField("gram", blank=True, null=True)
    weight_bigint = BigIntegerPintField("gram", blank=True, null=True)
    weight_decimal = DecimalPintField("gram", blank=True, null=True, max_digits=10, decimal_places=2)


class EmptyHayBaleInteger(FieldSaveModel):
    name = models.CharField(max_length=20)
    weight = IntegerPintField("gram", null=True)


class EmptyHayBaleBigInteger(FieldSaveModel):
    name = models.CharField(max_length=20)
    weight = BigIntegerPintField("gram", null=True)


class EmptyHayBaleDecimal(FieldSaveModel):
    name = models.CharField(max_length=20)
    weight = DecimalPintField("gram", null=True, max_digits=10, decimal_places=2)
    # Value to compare with default implementation
    compare = DecimalField(max_digits=10, decimal_places=2, null=True)


class CustomUregHayBale(models.Model):
    # Custom is defined in settings in conftest.py
    custom_int = IntegerPintField("custom")
    custom_bigint = BigIntegerPintField("custom")
    custom_decimal = DecimalPintField("custom", max_digits=10, decimal_places=2)


class ChoicesDefinedInModel(models.Model):
    weight_int = IntegerPintField("kilogram", unit_choices=["kilogram", "milligram", "pounds"])
    weight_bigint = BigIntegerPintField("kilogram", unit_choices=["milligram", "kilogram", "pounds"])
    weight_decimal = DecimalPintField(
        "kilogram", unit_choices=["milligram", "pounds", "kilogram"], max_digits=10, decimal_places=2
    )


class DefaultsInModel(models.Model):
    name = models.CharField(max_length=20)
    weight_int = IntegerPintField("gram", blank=True, null=True, default=1)
    weight_bigint = BigIntegerPintField("gram", blank=True, null=True, default=1)
    weight_decimal = DecimalPintField(
        "gram", blank=True, null=True, max_digits=10, decimal_places=2, default=Decimal("1.0")
    )
