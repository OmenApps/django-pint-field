"""Forms for the example app."""

from django import forms

from django_pint_field.forms import DecimalPintFormField
from django_pint_field.forms import IntegerPintFormField
from django_pint_field.widgets import TabledPintFieldWidget

from .models import BigIntegerPintFieldSaveModel
from .models import DecimalPintFieldSaveModel
from .models import DjangoPintFieldWidgetComparisonModel
from .models import IntegerPintFieldSaveModel


class DefaultFormInteger(forms.ModelForm):
    """Form for IntegerPintFieldSaveModel."""

    weight = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram"])

    class Meta:
        """Meta class for DefaultFormInteger."""

        model = IntegerPintFieldSaveModel
        fields = "__all__"


class DefaultFormBigInteger(forms.ModelForm):
    """Form for BigIntegerPintFieldSaveModel."""

    weight = IntegerPintFormField(default_unit="gram", unit_choices=["ounce", "gram"])

    class Meta:
        """Meta class for DefaultFormBigInteger."""

        model = BigIntegerPintFieldSaveModel
        fields = "__all__"


class DefaultFormDecimal(forms.ModelForm):
    """Form for DecimalPintFieldSaveModel."""

    weight = DecimalPintFormField(default_unit="gram", unit_choices=["ounce", "gram"], max_digits=10, decimal_places=2)

    class Meta:
        """Meta class for DefaultFormDecimal."""

        model = DecimalPintFieldSaveModel
        fields = "__all__"


class DjangoPintFieldWidgetComparisonAdminForm(forms.ModelForm):
    """Form for DjangoPintFieldWidgetComparisonModel."""

    class Meta:
        """Meta class for DjangoPintFieldWidgetComparisonAdminForm."""

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
