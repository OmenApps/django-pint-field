"""Helper functions for the example project."""

from django.db.models.base import ModelBase

from .models import *  # noqa: F401, F403


def get_test_models() -> dict[str, ModelBase]:
    """Get a list of all Test models."""
    result = {}
    for name, obj in globals().items():
        if not name.startswith("_"):
            if isinstance(obj, ModelBase):
                if not obj._meta.abstract:
                    if obj._meta.app_config.name.endswith("example"):
                        result[name] = obj
    return result


def print_admins():
    """Print the code to register all test models with the ReadOnlyEditing admin."""
    for model in sorted(get_test_models().keys()):
        print(f"admin.site.register({model}, ReadOnlyEditing)")
