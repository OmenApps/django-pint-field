import logging
from decimal import Decimal
from typing import Type

from django.test import TestCase

from django_pint_field.units import ureg
from tests.dummyapp.models import (
    BigIntegerPintFieldCachedModel,
    DecimalPintFieldCachedModel,
    FieldSaveModel,
    IntegerPintFieldCachedModel,
)

logger = logging.getLogger("django_pint_field")


Quantity = ureg.Quantity


class FieldCacheTestBase:
    MODEL: Type[FieldSaveModel]
    EXPECTED_TYPE: Type = float
    DEFAULT_WEIGHT = 100
    DEFAULT_WEIGHT_STR = "100.0"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.0 gram"
    HEAVIEST = 1000
    LIGHTEST = 1
    OUNCE_VALUE = 3.52739619496
    COMPARE_QUANTITY = Quantity(0.8 * ureg.ounce)  # 1 ounce = 28.34 grams
    WEIGHT = Quantity(2 * ureg.gram)

    def setUp(self):
        if self.EXPECTED_TYPE == Decimal:
            self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.DEFAULT_WEIGHT)) * ureg.gram),
                name="grams",
            )
            self.lightest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.LIGHTEST)) * ureg.gram),
                name="lightest",
            )
            self.heaviest = self.MODEL.objects.create(
                weight=Quantity(Decimal(str(self.HEAVIEST)) * ureg.gram),
                name="heaviest",
            )
        else:
            self.MODEL.objects.create(
                weight=Quantity(self.DEFAULT_WEIGHT * ureg.gram),
                name="grams",
            )
            self.lightest = self.MODEL.objects.create(
                weight=Quantity(self.LIGHTEST * ureg.gram),
                name="lightest",
            )
            self.heaviest = self.MODEL.objects.create(
                weight=Quantity(self.HEAVIEST * ureg.gram),
                name="heaviest",
            )

    def tearDown(self):
        self.MODEL.objects.all().delete()

    def test_value_stored_as_correct_count(self):
        count = self.MODEL.objects.all().count()
        self.assertEqual(count, 3)

    def test_value_stored_as_correct_magnitude_type(self):
        units = self.MODEL.objects.first().weight.units
        self.assertEqual(units, "gram")


class TestDecimalFieldSave(FieldCacheTestBase, TestCase):
    MODEL = DecimalPintFieldCachedModel
    EXPECTED_TYPE = Decimal
    DEFAULT_WEIGHT = "100.00"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.00 gram"
    OUNCES = Decimal("10") * ureg.ounce
    OUNCE_VALUE = Decimal("3.52739619496")
    OUNCES_IN_GRAM = Decimal("283.50")
    WEIGHT = Quantity(Decimal("2") * ureg.gram)


class IntLikeFieldSaveTestBase(FieldCacheTestBase):
    DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
    EXPECTED_TYPE = int
    # 1 ounce = 28.34 grams -> we use something that can be stored as int
    COMPARE_QUANTITY = Quantity(Decimal(str(28 * 1000)) * ureg.milligram)


class TestIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    MODEL = IntegerPintFieldCachedModel


class TestBigIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    MODEL = BigIntegerPintFieldCachedModel
