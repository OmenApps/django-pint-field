from django.db import models
from django.db.models import DecimalField

import quantityfield.fields
from quantityfield.fields import (
    BigIntegerQuantityField,
    DecimalQuantityField,
    IntegerQuantityField,
    QuantityField,
)


class FieldSaveModel(models.Model):
    name = models.CharField(max_length=20)
    weight = ...

    class Meta:
        abstract = True


class FloatFieldSaveModel(FieldSaveModel):
    weight = QuantityField("gram")


class IntFieldSaveModel(FieldSaveModel):
    weight = IntegerQuantityField("gram")


class BigIntFieldSaveModel(FieldSaveModel):
    weight = BigIntegerQuantityField("gram")


class DecimalFieldSaveModel(FieldSaveModel):
    weight = DecimalQuantityField("gram", max_digits=10, decimal_places=2)


class HayBale(models.Model):
    name = models.CharField(max_length=20)
    weight = QuantityField("gram")
    weight_int = IntegerQuantityField("gram", blank=True, null=True)
    weight_bigint = BigIntegerQuantityField("gram", blank=True, null=True)


class EmptyHayBaleFloat(models.Model):
    name = models.CharField(max_length=20)
    weight = QuantityField("gram", null=True)


class EmptyHayBaleInt(models.Model):
    name = models.CharField(max_length=20)
    weight = IntegerQuantityField("gram", null=True)


class EmptyHayBalePositiveInt(models.Model):
    name = models.CharField(max_length=20)
    weight = quantityfield.fields.PositiveIntegerQuantityField("gram", null=True)


class EmptyHayBaleBigInt(models.Model):
    name = models.CharField(max_length=20)
    weight = BigIntegerQuantityField("gram", null=True)


class EmptyHayBaleDecimal(models.Model):
    name = models.CharField(max_length=20)
    weight = DecimalQuantityField("gram", null=True, max_digits=10, decimal_places=2)
    # Value to compare with default implementation
    compare = DecimalField(max_digits=10, decimal_places=2, null=True)


class CustomUregHayBale(models.Model):
    # Custom is defined in settings in conftest.py
    custom = QuantityField("custom")
    custom_int = IntegerQuantityField("custom")
    custom_bigint = BigIntegerQuantityField("custom")


class CustomUregDecimalHayBale(models.Model):
    custom_decimal = DecimalQuantityField("custom", max_digits=10, decimal_places=2)


class ChoicesDefinedInModel(models.Model):
    weight = QuantityField("kilogram", unit_choices=["milligram", "pounds"])


class ChoicesDefinedInModelInt(models.Model):
    weight = IntegerQuantityField("kilogram", unit_choices=["milligram", "pounds"])
