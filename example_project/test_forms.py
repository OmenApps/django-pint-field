"""Test cases for forms in the example project."""

import json
import warnings
from decimal import Decimal
from typing import Type

import pytest
from django.core.exceptions import ValidationError
from django.core.serializers import deserialize
from django.core.serializers import serialize
from django.core.validators import EMPTY_VALUES
from django.db import transaction
from django.db.models import Field
from django.db.models import Model
from django.test import TestCase
from pint import UnitRegistry
from pint.errors import DimensionalityError
from pint.errors import UndefinedUnitError

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintCount
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintMin
from django_pint_field.aggregates import PintStdDev
from django_pint_field.aggregates import PintSum
from django_pint_field.aggregates import PintVariance
from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.models import BigIntegerPintField
from django_pint_field.models import DecimalPintField
from django_pint_field.models import IntegerPintField
from django_pint_field.units import ureg
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import CustomUregHayBale
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import DefaultsInModel
from example_project.example.models import EmptyHayBaleBigInteger
from example_project.example.models import EmptyHayBaleDecimal
from example_project.example.models import EmptyHayBaleInteger
from example_project.example.models import FieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


Quantity = ureg.Quantity


class DecimalPintFieldTests(TestCase):
    """Tests for the DecimalPintField."""

    def test_to_python(self):
        """Test the to_python method."""
        default_decimal_text = "1234.1234"
        default_decimal_value = Decimal(default_decimal_text)
        default_quantity = ureg.Quantity(default_decimal_value * ureg.gram)
        bad_quantity = ureg.Quantity(Decimal(1234.1234) * ureg.gram)

        field = DecimalPintField(
            default_unit="gram",
            default=default_decimal_value,
            unit_choices=["ounce", "gram", "pound", "kilogram"],
            max_digits=10,
            decimal_places=6,
        )

        # Verify to_python works with a good Quantity input value
        self.assertEqual(field.to_python(default_quantity), ureg.Quantity(Decimal("1.2341234") * ureg.kilogram))

        # When Decimal is initialized as a float, it is unable to accurately store the exact value
        self.assertLess(field.to_python(bad_quantity), ureg.Quantity(Decimal("1.2341234") * ureg.kilogram))

        # Check what happens when a Decimal is provided. Should use the Decimal and the default_unit
        self.assertEqual(field.to_python(default_decimal_value), default_quantity)

        # Check what happens when a decimal string is provided. Should convert to Decimal and use the default_unit
        self.assertEqual(field.to_python(default_decimal_text), default_quantity)

        # Check what happens when a decimal string is provided. Should convert to Decimal and use the default_unit
        self.assertEqual(field.to_python("gram"), ureg.Quantity("gram"))

    def test_invaid_registry_value_for_default(self):
        """Test that an invalid registry value for the default raises an error."""
        field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
        tests = [
            "non-registry string",
        ]
        for value in tests:
            with self.subTest(value):
                with self.assertRaises(UndefinedUnitError):
                    field.clean(value, None)

    def test_blank_value(self):
        """Test that a blank value raises an error."""
        field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
        msg = "This field cannot be null."
        for value in (None,):
            with self.subTest(value):
                with self.assertRaisesMessage(ValidationError, msg):
                    field.clean(value, None)

    def test_null_value(self):
        """Test that a null value raises an error."""
        field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
        msg = "This field cannot be blank."
        for value in ([], (), {}):
            with self.subTest(value):
                with self.assertRaisesMessage(ValidationError, msg):
                    field.clean(value, None)

    # def test_invalid_value(self):
    #     field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
    #     msg = "Value must be a Quantity."
    #     tests = [
    #         1,  # ToDo: These should raise ValidationError
    #         1.1,
    #         set(),
    #         object(),
    #         complex(),
    #         b"non-numeric byte-string",
    #     ]
    #     for value in tests:
    #         print(f"Value: {value}")
    #         with self.subTest(value):
    #             with self.assertRaisesMessage(ValidationError, msg):
    #                 field.clean(value, None)

    def test_get_prep_value(self):
        """Test the get_prep_value method."""
        quantity = ureg.Quantity(Decimal("1234.1234") * ureg.gram)
        quantity_list = [quantity, quantity]
        field = DecimalPintField(
            default_unit="ounce",
            default=Decimal("1.23456789"),
            unit_choices=["ounce", "gram", "pound", "kilogram"],
            max_digits=10,
            decimal_places=6,
        )
        self.assertIsNone(field.get_prep_value(None))
        self.assertEqual(str(field.get_prep_value(quantity)), "(1.2341234::decimal, 1234.1234::decimal, 'gram'::text)")


class BaseMixinTestFieldCreate:
    """Base mixin for testing the creation of a field."""

    # The field that needs to be tested
    FIELD: Type[Field]
    # Some fields, i.e. the decimal require default kwargs to work properly
    DEFAULT_KWARGS = {}

    def test_sets_units(self):
        """Test that the default unit is set correctly."""
        test_grams = self.FIELD(default_unit="gram", **self.DEFAULT_KWARGS)
        self.assertEqual(test_grams.default_unit, ureg.gram)

    def test_fails_with_unknown_units(self):
        """Test that default unit must be a valid unit."""
        with self.assertRaises(UndefinedUnitError):
            test_crazy_units = self.FIELD(default_unit="zinghie", **self.DEFAULT_KWARGS)  # noqa: F841

    def test_unit_choices_must_be_valid_units(self):
        """Test that unit choices must be valid units."""
        with self.assertRaises(UndefinedUnitError):
            self.FIELD(default_unit="mile", unit_choices=["gunzu"], **self.DEFAULT_KWARGS)

    def test_unit_choices_must_match_base_dimensionality(self):
        """Test that unit choices must match the base dimensionality of the default unit."""
        with self.assertRaises(DimensionalityError):
            self.FIELD(default_unit="gram", unit_choices=["meter", "ounces"], **self.DEFAULT_KWARGS)

    def test_default_unit_is_required(self):
        """Test that the default unit is required."""
        with self.assertRaises(TypeError):
            no_units = self.FIELD(**self.DEFAULT_KWARGS)  # noqa: F841

    def test_default_unit_set_with_name(self):
        """Test that the default unit can be set with a string."""
        okay_units = self.FIELD(default_unit="meter", **self.DEFAULT_KWARGS)  # noqa: F841

    def test_default_unit_are_invalid(self):
        """Test that default units must be valid units."""
        with self.assertRaises(ValueError):
            wrong_units = self.FIELD(default_unit=None, **self.DEFAULT_KWARGS)  # noqa: F841


class TestIntegerFieldCreate(BaseMixinTestFieldCreate, TestCase):
    """Test the creation of an IntegerPintField."""

    FIELD = IntegerPintField


class TestBigIntegerFieldCreate(BaseMixinTestFieldCreate, TestCase):
    """Test the creation of a BigIntegerPintField."""

    FIELD = BigIntegerPintField


class TestDecimalFieldCreate(BaseMixinTestFieldCreate, TestCase):
    """Test the creation of a DecimalPintField."""

    FIELD = DecimalPintField
    DEFAULT_KWARGS = {"max_digits": 10, "decimal_places": 2}


@pytest.mark.parametrize(
    "max_digits, decimal_places, error",
    [
        (
            None,
            None,
            "Invalid initialization for DecimalPintField(.*?)None(.*?)None",
        ),
        (
            10,
            None,
            "Invalid initialization for DecimalPintField(.*?)10(.*?)None",
        ),
        (
            None,
            2,
            "Invalid initialization for DecimalPintField(.*?)None(.*?)2",
        ),
        (-1, 2, "Invalid initialization for DecimalPintField(.*?)-1(.*?)2(.*?)not valid parameters"),
        (2, -1, "Invalid initialization for DecimalPintField(.*?)2(.*?)-1(.*?)not valid parameters"),
        (2, 3, "Invalid initialization for DecimalPintField(.*?)2(.*?)3(.*?)not valid parameters"),
    ],
)
def test_decimal_init_fail(max_digits, decimal_places, error):
    """Test that the DecimalPintField fails with invalid parameters."""
    with pytest.raises(ValueError, match=error):
        DecimalPintField(default_unit="meter", max_digits=max_digits, decimal_places=decimal_places)


@pytest.mark.parametrize("max_digits, decimal_places", [(2, 0), (2, 2), (1, 0)])
def decimal_init_success(max_digits, decimal_places):
    DecimalPintField(default_unit="meter", max_digits=max_digits, decimal_places=decimal_places)


@pytest.mark.django_db
class TestCustomUreg(TestCase):
    """Test the custom unit registry."""

    def setUp(self):
        """Set up the test."""
        # Custom Values are defined in confest.py
        CustomUregHayBale.objects.create(
            custom_int=5 * ureg.custom,
            custom_bigint=5 * ureg.custom,
            custom_decimal=Decimal("5") * ureg.custom,
        )
        CustomUregHayBale.objects.create(
            custom_int=5 * ureg.kilocustom,
            custom_bigint=5 * ureg.kilocustom,
            custom_decimal=Decimal("5") * ureg.kilocustom,
        )

    def tearDown(self):
        """Tear down the test."""
        CustomUregHayBale.objects.all().delete()

    def test_custom_ureg_int(self):
        """Test the custom unit registry with an integer."""
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_int, ureg.Quantity)
        self.assertEqual(str(obj.custom_int), "5 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_int.to_root_units()), "5000 custom")

    def test_custom_ureg_bigint(self):
        """Test the custom unit registry with a big integer."""
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_bigint, ureg.Quantity)
        self.assertEqual(str(obj.custom_bigint), "5 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_bigint.to_root_units()), "5000 custom")

    def test_custom_ureg_decimal(self):
        """Test the custom unit registry with a decimal."""
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_decimal, ureg.Quantity)
        self.assertEqual(str(obj.custom_decimal), "5.00 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_decimal.to_root_units()), "5000.00 custom")


class BaseMixinNullAble:
    """Base mixin for testing nullable fields."""

    EMPTY_MODEL: Type[Model]
    FLOAT_SET_STR = "707.7"
    FLOAT_SET = Decimal(FLOAT_SET_STR)  # ToDo: NEED WORK HERE
    DB_FLOAT_VALUE_EXPECTED = 707.7

    def setUp(self):
        """Set up the test."""
        self.EMPTY_MODEL.objects.create(name="Empty")

    def tearDown(self) -> None:
        """Tear down the test."""
        self.EMPTY_MODEL.objects.all().delete()

    def test_accepts_assigned_null(self):
        """Test that the field accepts a null value."""
        new = self.EMPTY_MODEL()
        new.weight = None
        new.name = "Test"
        new.save()
        self.assertIsNone(new.weight)
        # Also get it from database to verify
        from_db = self.EMPTY_MODEL.objects.last()
        self.assertIsNone(from_db.weight)

    def test_accepts_auto_null(self):
        """Test that the field accepts an auto null value."""
        empty = self.EMPTY_MODEL.objects.first()
        self.assertIsNone(empty.weight, None)

    def test_accepts_default_pint_unit(self):
        """Test that the field accepts a default pint unit."""
        new = self.EMPTY_MODEL(name="DefaultPintUnitTest")
        units = UnitRegistry()
        new.weight = 5 * units.kilogram
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "DefaultPintUnitTest")
        self.assertEqual(str(obj.weight.to_root_units().units), "gram")
        self.assertEqual(obj.weight.to_root_units().magnitude, 5000)

    def test_accepts_default_app_unit(self):
        """Test that the field accepts a default app unit."""
        new = self.EMPTY_MODEL(name="DefaultAppUnitTest")
        new.weight = 5 * ureg.kilogram
        # Make sure that the correct argument does not raise a warning
        with warnings.catch_warnings(record=True) as w:
            new.save()
        assert len(w) == 0
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "DefaultAppUnitTest")
        self.assertEqual(obj.weight.to_root_units().units, "gram")
        self.assertEqual(obj.weight.to_root_units().magnitude, 5000)

    def test_accepts_assigned_whole_number_quantity(self):
        """Test that the field accepts a whole number quantity."""
        new = self.EMPTY_MODEL(name="WholeNumber")
        new.weight = Quantity(707 * ureg.gram)
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "WholeNumber")
        self.assertEqual(obj.weight.units, "gram")
        self.assertEqual(obj.weight.magnitude, 707)

    def test_accepts_assigned_float_number_quantity(self):
        """Test that the field accepts a float number quantity."""
        new = self.EMPTY_MODEL(name="FloatNumber")
        new.weight = Quantity(self.FLOAT_SET * ureg.gram)
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "FloatNumber")
        self.assertEqual(obj.weight.units, "gram")
        # We expect the database to deliver the correct type, at least
        # for postgresql this is true
        self.assertEqual(obj.weight.magnitude, self.DB_FLOAT_VALUE_EXPECTED)
        self.assertIsInstance(obj.weight.magnitude, type(self.DB_FLOAT_VALUE_EXPECTED))

    def test_serialisation(self):
        """Test that the field serializes correctly."""
        serialized = serialize(
            "json",
            [
                self.EMPTY_MODEL.objects.first(),
            ],
        )
        deserialized = json.loads(serialized)
        obj = deserialized[0]["fields"]
        self.assertEqual(obj["name"], "Empty")
        self.assertIsNone(obj["weight"])
        obj_generator = deserialize("json", serialized, ignorenonexistent=True)
        obj_back = next(obj_generator)
        self.assertEqual(obj_back.object.name, "Empty")
        self.assertIsNone(obj_back.object.weight)


@pytest.mark.django_db
class TestNullableInteger(BaseMixinNullAble, TestCase):
    """Test the nullable integer field."""

    EMPTY_MODEL = EmptyHayBaleInteger
    DB_FLOAT_VALUE_EXPECTED = int(BaseMixinNullAble.FLOAT_SET)


@pytest.mark.django_db
class TestNullableBigInteger(BaseMixinNullAble, TestCase):
    """Test the nullable big integer field."""

    EMPTY_MODEL = EmptyHayBaleBigInteger
    DB_FLOAT_VALUE_EXPECTED = int(BaseMixinNullAble.FLOAT_SET)


@pytest.mark.django_db
class TestNullableDecimal(BaseMixinNullAble, TestCase):
    """Test the nullable decimal field."""

    EMPTY_MODEL = EmptyHayBaleDecimal
    DB_FLOAT_VALUE_EXPECTED = Decimal(BaseMixinNullAble.FLOAT_SET_STR)

    def test_with_default_implementation(self):
        """Test the field with the default implementation."""
        new = self.EMPTY_MODEL(name="FloatNumber")
        new.weight = Quantity(self.FLOAT_SET * ureg.gram)
        new.compare = self.FLOAT_SET
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "FloatNumber")
        self.assertEqual(obj.weight.units, "gram")
        # We compare with the reference implementation of django, this should
        # be always true no matter which database is used
        self.assertEqual(obj.weight.magnitude, obj.compare)
        self.assertIsInstance(obj.weight.magnitude, type(obj.compare))
        # We also expect (at least for postgresql) that this a Decimal
        self.assertEqual(obj.weight.magnitude, self.DB_FLOAT_VALUE_EXPECTED)
        self.assertIsInstance(obj.weight.magnitude, Decimal)


class FieldSaveTestBase:
    """Base class for testing the saving of a field."""

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
        """Set up the test."""
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
        """Tear down the test."""
        self.MODEL.objects.all().delete()

    def test_fails_with_incompatible_units(self):
        """Test that the field fails with incompatible units."""
        # we have to wrap this in a transaction
        # fixing a unit test problem
        # http://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        metres = Quantity(100 * ureg.meter)
        with transaction.atomic():
            with self.assertRaises(DimensionalityError):
                self.MODEL.objects.create(weight=metres, name="Should Fail")

    def test_value_stored_as_quantity(self):
        """Test that the value is stored as a quantity."""
        obj = self.MODEL.objects.first()
        self.assertIsInstance(obj.weight, Quantity)
        self.assertEqual(str(obj.weight), self.DEFAULT_WEIGHT_QUANTITY_STR)

    def test_value_stored_as_correct_magnitude_type(self):
        """Test that the value is stored as the correct magnitude type."""
        obj = self.MODEL.objects.first()
        self.assertIsInstance(obj.weight, Quantity)
        self.assertIsInstance(obj.weight.magnitude, self.EXPECTED_TYPE)

    def test_value_conversion(self):
        """Test that the value is converted correctly."""
        obj = self.MODEL.objects.first()
        ounces = obj.weight.to(ureg.ounce)
        # self.assertAlmostEqual(ounces.magnitude, self.OUNCE_VALUE)
        self.assertEqual(ounces.units, ureg.ounce)

    def test_order_by(self):
        """Test that the objects are ordered by weight."""
        qs = list(self.MODEL.objects.all().order_by("weight"))
        self.assertEqual(qs[0].name, "lightest")
        self.assertEqual(qs[-1].name, "heaviest")
        self.assertEqual(qs[0], self.lightest)
        self.assertEqual(qs[-1], self.heaviest)

    def test_serialisation(self):
        """Test that the field serializes correctly."""
        serialized = serialize(
            "json",
            [
                self.MODEL.objects.first(),
            ],
        )
        deserialized = json.loads(serialized)
        obj = deserialized[0]["fields"]
        self.assertEqual(obj["weight"], self.DEFAULT_WEIGHT_QUANTITY_STR)


class TestDecimalFieldSave(FieldSaveTestBase, TestCase):
    """Test the saving of a decimal field."""

    MODEL = DecimalPintFieldSaveModel
    EXPECTED_TYPE = Decimal
    DEFAULT_WEIGHT = "100.00"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.00 gram"
    OUNCES = Decimal("10") * ureg.ounce
    OUNCE_VALUE = Decimal("3.52739619496")
    OUNCES_IN_GRAM = Decimal("283.50")
    WEIGHT = Quantity(Decimal("2") * ureg.gram)


class IntLikeFieldSaveTestBase(FieldSaveTestBase):
    """Base class for testing the saving of an integer-like field."""

    DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
    EXPECTED_TYPE = int
    # 1 ounce = 28.34 grams -> we use something that can be stored as int
    COMPARE_QUANTITY = Quantity(Decimal(str(28 * 1000)) * ureg.milligram)


class TestIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    """Test the saving of an integer field."""

    MODEL = IntegerPintFieldSaveModel


class TestBigIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    """Test the saving of a big integer field."""

    MODEL = BigIntegerPintFieldSaveModel


@pytest.mark.django_db
class TestDefaults(TestCase):
    """Test the defaults."""

    def setUp(self):
        """Set up the test."""
        # Default Values can be used in models
        DefaultsInModel.objects.create(
            weight_int=5 * ureg.gram,
            weight_bigint=5 * ureg.gram,
            weight_decimal=Decimal("5") * ureg.gram,
        )

    def tearDown(self):
        """Tear down the test."""
        DefaultsInModel.objects.all().delete()

    def test_defaults_int(self):
        """Test the defaults with an integer."""
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_int, ureg.Quantity)
        self.assertEqual(str(obj.weight_int), "5 gram")

    def test_defaults_bigint(self):
        """Test the defaults with a big integer."""
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_bigint, ureg.Quantity)
        self.assertEqual(str(obj.weight_bigint), "5 gram")

    def test_defaults_decimal(self):
        """Test the defaults with a decimal."""
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_decimal, ureg.Quantity)
        self.assertEqual(str(obj.weight_decimal), "5.00 gram")


class FieldUpdateTestBase:
    """Base class for testing the updating of a field."""

    MODEL: Type[FieldSaveModel]
    EXPECTED_TYPE: Type = int
    DEFAULT_WEIGHT = Quantity(2 * ureg.gram)
    DEFAULT_WEIGHT_QUANTITY_STR = "2 gram"
    NEW_WEIGHT = Quantity(2 * ureg.ounce)
    NEW_WEIGHT_QUANTITY_STR = "2 ounce"

    def setUp(self):
        """Set up the test."""
        self.MODEL.objects.create(
            weight=self.DEFAULT_WEIGHT,
            name="grams",
        )

    def tearDown(self):
        """Tear down the test."""
        self.MODEL.objects.all().delete()

    def test_value_updated(self):
        """Test that the value is updated."""
        obj = self.MODEL.objects.first()
        self.assertEqual(str(obj.weight), self.DEFAULT_WEIGHT_QUANTITY_STR)

        new_weight = self.NEW_WEIGHT
        obj.weight = new_weight
        obj.save(
            update_fields=[
                "weight",
            ]
        )

        self.assertIsInstance(obj.weight, Quantity)
        self.assertEqual(str(obj.weight), self.NEW_WEIGHT_QUANTITY_STR)

        obj.refresh_from_db()
        self.assertIsInstance(obj.weight, Quantity)
        self.assertEqual(str(obj.weight), self.NEW_WEIGHT_QUANTITY_STR)


class TestDecimalFieldUpdate(FieldUpdateTestBase, TestCase):
    """Test the updating of a decimal field."""

    MODEL = DecimalPintFieldSaveModel
    EXPECTED_TYPE = Decimal
    DEFAULT_WEIGHT = Quantity(Decimal("2.00") * ureg.gram)
    DEFAULT_WEIGHT_QUANTITY_STR = "2.00 gram"
    NEW_WEIGHT = Quantity(Decimal("2.00") * ureg.ounce)
    NEW_WEIGHT_QUANTITY_STR = "2.00 ounce"


class TestIntFieldUpdate(FieldUpdateTestBase, TestCase):
    """Test the updating of an integer field."""

    MODEL = IntegerPintFieldSaveModel


class TestBigIntFieldUpdate(FieldUpdateTestBase, TestCase):
    """Test the updating of a big integer field."""

    MODEL = BigIntegerPintFieldSaveModel
