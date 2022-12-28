from django import forms

from quantityfield.fields import (
    DecimalQuantityFormField,
    IntegerQuantityFormField,
    QuantityFormField,
)
from tests.dummyapp.models import (
    BigIntFieldSaveModel,
    DecimalFieldSaveModel,
    FloatFieldSaveModel,
    IntFieldSaveModel,
)


class DefaultFormFloat(forms.ModelForm):
    weight = QuantityFormField(base_units="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = FloatFieldSaveModel
        fields = "__all__"


class DefaultFormInt(forms.ModelForm):
    weight = IntegerQuantityFormField(base_units="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = IntFieldSaveModel
        fields = "__all__"


class DefaultFormBigInt(forms.ModelForm):
    weight = IntegerQuantityFormField(base_units="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = BigIntFieldSaveModel
        fields = "__all__"


class DefaultFormDecimal(forms.ModelForm):
    weight = DecimalQuantityFormField(base_units="gram", unit_choices=["ounce", "gram"])

    class Meta:
        model = DecimalFieldSaveModel
        fields = "__all__"


class DefaultFormFieldsFloat(forms.ModelForm):
    weight = forms.FloatField()

    class Meta:
        model = FloatFieldSaveModel
        fields = "__all__"


class DefaultFormFieldsDecimal(forms.ModelForm):
    weight = forms.FloatField()

    class Meta:
        model = DecimalFieldSaveModel
        fields = "__all__"


class DefaultFormFieldsInt(forms.ModelForm):
    weight = forms.IntegerField()

    class Meta:
        model = IntFieldSaveModel
        fields = "__all__"


class DefaultFormFieldsBigInt(forms.ModelForm):
    weight = forms.IntegerField()

    class Meta:
        model = BigIntFieldSaveModel
        fields = "__all__"


class DefaultWidgetsFormFloat(forms.ModelForm):
    weight = QuantityFormField(
        base_units="gram", unit_choices=["ounce", "gram"], widget=forms.NumberInput
    )

    class Meta:
        model = FloatFieldSaveModel
        fields = "__all__"


class DefaultWidgetsFormDecimal(forms.ModelForm):
    weight = QuantityFormField(
        base_units="gram", unit_choices=["ounce", "gram"], widget=forms.NumberInput
    )

    class Meta:
        model = DecimalFieldSaveModel
        fields = "__all__"


class DefaultWidgetsFormInt(forms.ModelForm):
    weight = IntegerQuantityFormField(
        base_units="gram", unit_choices=["ounce", "gram"], widget=forms.NumberInput
    )

    class Meta:
        model = IntFieldSaveModel
        fields = "__all__"


class DefaultWidgetsFormBigInt(forms.ModelForm):
    weight = IntegerQuantityFormField(
        base_units="gram", unit_choices=["ounce", "gram"], widget=forms.NumberInput
    )

    class Meta:
        model = BigIntFieldSaveModel
        fields = "__all__"
