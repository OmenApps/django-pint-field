from decimal import Decimal

from django.test import SimpleTestCase
from rest_framework import serializers

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


def serializer_test_factory(Model, SerializerField, quantity):
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

    return DjangoPintFieldSerializerTest


IntegerPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleInteger, SerializerField=IntegerPintRestField, quantity=INTEGER_QUANTITY
)
BigIntegerPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleBigInteger, SerializerField=IntegerPintRestField, quantity=INTEGER_QUANTITY
)
DjangoPintFieldSerializerTest = serializer_test_factory(
    Model=EmptyHayBaleDecimal, SerializerField=DecimalPintRestField, quantity=DECIMAL_QUANTITY
)
