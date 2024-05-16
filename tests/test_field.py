import json
import warnings
from decimal import Decimal
from typing import Type

import pytest
from django.core.exceptions import ValidationError
from django.core.serializers import deserialize, serialize
from django.db import transaction
from django.db.models import Field, Model
from django.test import TestCase
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError

from django_pint_field.aggregates import (
    PintAvg,
    PintCount,
    PintMax,
    PintMin,
    PintStdDev,
    PintSum,
    PintVariance,
)
from django_pint_field.exceptions import PintFieldLookupError
from django_pint_field.models import (
    BigIntegerPintField,
    DecimalPintField,
    IntegerPintField,
)
from django_pint_field.units import ureg
from tests.demoapp.models import (
    BigIntegerPintFieldSaveModel,
    CustomUregHayBale,
    DecimalPintFieldSaveModel,
    DefaultsInModel,
    EmptyHayBaleBigInteger,
    EmptyHayBaleDecimal,
    EmptyHayBaleInteger,
    FieldSaveModel,
    IntegerPintFieldSaveModel,
)

Quantity = ureg.Quantity


class DecimalPintFieldTests(TestCase):
    def test_to_python(self):
        default_decimal_text = "1234.1234"
        default_decimal_value = Decimal(default_decimal_text)
        default_quantity = ureg.Quantity(default_decimal_value * ureg.gram)
        bad_quantity = ureg.Quantity(Decimal(1234.1234) * ureg.gram)

        field = DecimalPintField(
            "gram",
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
        field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
        tests = [
            "non-registry string",
        ]
        for value in tests:
            with self.subTest(value):
                with self.assertRaises(UndefinedUnitError):
                    field.clean(value, None)

    def test_empty_and_invalid_value(self):
        field = DecimalPintField(default_unit="gram", max_digits=4, decimal_places=2)
        msg = "This field cannot be blank."
        tests = [
            # 1,  # ToDo: These should raise ValidationError
            # 1.1,
            (),
            # [],
            {},
            set(),
            object(),
            complex(),
            b"non-numeric byte-string",
        ]
        for value in tests:
            with self.subTest(value):
                with self.assertRaisesMessage(ValidationError, msg):
                    field.clean(value, None)

    def test_get_prep_value(self):
        quantity = ureg.Quantity(Decimal("1234.1234") * ureg.gram)
        quantity_list = [quantity, quantity]
        field = DecimalPintField(
            "ounce",
            default=Decimal("1.23456789"),
            unit_choices=["ounce", "gram", "pound", "kilogram"],
            max_digits=10,
            decimal_places=6,
        )
        self.assertIsNone(field.get_prep_value(None))
        self.assertEqual(str(field.get_prep_value(quantity)), "(1.2341234::decimal, 1234.1234::decimal, 'gram'::text)")


class BaseMixinTestFieldCreate:
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
    FIELD = IntegerPintField


class TestBigIntegerFieldCreate(BaseMixinTestFieldCreate, TestCase):
    FIELD = BigIntegerPintField


class TestDecimalFieldCreate(BaseMixinTestFieldCreate, TestCase):
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
    with pytest.raises(ValueError, match=error):
        DecimalPintField("meter", max_digits=max_digits, decimal_places=decimal_places)


@pytest.mark.parametrize("max_digits, decimal_places", [(2, 0), (2, 2), (1, 0)])
def decimal_init_success(max_digits, decimal_places):
    DecimalPintField("meter", max_digits=max_digits, decimal_places=decimal_places)


@pytest.mark.django_db
class TestCustomUreg(TestCase):
    def setUp(self):
        # Custom Values are fined in confest.py
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
        CustomUregHayBale.objects.all().delete()

    def test_custom_ureg_int(self):
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_int, ureg.Quantity)
        self.assertEqual(str(obj.custom_int), "5 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_int.to_root_units()), "5000 custom")

    def test_custom_ureg_bigint(self):
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_bigint, ureg.Quantity)
        self.assertEqual(str(obj.custom_bigint), "5 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_bigint.to_root_units()), "5000 custom")

    def test_custom_ureg_decimal(self):
        obj = CustomUregHayBale.objects.first()
        self.assertIsInstance(obj.custom_decimal, ureg.Quantity)
        self.assertEqual(str(obj.custom_decimal), "5.00 custom")

        obj = CustomUregHayBale.objects.last()
        self.assertEqual(str(obj.custom_decimal.to_root_units()), "5000.00 custom")


class BaseMixinNullAble:
    EMPTY_MODEL: Type[Model]
    FLOAT_SET_STR = "707.7"
    FLOAT_SET = Decimal(FLOAT_SET_STR)  # ToDo: NEED WORK HERE
    DB_FLOAT_VALUE_EXPECTED = 707.7

    def setUp(self):
        self.EMPTY_MODEL.objects.create(name="Empty")

    def tearDown(self) -> None:
        self.EMPTY_MODEL.objects.all().delete()

    def test_accepts_assigned_null(self):
        new = self.EMPTY_MODEL()
        new.weight = None
        new.name = "Test"
        new.save()
        self.assertIsNone(new.weight)
        # Also get it from database to verify
        from_db = self.EMPTY_MODEL.objects.last()
        self.assertIsNone(from_db.weight)

    def test_accepts_auto_null(self):
        empty = self.EMPTY_MODEL.objects.first()
        self.assertIsNone(empty.weight, None)

    def test_accepts_default_pint_unit(self):
        new = self.EMPTY_MODEL(name="DefaultPintUnitTest")
        units = UnitRegistry()
        new.weight = 5 * units.kilogram
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "DefaultPintUnitTest")
        self.assertEqual(str(obj.weight.to_root_units().units), "gram")
        self.assertEqual(obj.weight.to_root_units().magnitude, 5000)

    def test_accepts_default_app_unit(self):
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
        new = self.EMPTY_MODEL(name="WholeNumber")
        new.weight = Quantity(707 * ureg.gram)
        new.save()
        obj = self.EMPTY_MODEL.objects.last()
        self.assertEqual(obj.name, "WholeNumber")
        self.assertEqual(obj.weight.units, "gram")
        self.assertEqual(obj.weight.magnitude, 707)

    def test_accepts_assigned_float_number_quantity(self):
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
    EMPTY_MODEL = EmptyHayBaleInteger
    DB_FLOAT_VALUE_EXPECTED = int(BaseMixinNullAble.FLOAT_SET)


@pytest.mark.django_db
class TestNullableBigInteger(BaseMixinNullAble, TestCase):
    EMPTY_MODEL = EmptyHayBaleBigInteger
    DB_FLOAT_VALUE_EXPECTED = int(BaseMixinNullAble.FLOAT_SET)


@pytest.mark.django_db
class TestNullableDecimal(BaseMixinNullAble, TestCase):
    EMPTY_MODEL = EmptyHayBaleDecimal
    DB_FLOAT_VALUE_EXPECTED = Decimal(BaseMixinNullAble.FLOAT_SET_STR)

    def test_with_default_implementation(self):
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

    def test_fails_with_incompatible_units(self):
        # we have to wrap this in a transaction
        # fixing a unit test problem
        # http://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        metres = Quantity(100 * ureg.meter)
        with transaction.atomic():
            with self.assertRaises(DimensionalityError):
                self.MODEL.objects.create(weight=metres, name="Should Fail")

    def test_value_stored_as_quantity(self):
        obj = self.MODEL.objects.first()
        self.assertIsInstance(obj.weight, Quantity)
        self.assertEqual(str(obj.weight), self.DEFAULT_WEIGHT_QUANTITY_STR)

    def test_value_stored_as_correct_magnitude_type(self):
        obj = self.MODEL.objects.first()
        self.assertIsInstance(obj.weight, Quantity)
        self.assertIsInstance(obj.weight.magnitude, self.EXPECTED_TYPE)

    def test_value_conversion(self):
        obj = self.MODEL.objects.first()
        ounces = obj.weight.to(ureg.ounce)
        # self.assertAlmostEqual(ounces.magnitude, self.OUNCE_VALUE)
        self.assertEqual(ounces.units, ureg.ounce)

    def test_order_by(self):
        qs = list(self.MODEL.objects.all().order_by("weight"))
        self.assertEqual(qs[0].name, "lightest")
        self.assertEqual(qs[-1].name, "heaviest")
        self.assertEqual(qs[0], self.lightest)
        self.assertEqual(qs[-1], self.heaviest)

    def test_comparison_with_quantity(self):
        weight = Quantity(2 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__gt=weight)
        self.assertNotIn(self.lightest, qs)

    def test_serialisation(self):
        serialized = serialize(
            "json",
            [
                self.MODEL.objects.first(),
            ],
        )
        deserialized = json.loads(serialized)
        obj = deserialized[0]["fields"]
        self.assertEqual(obj["weight"], self.DEFAULT_WEIGHT_QUANTITY_STR)

    def test_comparison_with_quantity_gt(self):
        qs = self.MODEL.objects.filter(weight__gt=self.COMPARE_QUANTITY)
        self.assertNotIn(self.lightest, qs)

    def test_comparison_with_quantity_lt(self):
        qs = self.MODEL.objects.filter(weight__lt=self.COMPARE_QUANTITY)
        self.assertNotIn(self.heaviest, qs)

    def test_comparison_with_quantity_gte(self):
        qs = self.MODEL.objects.filter(weight__gte=self.COMPARE_QUANTITY)
        self.assertNotIn(self.lightest, qs)

    def test_comparison_with_quantity_lte(self):
        qs = self.MODEL.objects.filter(weight__lte=self.COMPARE_QUANTITY)
        self.assertNotIn(self.heaviest, qs)

    def test_comparison_with_quantity_isnull(self):
        qs = self.MODEL.objects.filter(weight__isnull=False)
        self.assertIn(self.lightest, qs)
        self.assertIn(self.heaviest, qs)

    def test_comparison_with_quantity_range(self):
        COMPARE_QUANTITY_2 = Quantity(2 * ureg.gram)
        qs = self.MODEL.objects.filter(weight__range=(self.COMPARE_QUANTITY, COMPARE_QUANTITY_2))
        self.assertNotIn(self.heaviest, qs)

    def test_comparison_with_invalid_lookup_contains(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__contains=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_icontains(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__icontains=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_in(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__in=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_startswith(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__startswith=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_istartswith(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__istartswith=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_endswith(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__endswith=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_iendswith(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__iendswith=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_date(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__date=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_year(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__year=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_iso_year(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__iso_year=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_month(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__month=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_day(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__day=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_week(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__week=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_week_day(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__week_day=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_iso_week_day(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__iso_week_day=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_quarter(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__quarter=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_time(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__time=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_hour(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__hour=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_minute(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__minute=self.COMPARE_QUANTITY)
            x.first()

    def test_comparison_with_invalid_lookup_second(self):
        with self.assertRaises(PintFieldLookupError):
            x = self.MODEL.objects.filter(weight__second=self.COMPARE_QUANTITY)
            x.first()

    def test_aggregate_avg(self):
        comparison = Quantity(Decimal("367.00000000000000000") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintAvg("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_count(self):
        comparison = 3
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintCount("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_max(self):
        comparison = Quantity(Decimal("1000") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMax("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_min(self):
        comparison = Quantity(Decimal("1.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintMin("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_sum(self):
        comparison = Quantity(Decimal("1101.00") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintSum("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_std_dev(self):
        comparison = Quantity(Decimal("449.41962573968662856") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintStdDev("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)

    def test_aggregate_variance(self):
        comparison = Quantity(Decimal("201.978") * ureg.gram)
        pint_agg = self.MODEL.objects.aggregate(pint_agg=PintVariance("weight"))["pint_agg"]
        self.assertEqual(comparison, pint_agg)


class TestDecimalFieldSave(FieldSaveTestBase, TestCase):
    MODEL = DecimalPintFieldSaveModel
    EXPECTED_TYPE = Decimal
    DEFAULT_WEIGHT = "100.00"
    DEFAULT_WEIGHT_QUANTITY_STR = "100.00 gram"
    OUNCES = Decimal("10") * ureg.ounce
    OUNCE_VALUE = Decimal("3.52739619496")
    OUNCES_IN_GRAM = Decimal("283.50")
    WEIGHT = Quantity(Decimal("2") * ureg.gram)


class IntLikeFieldSaveTestBase(FieldSaveTestBase):
    DEFAULT_WEIGHT_QUANTITY_STR = "100 gram"
    EXPECTED_TYPE = int
    # 1 ounce = 28.34 grams -> we use something that can be stored as int
    COMPARE_QUANTITY = Quantity(Decimal(str(28 * 1000)) * ureg.milligram)


class TestIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    MODEL = IntegerPintFieldSaveModel


class TestBigIntFieldSave(IntLikeFieldSaveTestBase, TestCase):
    MODEL = BigIntegerPintFieldSaveModel


@pytest.mark.django_db
class TestDefaults(TestCase):
    def setUp(self):
        # Default Values can be used in models
        DefaultsInModel.objects.create(
            weight_int=5 * ureg.gram,
            weight_bigint=5 * ureg.gram,
            weight_decimal=Decimal("5") * ureg.gram,
        )

    def tearDown(self):
        DefaultsInModel.objects.all().delete()

    def test_defaults_int(self):
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_int, ureg.Quantity)
        self.assertEqual(str(obj.weight_int), "5 gram")

    def test_defaults_bigint(self):
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_bigint, ureg.Quantity)
        self.assertEqual(str(obj.weight_bigint), "5 gram")

    def test_defaults_decimal(self):
        obj = DefaultsInModel.objects.first()
        self.assertIsInstance(obj.weight_decimal, ureg.Quantity)
        self.assertEqual(str(obj.weight_decimal), "5.00 gram")


class FieldUpdateTestBase:
    MODEL: Type[FieldSaveModel]
    EXPECTED_TYPE: Type = int
    DEFAULT_WEIGHT = Quantity(2 * ureg.gram)
    DEFAULT_WEIGHT_QUANTITY_STR = "2 gram"
    NEW_WEIGHT = Quantity(2 * ureg.ounce)
    NEW_WEIGHT_QUANTITY_STR = "2 ounce"

    def setUp(self):
        self.MODEL.objects.create(
            weight=self.DEFAULT_WEIGHT,
            name="grams",
        )

    def tearDown(self):
        self.MODEL.objects.all().delete()

    def test_value_updated(self):
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
    MODEL = DecimalPintFieldSaveModel
    EXPECTED_TYPE = Decimal
    DEFAULT_WEIGHT = Quantity(Decimal("2.00") * ureg.gram)
    DEFAULT_WEIGHT_QUANTITY_STR = "2.00 gram"
    NEW_WEIGHT = Quantity(Decimal("2.00") * ureg.ounce)
    NEW_WEIGHT_QUANTITY_STR = "2.00 ounce"


class TestIntFieldUpdate(FieldUpdateTestBase, TestCase):
    MODEL = IntegerPintFieldSaveModel


class TestBigIntFieldUpdate(FieldUpdateTestBase, TestCase):
    MODEL = BigIntegerPintFieldSaveModel
