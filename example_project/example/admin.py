"""Admin configuration for the example app."""

from django.contrib import admin

from .forms import DjangoPintFieldWidgetComparisonAdminForm
from .models import BigIntegerPintFieldSaveModel
from .models import ChoicesDefinedInModel
from .models import CustomUregHayBale
from .models import DecimalPintFieldSaveModel
from .models import DjangoPintFieldWidgetComparisonModel
from .models import EmptyHayBaleBigInteger
from .models import EmptyHayBaleDecimal
from .models import EmptyHayBaleInteger
from .models import HayBale
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


admin.site.register(HayBale)
admin.site.register(EmptyHayBaleInteger)
admin.site.register(EmptyHayBaleBigInteger)
admin.site.register(EmptyHayBaleDecimal)
admin.site.register(CustomUregHayBale)
admin.site.register(ChoicesDefinedInModel)


@admin.register(DjangoPintFieldWidgetComparisonModel)
class DjangoPintFieldWidgetComparisonAdmin(admin.ModelAdmin):
    """Admin for DjangoPintFieldWidgetComparisonModel."""

    form = DjangoPintFieldWidgetComparisonAdminForm
