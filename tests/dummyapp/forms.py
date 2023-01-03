from django import forms

from django_pint_field.forms import (
    DecimalPintFormField,
    IntegerPintFormField,
)
from tests.dummyapp.models import (
    BigIntegerPintFieldSaveModel,
    DecimalPintFieldSaveModel,
    IntegerPintFieldSaveModel,
)


class DefaultFormInteger(forms.ModelForm):
    weight = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = IntegerPintFieldSaveModel
        fields = "__all__"


class DefaultFormBigInteger(forms.ModelForm):
    weight = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = BigIntegerPintFieldSaveModel
        fields = "__all__"


class DefaultFormDecimal(forms.ModelForm):
    weight = DecimalPintFormField(default_unit="gram", unit_choices=["ounce", "gram"], max_digits=10, decimal_places=2)

    class Meta:
        model = DecimalPintFieldSaveModel
        fields = "__all__"
