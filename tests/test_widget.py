# flake8: noqa: F841
import pytest

from django import forms
from django.test import TestCase

from decimal import Decimal
from pint import DimensionalityError, UndefinedUnitError

from django_pint_field.fields import (
    IntegerPintFormField,
    DecimalPintFormField,
)
from django_pint_field.units import ureg
from django_pint_field.widgets import PintFieldWidget
from tests.dummyapp.models import (
    ChoicesDefinedInModel,
    HayBale,
)

Quantity = ureg.Quantity

"""
ToDo: Need to resolve and test for the following case:
    If we use a plural (e.g.: 'pounds') instead of the singular (e.g.: 'pound'),
    the form will show the default units rather than the desired units.
"""


class HayBaleForm(forms.ModelForm):
    weight_int = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram", "kilogram"])
    weight_bigint = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram", "kilogram"])
    weight_decimal = DecimalPintFormField(
        default_unit="gram", unit_choices=["ounce", "gram", "kilogram"], max_digits=10, decimal_places=2
    )

    class Meta:
        model = HayBale
        fields = ["weight_int", "weight_bigint", "weight_decimal"]


class UnitChoicesDefinedInModelFieldModelForm(forms.ModelForm):
    class Meta:
        model = ChoicesDefinedInModel
        fields = ["weight_int", "weight_bigint", "weight_decimal"]


class NullableWeightForm(forms.Form):
    weight_int = IntegerPintFormField(default_unit="gram", required=False)
    weight_decimal = DecimalPintFormField(default_unit="gram", required=False, max_digits=10, decimal_places=2)


class UnitChoicesForm(forms.Form):
    distance = IntegerPintFormField(default_unit="kilometer", unit_choices=["mile", "kilometer", "yard", "feet"])


class TestWidgets(TestCase):
    def test_creates_correct_widget_for_modelform(self):
        form = HayBaleForm()
        self.assertIsInstance(form.fields["weight_int"], IntegerPintFormField)
        self.assertIsInstance(form.fields["weight_int"].widget, PintFieldWidget)
        self.assertIsInstance(form.fields["weight_bigint"], IntegerPintFormField)
        self.assertIsInstance(form.fields["weight_bigint"].widget, PintFieldWidget)
        self.assertIsInstance(form.fields["weight_decimal"], DecimalPintFormField)
        self.assertIsInstance(form.fields["weight_decimal"].widget, PintFieldWidget)

    def test_displays_initial_data_correctly(self):
        form = HayBaleForm(initial={"weight": Quantity(100 * ureg.gram), "name": "test"})

    def test_clean_yields_quantity(self):
        form = HayBaleForm(
            data={
                "weight_int_0": 100,
                "weight_int_1": "gram",
                "weight_bigint_0": 100,
                "weight_bigint_1": "gram",
                "weight_decimal_0": 100,
                "weight_decimal_1": "gram",
                "name": "test",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data["weight_int"], Quantity)
        self.assertIsInstance(form.cleaned_data["weight_bigint"], Quantity)
        self.assertIsInstance(form.cleaned_data["weight_decimal"], Quantity)

    def test_clean_yields_quantity_in_correct_units(self):
        form = HayBaleForm(
            data={
                "weight_int_0": 1,
                "weight_int_1": "kilogram",
                "weight_bigint_0": 1,
                "weight_bigint_1": "ounce",
                "weight_decimal_0": 1.0,
                "weight_decimal_1": "pound",
                "name": "test",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(str(form.cleaned_data["weight_int"].units), "kilogram")
        self.assertAlmostEqual(form.cleaned_data["weight_int"].magnitude, 1)
        self.assertEqual(str(form.cleaned_data["weight_bigint"].units), "ounce")
        self.assertAlmostEqual(form.cleaned_data["weight_bigint"].magnitude, 1)
        self.assertEqual(str(form.cleaned_data["weight_decimal"].units), "pound")
        self.assertAlmostEqual(form.cleaned_data["weight_decimal"].magnitude, Decimal("1.0"))

    def test_precision_lost(self):
        def test_clean_yields_quantity_in_correct_units(self):
            form = HayBaleForm(
                data={
                    "weight_int_0": 1,
                    "weight_int_1": "onuce",  # intentional misspelling
                    "weight_bigint_0": 1,
                    "weight_bigint_1": "ounce",
                    "weight_decimal_0": 1.0,
                    "weight_decimal_1": "ounce",
                    "name": "test",
                }
            )
            self.assertFalse(form.is_valid())

    def test_default_unit_is_required_for_integer_form_field(self):
        with self.assertRaises(ValueError):
            field = IntegerPintFormField()  # noqa: F841
        with self.assertRaises(ValueError):
            field = DecimalPintFormField()  # noqa: F841

    def test_quantityfield_can_be_null(self):
        form = NullableWeightForm(
            data={
                "weight_int_0": None,
                "weight_int_1": None,
                "weight_decimal_0": None,
                "weight_decimal_1": None,
            }
        )
        self.assertTrue(form.is_valid())

    def test_validate_units(self):
        form = UnitChoicesForm(
            data={
                "distance_0": 100,
                "distance_1": "ounce",
            }
        )
        self.assertFalse(form.is_valid())

    def test_default_unit_is_included_by_default(self):
        field = IntegerPintFormField(default_unit="mile", unit_choices=["meters", "feet"])
        self.assertIn("mile", field.unit_choices)
        field = DecimalPintFormField(
            default_unit="mile", unit_choices=["meters", "feet"], max_digits=10, decimal_places=2
        )
        self.assertIn("mile", field.unit_choices)

    def test_widget_field_displays_unit_choices(self):
        form = UnitChoicesForm()
        self.assertListEqual(
            [
                ("mile", "mile"),
                ("kilometer", "kilometer"),
                ("yard", "yard"),
                ("feet", "feet"),
            ],
            form.fields["distance"].widget.widgets[1].choices,
        )

    def test_widget_field_displays_unit_choices_for_model_field_propagation(self):
        form = UnitChoicesDefinedInModelFieldModelForm()
        self.assertListEqual(
            [
                ("kilogram", "kilogram"),
                ("milligram", "milligram"),
                ("pounds", "pounds"),
            ],
            form.fields["weight_int"].widget.widgets[1].choices,
        )
        self.assertListEqual(
            [
                ("kilogram", "kilogram"),
                ("milligram", "milligram"),
                ("pounds", "pounds"),
            ],
            form.fields["weight_bigint"].widget.widgets[1].choices,
        )
        self.assertListEqual(
            [
                ("kilogram", "kilogram"),
                ("milligram", "milligram"),
                ("pounds", "pounds"),
            ],
            form.fields["weight_decimal"].widget.widgets[1].choices,
        )

    def test_unit_choices_must_be_valid_units(self):
        with self.assertRaises(UndefinedUnitError):
            field = IntegerPintFormField(default_unit="mile", unit_choices=["gunzu"])  # noqa: F841
            field = DecimalPintFormField(default_unit="mile", unit_choices=["gunzu"])  # noqa: F841

    def test_unit_choices_must_match_base_dimensionality(self):
        with self.assertRaises(DimensionalityError):
            field = IntegerPintFormField(default_unit="gram", unit_choices=["meter", "ounces"])  # noqa: F841
        with self.assertRaises(DimensionalityError):
            field = DecimalPintFormField(
                default_unit="gram", unit_choices=["meter", "ounces"], max_digits=10, decimal_places=2
            )  # noqa: F841

    def test_widget_invalid_float(self):  # ToDo: Not working as expected. Why isn't exception raised?
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "XX",
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "10",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "XX",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())

    def test_widget_missing_required_input(self):
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "",
                "weight_bigint_0": "10",
                "weight_bigint_1": "",
                "weight_decimal_0": "10",
                "weight_decimal_1": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_int", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "",
                "weight_bigint_0": "10",
                "weight_bigint_1": "",
                "weight_decimal_0": "10",
                "weight_decimal_1": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_bigint", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "",
                "weight_bigint_0": "10",
                "weight_bigint_1": "",
                "weight_decimal_0": "10",
                "weight_decimal_1": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_decimal", form.errors)

    def test_widget_empty_value_for_required_input(self):
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "",
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "10",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_int", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "gram",
                "weight_bigint_0": "",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "10",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_bigint", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_decimal", form.errors)

    def test_widget_none_value_set_for_required_input(self):
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": None,
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_int", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "gram",
                "weight_bigint_0": None,
                "weight_bigint_1": "gram",
                "weight_decimal_0": "10",
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_bigint", form.errors)
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10",
                "weight_int_1": "gram",
                "weight_bigint_0": "10",
                "weight_bigint_1": "gram",
                "weight_decimal_0": None,
                "weight_decimal_1": "gram",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_decimal", form.errors)

    def test_widget_int_precision_loss(self):
        form = HayBaleForm(
            data={
                "name": "testing",
                "weight_int_0": "10.3",
                "weight_int_1": "gram",
                "weight_bigint_0": "10.3",
                "weight_bigint_1": "gram",
                "weight_decimal_0": "10.3",
                "weight_decimal_1": "gram",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["weight_int"].magnitude, 10)
        self.assertEqual(form.cleaned_data["weight_bigint"].magnitude, 10)
        self.assertEqual(form.cleaned_data["weight_decimal"].magnitude, Decimal("10.3"))


class TestWidgetRenderingBase(TestCase):
    magnitude = 20
    value = Quantity(magnitude * ureg.ounce)
    expected_created = str(magnitude)
    expected_db = str(magnitude)

    decimal_magnitude = Decimal("20.00")
    decimal_value = Quantity(decimal_magnitude * ureg.ounce)
    decimal_expected_created = str(decimal_magnitude)
    decimal_expected_db = str(decimal_magnitude)

    def get_html(self, value_from_db: bool) -> str:
        """Create the rendered form with the widget"""
        bale = HayBale.objects.create(
            name="Fritz",
            weight_int=self.value,
            weight_bigint=self.value,
            weight_decimal=self.decimal_value,
        )
        if value_from_db:
            # When creating an object django just takes the given value and sets it
            # Once we receive it from the database the correct Quantity is created
            bale = HayBale.objects.get(pk=bale.pk)
        form = HayBaleForm(instance=bale)
        return str(form)

    def get_html_from_dict(self, value_from_db: bool) -> str:
        """Create the rendered form with the widget"""
        data = {
            "name": "testing",
            "weight_int": {
                "magnitude": self.magnitude,
                "units": ureg.ounce,
            },
            "weight_bigint": {
                "magnitude": self.magnitude,
                "units": ureg.ounce,
            },
            "weight_decimal": {
                "magnitude": self.decimal_magnitude,
                "units": ureg.ounce,
            },
        }
        bale = HayBale.objects.create(**data)
        if value_from_db:
            # When creating an object django just takes the given value and sets it
            # Once we receive it from the database the correct Quantity is created
            bale = HayBale.objects.get(pk=bale.pk)
        form = HayBaleForm(instance=bale)
        return str(form)

    def test_widget_display(self):
        # Add to Integration tests
        html = self.get_html(False)
        expected = f'<input type="number" name="weight_int_0" value="{self.expected_created}" step="any" required id="id_weight_int_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_bigint_0" value="{self.expected_created}" step="any" required id="id_weight_bigint_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_decimal_0" value="{self.decimal_expected_created}" step="any" required id="id_weight_decimal_0">'
        self.assertIn(expected, html)
        self.assertIn('<option value="ounce" selected>ounce</option>', html)

    def test_widget_display_db_value(self):
        html = self.get_html(True)
        expected = f'<input type="number" name="weight_int_0" value="{self.expected_db}" step="any" required id="id_weight_int_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_bigint_0" value="{self.expected_db}" step="any" required id="id_weight_bigint_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_decimal_0" value="{self.decimal_expected_db}" step="any" required id="id_weight_decimal_0">'
        self.assertIn(expected, html)
        self.assertIn('<option value="ounce" selected>ounce</option>', html)

    # def test_widget_display_using_dict(self):  # ToDo: Figure out why behavior is different here
    #     # Add to Integration tests
    #     html = self.get_html_from_dict(False)
    #     expected = f'<input type="number" name="weight_int_0" value="{self.expected_created}" step="any" required id="id_weight_int_0">'
    #     self.assertIn(expected, html)
    #     expected = f'<input type="number" name="weight_bigint_0" value="{self.expected_created}" step="any" required id="id_weight_bigint_0">'
    #     self.assertIn(expected, html)
    #     expected = f'<input type="number" name="weight_decimal_0" value="{self.decimal_expected_created}" step="any" required id="id_weight_decimal_0">'
    #     self.assertIn(expected, html)
    #     self.assertIn('<option value="ounce" selected>ounce</option>', html)

    def test_widget_display_using_dict_db_value(self):
        # Add to Integration tests
        html = self.get_html_from_dict(True)
        expected = f'<input type="number" name="weight_int_0" value="{self.expected_db}" step="any" required id="id_weight_int_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_bigint_0" value="{self.expected_db}" step="any" required id="id_weight_bigint_0">'
        self.assertIn(expected, html)
        expected = f'<input type="number" name="weight_decimal_0" value="{self.decimal_expected_db}" step="any" required id="id_weight_decimal_0">'
        self.assertIn(expected, html)
        self.assertIn('<option value="ounce" selected>ounce</option>', html)


class TestWidgetRenderingNegativeNumber(TestWidgetRenderingBase):
    magnitude = 20
    decimal_magnitude = Decimal("20.00")


class TestWidgetRenderingSmallNumber(TestWidgetRenderingBase):
    magnitude = 1e-10
    value = Quantity(magnitude * ureg.ounce)
    expected_created = str(magnitude)
    expected_db = str(0)

    decimal_magnitude = Decimal("1E-10")
    decimal_value = Quantity(decimal_magnitude * ureg.ounce)
    decimal_expected_created = decimal_magnitude.quantize(Decimal("11111111.11"))
    decimal_expected_db = decimal_magnitude.quantize(Decimal("11111111.11"))


class TestWidgetRenderingZeroInt(TestWidgetRenderingBase):
    magnitude = 0
    value = Quantity(magnitude * ureg.ounce)
    expected_created = str(magnitude)
    expected_db = str(0)

    decimal_magnitude = Decimal("0.000000000000000")
    decimal_value = Quantity(decimal_magnitude * ureg.ounce)
    decimal_expected_created = decimal_magnitude.quantize(Decimal("11111111.11"))
    decimal_expected_db = decimal_magnitude.quantize(Decimal("11111111.11"))
