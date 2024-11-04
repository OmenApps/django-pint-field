"""Admin configuration for the example app."""

from django.contrib import admin

from .forms import DjangoPintFieldWidgetComparisonAdminForm
from .models import *  # noqa: F401, F403


class ReadOnlyEditing(admin.ModelAdmin):
    """Admin class that makes all fields readonly."""

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return list(self.get_fields(request))
        return []


admin.site.register(IntegerPintFieldSaveModel)
admin.site.register(BigIntegerPintFieldSaveModel)
admin.site.register(DecimalPintFieldSaveModel)

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
