from collections import OrderedDict
from decimal import Decimal

from django.test import SimpleTestCase
from pint import UndefinedUnitError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django_pint_field.rest import DecimalPintRestField, IntegerPintRestField
from django_pint_field.units import ureg
from tests.dummyapp.models import (
    EmptyHayBaleBigInteger,
    EmptyHayBaleDecimal,
    EmptyHayBaleInteger,
)

Quantity = ureg.Quantity

INTEGER_QUANTITY = Quantity(1 * ureg.ounce)
DECIMAL_QUANTITY = Quantity(Decimal("1.0") * ureg.ounce)


def serializer_test_factory(Model, SerializerField, quantity, expected_representation):
    class DjangoPintFieldSerializerTest(SimpleTestCase):
        def test_blank_field(self):
            class DjangoPintFieldSerializer(serializers.ModelSerializer):
                weight = SerializerField()

                class Meta:
                    model = Model
                    fields = ["name", "weight"]

            data = {"name": "any"}
            with self.subTest(data):
                serializer = DjangoPintFieldSerializer(data=data)
                self.assertIs(serializer.is_valid(), False)
                self.assertEqual(
                    serializer.data,
                    {
                        "name": "any",
                    },
                )

        def test_quantity(self):
            class DjangoPintFieldSerializer(serializers.Serializer):
                weight = SerializerField()

            data = {"name": "any", "weight": quantity}
            serializer = DjangoPintFieldSerializer(data=data)
            self.assertIs(serializer.is_valid(), True)
            self.assertEqual(serializer.validated_data, OrderedDict([("weight", quantity)]))

        def test_empty_required(self):
            class DjangoPintFieldSerializer(serializers.Serializer):
                weight = SerializerField(allow_null=False)

            serializer = DjangoPintFieldSerializer(data={"name": "any", "weight": None})
            self.assertIs(serializer.is_valid(), False)
            self.assertEqual(serializer.validated_data, {})

        def test_empty_optional(self):
            class DjangoPintFieldSerializer(serializers.Serializer):
                weight = SerializerField(allow_null=True)

            serializer = DjangoPintFieldSerializer(data={"name": "any", "weight": None})
            self.assertIs(serializer.is_valid(), True)

        def test_good_data_serializer_to_internal_value(self):
            weight = SerializerField()
            internal_value = weight.to_internal_value(data="1 ounce")
            self.assertEqual(internal_value, quantity)

        def test_bad_data_units_serializer_to_internal_value(self):
            weight = SerializerField()
            with self.assertRaises(UndefinedUnitError):
                weight.to_internal_value(data="1 elephants")

        def test_bad_data_magnitude_serializer_to_internal_value(self):
            weight = SerializerField()
            with self.assertRaises(ValidationError):
                weight.to_internal_value(data="large ounce")

        def test_good_serializer_to_representation(self):
            weight = SerializerField()
            weight.to_representation(value=Quantity(Decimal("1.0"), ureg.ounce))
            representation = weight.to_representation(value=Quantity(quantity, ureg.ounce))
            self.assertEqual(representation, expected_representation)

        def test_bad_value_str_serializer_to_representation(self):
            weight = SerializerField()
            with self.assertRaises(ValidationError):
                weight.to_representation(value="string")

        def test_bad_value_int_serializer_to_representation(self):
            weight = SerializerField()
            with self.assertRaises(ValidationError):
                weight.to_representation(value=1)

    return DjangoPintFieldSerializerTest


IntegerPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleInteger,
    SerializerField=IntegerPintRestField,
    quantity=INTEGER_QUANTITY,
    expected_representation="1 ounce",
)
BigIntegerPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleBigInteger,
    SerializerField=IntegerPintRestField,
    quantity=INTEGER_QUANTITY,
    expected_representation="1 ounce",
)
DjangoPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleDecimal,
    SerializerField=DecimalPintRestField,
    quantity=DECIMAL_QUANTITY,
    expected_representation="Quantity(1.0 ounce)",
)
