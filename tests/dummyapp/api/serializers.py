from rest_framework import serializers
from django_pint_field.rest import IntegerPintRestField, DecimalPintRestField

from tests.dummyapp.models import IntegerPintFieldSaveModel, BigIntegerPintFieldSaveModel, DecimalPintFieldSaveModel


class IntegerModelSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()

    class Meta:
        model = IntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields


class BigIntegerModelSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()

    class Meta:
        model = BigIntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields


class DecimalModelSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField()

    class Meta:
        model = DecimalPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields
