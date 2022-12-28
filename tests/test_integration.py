import pytest

from django import forms
from django.test import TestCase

from decimal import Decimal

from tests.dummyapp.forms import (
    DefaultFormBigInt,
    DefaultFormDecimal,
    DefaultFormFieldsBigInt,
    DefaultFormFieldsDecimal,
    DefaultFormFieldsFloat,
    DefaultFormFieldsInt,
    DefaultFormFloat,
    DefaultFormInt,
    DefaultWidgetsFormBigInt,
    DefaultWidgetsFormDecimal,
    DefaultWidgetsFormFloat,
    DefaultWidgetsFormInt,
)


class IntegrationTestBase:
    DEFAULT_FORM = DefaultFormFloat
    DEFAULT_FIELDS_FORM = DefaultFormFieldsFloat
    DEFAULT_WIDGET_FORM = DefaultWidgetsFormFloat

    INPUT_STR = "10.3"
    OUTPUT_MAGNITUDE = 10.3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure we did no mistake creating the tests
        assert self.DEFAULT_FORM.Meta.model == self.DEFAULT_FIELDS_FORM.Meta.model
        assert self.DEFAULT_FORM.Meta.model == self.DEFAULT_WIDGET_FORM.Meta.model

    def _check_form_and_saved_object(self, form: forms.ModelForm, has_magnitude: bool):
        self.assertTrue(form.is_valid())
        if has_magnitude:
            self.assertAlmostEqual(
                form.cleaned_data["weight"].magnitude, self.OUTPUT_MAGNITUDE
            )
            self.assertEqual(str(form.cleaned_data["weight"].units), "gram")
        else:
            self.assertAlmostEqual(form.cleaned_data["weight"], self.OUTPUT_MAGNITUDE)
        form.save()
        obj = form.Meta.model.objects.last()
        self.assertEqual(str(obj.weight.units), "gram")
        if type(self.OUTPUT_MAGNITUDE) == float:
            self.assertAlmostEqual(obj.weight.magnitude, self.OUTPUT_MAGNITUDE)
        else:
            self.assertEqual(obj.weight.magnitude, self.OUTPUT_MAGNITUDE)
        self.assertIsInstance(obj.weight.magnitude, type(self.OUTPUT_MAGNITUDE))

    @pytest.mark.django_db
    def test_widget_valid_inputs_with_units(self):
        form = self.DEFAULT_FORM(
            data={
                "name": "testing",
                "weight_0": self.INPUT_STR,
                "weight_1": "gram",
            }
        )
        self._check_form_and_saved_object(form, True)

    @pytest.mark.django_db
    def test_widget_single_inputs_with_units_and_default_form_fields(self):
        """
        Test with default form fields, will still create the correct
        database entries
        """
        form = self.DEFAULT_FIELDS_FORM(
            data={
                "name": "testing",
                "weight": self.INPUT_STR,
            }
        )
        self._check_form_and_saved_object(form, False)


class TestFloatFieldWidgetIntegration(IntegrationTestBase, TestCase):
    pass


class TestDecimalFieldWidgetIntegration(IntegrationTestBase, TestCase):
    DEFAULT_FORM = DefaultFormDecimal
    DEFAULT_FIELDS_FORM = DefaultFormFieldsDecimal
    DEFAULT_WIDGET_FORM = DefaultWidgetsFormDecimal
    INPUT_STR = "10"
    OUTPUT_MAGNITUDE = Decimal("10")


class IntegrationTestBaseInt(IntegrationTestBase):
    INPUT_STR = "10"
    OUTPUT_MAGNITUDE = 10


class TestIntFiledWidgetIntegration(IntegrationTestBaseInt, TestCase):
    DEFAULT_FORM = DefaultFormInt
    DEFAULT_FIELDS_FORM = DefaultFormFieldsInt
    DEFAULT_WIDGET_FORM = DefaultWidgetsFormInt


class TestBigIntFiledWidgetIntegration(IntegrationTestBaseInt, TestCase):
    DEFAULT_FORM = DefaultFormBigInt
    DEFAULT_FIELDS_FORM = DefaultFormFieldsBigInt
    DEFAULT_WIDGET_FORM = DefaultWidgetsFormBigInt
