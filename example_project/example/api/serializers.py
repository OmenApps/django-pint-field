"""Serializers for the example app."""

from rest_framework import serializers

from django_pint_field.rest import DecimalPintRestField
from django_pint_field.rest import IntegerPintRestField
from django_pint_field.rest import PintRestField
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


class GeneralIntegerModelSerializer(serializers.ModelSerializer):
    """Serializer for IntegerPintFieldSaveModel."""

    weight = PintRestField()

    class Meta:
        """Meta class for IntegerModelSerializer using PintRestField."""

        model = IntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields



class IntegerModelSerializer(serializers.ModelSerializer):
    """Serializer for IntegerPintFieldSaveModel."""

    weight = IntegerPintRestField()

    class Meta:
        """Meta class for IntegerModelSerializer."""

        model = IntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields


class BigIntegerModelSerializer(serializers.ModelSerializer):
    """Serializer for BigIntegerPintFieldSaveModel."""

    weight = IntegerPintRestField()

    class Meta:
        """Meta class for BigIntegerModelSerializer."""

        model = BigIntegerPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields


class DecimalModelSerializer(serializers.ModelSerializer):
    """Serializer for DecimalPintFieldSaveModel."""

    weight = DecimalPintRestField()

    class Meta:
        """Meta class for DecimalModelSerializer."""

        model = DecimalPintFieldSaveModel

        fields = (
            "id",
            "weight",
        )
        read_only_fields = fields
