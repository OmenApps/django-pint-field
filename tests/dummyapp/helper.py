from django.db.models.base import ModelBase
from typing import Dict
from .models import *  # noqa: F401, F403


def get_test_models() -> Dict[str, ModelBase]:
    """
    Get a list of all Test models
    """
    result = {}
    for name, obj in globals().items():
        if not name.startswith("_"):
            if isinstance(obj, ModelBase):
                if not obj._meta.abstract:
                    if obj._meta.app_config.name.endswith("dummyapp"):
                        result[name] = obj
    return result


def print_admins():
    for model in sorted(get_test_models().keys()):
        print(f"admin.site.register({model}, ReadOnlyEditing)")
