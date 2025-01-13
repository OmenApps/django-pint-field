"""Automatically register all models in the reports app with the admin site."""

from django.apps import apps
from django.contrib import admin


class ListAdminMixin(object):
    """Mixin to automatically set list_display to all fields on a model."""

    def __init__(self, model, admin_site):  # pylint: disable=W0621
        self.list_display = [field.name for field in model._meta.fields]
        super().__init__(model, admin_site)


for model in apps.get_app_config("laboratory").get_models():
    admin_class = type("AdminClass", (ListAdminMixin, admin.ModelAdmin), {})  # pylint: disable=C0103
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass
