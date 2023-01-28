from django import forms

from django_pint_field.forms import DecimalPintFormField, IntegerPintFormField
from django_pint_field.widgets import TabledPintFieldWidget, PintFieldWidget

from .models import (
    BigIntegerPintFieldSaveModel,
    DecimalPintFieldSaveModel,
    IntegerPintFieldSaveModel,
    DjangoPintFieldWidgetComparisonModel,
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


class DjangoPintFieldWidgetComparisonAdminForm(forms.ModelForm):
    class Meta:
        model = DjangoPintFieldWidgetComparisonModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        default_unit = self.fields["tabled_weight_int"].default_unit
        unit_choices = self.fields["tabled_weight_int"].unit_choices
        self.fields["tabled_weight_int"].widget = TabledPintFieldWidget(
            default_unit=default_unit, unit_choices=unit_choices
        )
        self.fields["tabled_weight_bigint"].widget = TabledPintFieldWidget(
            default_unit=default_unit, unit_choices=unit_choices
        )
        self.fields["tabled_weight_decimal"].widget = TabledPintFieldWidget(
            default_unit=default_unit, unit_choices=unit_choices
        )
