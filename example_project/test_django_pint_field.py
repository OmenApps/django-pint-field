"""Test cases for the django-pint-field package."""

from django.apps import apps
from django.conf import settings


def test_succeeds() -> None:
    """It exits with a status code of zero."""
    assert 0 == 0


def test_settings() -> None:
    """It exits with a status code of zero."""
    assert settings.USE_TZ is True


def test_apps() -> None:
    """It exits with a status code of zero."""
    assert "django_pint_field" in apps.get_app_config("django_pint_field").name
