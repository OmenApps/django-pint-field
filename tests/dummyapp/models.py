from django.db import models
from django.db.models import DecimalField

import django_pint_field.fields
from django_pint_field.fields import (
    BigIntegerPintField,
    DecimalPintField,
    IntegerPintField,
    PintField,
    XYZPintField,
)


class FieldSaveModel(models.Model):
    name = models.CharField(max_length=20)
    weight = ...

    class Meta:
        abstract = True


class FloatFieldSaveModel(FieldSaveModel):
    weight = PintField("gram")


class IntFieldSaveModel(FieldSaveModel):
    weight = IntegerPintField("gram")


class XYZIntFieldSaveModel(FieldSaveModel):
    weight = XYZPintField("gram", unit_choices=["pound", "ounce"])


class BigIntFieldSaveModel(FieldSaveModel):
    weight = BigIntegerPintField("gram")


class DecimalFieldSaveModel(FieldSaveModel):
    weight = DecimalPintField("gram", max_digits=10, decimal_places=2)


class HayBale(models.Model):
    name = models.CharField(max_length=20)
    weight = PintField("gram")
    weight_int = IntegerPintField("gram", blank=True, null=True)
    weight_bigint = BigIntegerPintField("gram", blank=True, null=True)


class EmptyHayBaleFloat(models.Model):
    name = models.CharField(max_length=20)
    weight = PintField("gram", null=True)


class EmptyHayBaleInt(models.Model):
    name = models.CharField(max_length=20)
    weight = IntegerPintField("gram", null=True)


class EmptyHayBalePositiveInt(models.Model):
    name = models.CharField(max_length=20)
    weight = django_pint_field.fields.PositiveIntegerPintField("gram", null=True)


class EmptyHayBaleBigInt(models.Model):
    name = models.CharField(max_length=20)
    weight = BigIntegerPintField("gram", null=True)


class EmptyHayBaleDecimal(models.Model):
    name = models.CharField(max_length=20)
    weight = DecimalPintField("gram", null=True, max_digits=10, decimal_places=2)
    # Value to compare with default implementation
    compare = DecimalField(max_digits=10, decimal_places=2, null=True)


class CustomUregHayBale(models.Model):
    # Custom is defined in settings in conftest.py
    custom = PintField("custom")
    custom_int = IntegerPintField("custom")
    custom_bigint = BigIntegerPintField("custom")


class CustomUregDecimalHayBale(models.Model):
    custom_decimal = DecimalPintField("custom", max_digits=10, decimal_places=2)


class ChoicesDefinedInModel(models.Model):
    weight = PintField("kilogram", unit_choices=["milligram", "pounds"])


class ChoicesDefinedInModelInt(models.Model):
    weight = IntegerPintField("kilogram", unit_choices=["milligram", "pounds"])
