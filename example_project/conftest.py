"""Pytest configuration for example project."""

import warnings

# Filter out pydantic deprecation warnings from django-ninja before any imports
# This must be done early because the warnings are raised at import time
warnings.filterwarnings(
    "ignore",
    message="Support for class-based",
    category=DeprecationWarning,
)

from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402

from django_pint_field.models import IntegerPintField  # noqa: E402
from django_pint_field.units import ureg  # noqa: E402


def pytest_configure(config):
    """Configure pytest before test collection."""
    # Also set the warning filter in pytest's warning plugin
    # This catches warnings during collection
    warnings.filterwarnings(
        "ignore",
        message="Support for class-based",
        category=DeprecationWarning,
    )


@pytest.fixture
def field_test_objects(request):
    """Create test objects with different weights."""
    model_cls = request.cls.MODEL
    expected_type = request.cls.EXPECTED_TYPE
    default_weight = request.cls.DEFAULT_WEIGHT
    heaviest = request.cls.HEAVIEST
    lightest = request.cls.LIGHTEST

    if expected_type == Decimal:
        default = model_cls.objects.create(
            weight=ureg.Quantity(Decimal(str(default_weight)) * ureg.gram),
            name="grams",
        )
        lightest_obj = model_cls.objects.create(
            weight=ureg.Quantity(Decimal(str(lightest)) * ureg.gram),
            name="lightest",
        )
        heaviest_obj = model_cls.objects.create(
            weight=ureg.Quantity(Decimal(str(heaviest)) * ureg.gram),
            name="heaviest",
        )
    else:
        default = model_cls.objects.create(
            weight=ureg.Quantity(default_weight * ureg.gram),
            name="grams",
        )
        lightest_obj = model_cls.objects.create(
            weight=ureg.Quantity(lightest * ureg.gram),
            name="lightest",
        )
        heaviest_obj = model_cls.objects.create(
            weight=ureg.Quantity(heaviest * ureg.gram),
            name="heaviest",
        )

    yield {"default": default, "lightest": lightest_obj, "heaviest": heaviest_obj}

    model_cls.objects.all().delete()


@pytest.fixture
def unit_registry():
    """Return a Pint unit registry."""
    return ureg


@pytest.fixture
def integer_pint_field():
    """Return an IntegerPintField instance."""
    return IntegerPintField(default_unit="meter")
