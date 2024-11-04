"""Test the admin pages for the example models"""

from typing import Dict

import django.contrib.admin
import pytest
from django.contrib.admin import ModelAdmin
from django.db.models import Model
from django.forms import Field
from django.forms import ModelForm

from django_pint_field.widgets import PintFieldWidget
from example_project.example import models


@pytest.mark.parametrize(
    "model, field",
    [
        (models.IntegerPintFieldSaveModel, "weight"),
        (models.BigIntegerPintFieldSaveModel, "weight"),
        (models.DecimalPintFieldSaveModel, "weight"),
        (models.HayBale, "weight_int"),
        (models.HayBale, "weight_bigint"),
        (models.HayBale, "weight_decimal"),
        (models.EmptyHayBaleInteger, "weight"),
        (models.EmptyHayBaleBigInteger, "weight"),
        (models.EmptyHayBaleDecimal, "weight"),
        (models.CustomUregHayBale, "custom_int"),
        (models.CustomUregHayBale, "custom_bigint"),
        (models.CustomUregHayBale, "custom_decimal"),
        (models.ChoicesDefinedInModel, "weight_int"),
        (models.ChoicesDefinedInModel, "weight_bigint"),
        (models.ChoicesDefinedInModel, "weight_decimal"),
    ],
)
def test_admin_widgets(model: Model, field: str):
    """Test that all admin pages deliver the correct widget."""
    admin: ModelAdmin = django.contrib.admin.site._registry[model]
    form: ModelForm = admin.get_form({})()
    form_fields: Dict[str, Field] = form.fields
    assert isinstance(form_fields[field].widget, PintFieldWidget)
