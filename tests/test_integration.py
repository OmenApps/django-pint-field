import pytest

from django import forms
from django.test import TestCase

from decimal import Decimal

from tests.dummyapp.forms import (
    DefaultFormInteger,
    DefaultFormDecimal,
    DefaultFormBigInteger,
)


class IntegrationTestBase:
    DEFAULT_FORM = DefaultFormInteger

    INPUT_STR = "10.3"
    OUTPUT_MAGNITUDE = 10.3

    def _check_form_and_saved_object(self, form: forms.ModelForm, has_magnitude: bool):
        self.assertTrue(form.is_valid())
        if has_magnitude:
            self.assertAlmostEqual(form.cleaned_data["weight"].magnitude, self.OUTPUT_MAGNITUDE)
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


class TestDecimalFieldWidgetIntegration(IntegrationTestBase, TestCase):
    DEFAULT_FORM = DefaultFormDecimal
    INPUT_STR = "10"
    OUTPUT_MAGNITUDE = Decimal("10")


class TestIntFieldWidgetIntegration(IntegrationTestBase, TestCase):
    INPUT_STR = "10"
    OUTPUT_MAGNITUDE = 10
    DEFAULT_FORM = DefaultFormInteger


class TestBigIntFieldWidgetIntegration(IntegrationTestBase, TestCase):
    INPUT_STR = "10"
    OUTPUT_MAGNITUDE = 10
    DEFAULT_FORM = DefaultFormBigInteger
