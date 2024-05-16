from rest_framework import serializers

from django_pint_field.rest import DecimalPintRestField, IntegerPintRestField
from tests.demoapp.models import (
    BigIntegerPintFieldSaveModel,
    DecimalPintFieldSaveModel,
    IntegerPintFieldSaveModel,
)


class IntegerModelSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()

    class Meta:
        model = IntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        return data


class BigIntegerModelSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()

    class Meta:
        model = BigIntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        return data


class DecimalModelSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField()

    class Meta:
        model = DecimalPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        return data
