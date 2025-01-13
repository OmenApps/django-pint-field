"""Admin configuration for the example app."""

from django.apps import apps
from django.contrib import admin

from .forms import DjangoPintFieldWidgetComparisonAdminForm
from .models import BigIntegerPintFieldSaveModel
from .models import DecimalPintFieldSaveModel
from .models import DjangoPintFieldWidgetComparisonModel
from .models import IntegerPintFieldSaveModel
from .models import IntegerPintFieldSaveWithIndexModel


class ReadOnlyEditing(admin.ModelAdmin):
    """Admin class that makes all fields readonly."""

    def get_readonly_fields(self, request, obj=None):
        """Return all fields as readonly."""
        if obj is not None:
            return list(self.get_fields(request))
        return []


@admin.register(IntegerPintFieldSaveModel)
class IntegerPintFieldSaveModelAdmin(admin.ModelAdmin):
    """Admin for IntegerPintFieldSaveModel."""

    list_display = ("id", "weight", "weight__kilogram", "weight__pound")


@admin.register(IntegerPintFieldSaveWithIndexModel)
class IntegerPintFieldSaveWithIndexModelAdmin(admin.ModelAdmin):
    """Admin for IntegerPintFieldSaveWithIndexModel."""

    list_display = ("id", "weight", "weight__kilogram", "weight_two", "weight_two__gram")


@admin.register(BigIntegerPintFieldSaveModel)
class BigIntegerPintFieldSaveModelAdmin(admin.ModelAdmin):
    """Admin for BigIntegerPintFieldSaveModel."""

    list_display = ("id", "weight", "weight__kilogram", "weight__pound")


@admin.register(DecimalPintFieldSaveModel)
class DecimalPintFieldSaveModelAdmin(admin.ModelAdmin):
    """Admin for DecimalPintFieldSaveModel."""

    list_display = ("id", "weight", "weight__kilogram", "weight__pound")


@admin.register(DjangoPintFieldWidgetComparisonModel)
class DjangoPintFieldWidgetComparisonAdmin(admin.ModelAdmin):
    """Admin for DjangoPintFieldWidgetComparisonModel."""

    form = DjangoPintFieldWidgetComparisonAdminForm


class ListAdminMixin(object):
    """Mixin to automatically set list_display to all fields on a model."""

    def __init__(self, model, admin_site):  # pylint: disable=W0621
        self.list_display = [field.name for field in model._meta.fields]
        super().__init__(model, admin_site)


for model in apps.get_app_config("example").get_models():
    admin_class = type("AdminClass", (ListAdminMixin, admin.ModelAdmin), {})  # pylint: disable=C0103
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass
