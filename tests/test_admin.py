import pytest

import django.contrib.admin
from django.contrib.admin import ModelAdmin
from django.db.models import Model
from django.forms import Field, ModelForm

from typing import Dict

from quantityfield.widgets import QuantityWidget
from tests.dummyapp import models


@pytest.mark.parametrize(
    "model, field",
    [
        (models.FloatFieldSaveModel, "weight"),
        (models.IntFieldSaveModel, "weight"),
        (models.BigIntFieldSaveModel, "weight"),
        (models.DecimalFieldSaveModel, "weight"),
        (models.HayBale, "weight"),
        (models.HayBale, "weight_int"),
        (models.HayBale, "weight_bigint"),
        (models.EmptyHayBaleFloat, "weight"),
        (models.EmptyHayBaleInt, "weight"),
        (models.EmptyHayBaleBigInt, "weight"),
        (models.EmptyHayBaleDecimal, "weight"),
        (models.CustomUregHayBale, "custom"),
        (models.CustomUregHayBale, "custom_int"),
        (models.CustomUregHayBale, "custom_bigint"),
        (models.CustomUregDecimalHayBale, "custom_decimal"),
        (models.ChoicesDefinedInModel, "weight"),
        (models.ChoicesDefinedInModelInt, "weight"),
    ],
)
def test_admin_widgets(model: Model, field: str):
    """
    Test that all admin pages deliver the correct widget
    """
    admin: ModelAdmin = django.contrib.admin.site._registry[model]
    form: ModelForm = admin.get_form({})()
    form_fields: Dict[str, Field] = form.fields
    assert type(form_fields[field].widget) == QuantityWidget
