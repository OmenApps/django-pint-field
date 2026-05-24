"""Tests for system checks and the setup_pint_field management command."""

from io import StringIO
from unittest import mock

import pytest
from django.core.checks import registry as checks_registry
from django.core.management import call_command

from django_pint_field.checks import check_composite_type_registered
from django_pint_field.checks import check_database_backend


class TestDatabaseBackendCheck:
    """Tests for the non-PostgreSQL backend check."""

    def test_no_error_for_postgresql(self):
        """A PostgreSQL default connection produces no errors."""
        fake_conn = mock.Mock(vendor="postgresql")
        with mock.patch("django_pint_field.checks.connections", {"default": fake_conn}):
            errors = check_database_backend(app_configs=None)
        assert errors == []

    def test_error_for_sqlite(self):
        """A non-PostgreSQL default connection produces error E001."""
        fake_conn = mock.Mock(vendor="sqlite")
        with mock.patch("django_pint_field.checks.connections", {"default": fake_conn}):
            errors = check_database_backend(app_configs=None)
        assert len(errors) == 1
        assert errors[0].id == "django_pint_field.E001"


@pytest.mark.django_db
class TestCompositeTypeCheck:
    """Tests for the missing-composite-type database check."""

    def test_no_warning_when_type_exists(self):
        """The migrations create pint_field, so no warning is emitted."""
        warnings = check_composite_type_registered(app_configs=None, databases=["default"])
        assert warnings == []

    def test_skipped_when_databases_not_requested(self):
        """Without a databases list (no DB access requested), the check is skipped."""
        warnings = check_composite_type_registered(app_configs=None, databases=None)
        assert warnings == []

    def test_warning_when_type_missing(self):
        """W001 is emitted when the composite type is not visible."""
        fake_conn = mock.Mock(vendor="postgresql")
        with mock.patch("django_pint_field.checks.connections", {"default": fake_conn}):
            with mock.patch("django_pint_field.checks.pint_composite_type_exists", return_value=False):
                warnings = check_composite_type_registered(app_configs=None, databases=["default"])
        assert len(warnings) == 1
        assert warnings[0].id == "django_pint_field.W001"


def test_checks_are_registered():
    """Both pint-field checks are registered with Django's check framework."""
    names = {getattr(check, "__name__", "") for check in checks_registry.registry.registered_checks}
    assert "check_database_backend" in names
    assert "check_composite_type_registered" in names


@pytest.mark.django_db
class TestSetupCommand:
    """Tests for the setup_pint_field management command."""

    def test_reports_composite_type_present(self):
        """After migrations the command confirms the composite type exists."""
        out = StringIO()
        call_command("setup_pint_field", stdout=out)
        output = out.getvalue()
        assert "pint_field" in output
        assert "ready" in output.lower() or "exists" in output.lower()
