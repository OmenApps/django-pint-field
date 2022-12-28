from django.contrib import admin

from .models import *  # noqa: F401, F403


class ReadOnlyEditing(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return list(self.get_fields(request))
        return []


admin.site.register(BigIntFieldSaveModel, ReadOnlyEditing)
admin.site.register(ChoicesDefinedInModel, ReadOnlyEditing)
admin.site.register(ChoicesDefinedInModelInt, ReadOnlyEditing)
admin.site.register(CustomUregDecimalHayBale, ReadOnlyEditing)
admin.site.register(CustomUregHayBale, ReadOnlyEditing)
admin.site.register(DecimalFieldSaveModel, ReadOnlyEditing)
admin.site.register(EmptyHayBaleBigInt, ReadOnlyEditing)
admin.site.register(EmptyHayBaleDecimal, ReadOnlyEditing)
admin.site.register(EmptyHayBaleFloat, ReadOnlyEditing)
admin.site.register(EmptyHayBaleInt, ReadOnlyEditing)
admin.site.register(FloatFieldSaveModel, ReadOnlyEditing)
admin.site.register(HayBale, ReadOnlyEditing)
admin.site.register(IntFieldSaveModel, ReadOnlyEditing)
