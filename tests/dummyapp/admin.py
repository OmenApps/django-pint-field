from django.contrib import admin

from .models import *  # noqa: F401, F403


class ReadOnlyEditing(admin.ModelAdmin):
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
