"""Test cases for app configuration and initialization."""

from decimal import getcontext
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django.db.backends.signals import connection_created
from django.db.models.signals import post_migrate

import django_pint_field.apps as apps_module
from django_pint_field.apps import DjangoPintFieldAppConfig
from django_pint_field.apps import register_composite_types_once
from django_pint_field.apps import set_decimal_precision


pytestmark = pytest.mark.django_db


class TestSetDecimalPrecision:
    """Test the set_decimal_precision function."""

    def test_sets_precision_when_valid_int(self):
        """Test that precision is set when a valid integer is provided."""
        original_precision = getcontext().prec
        try:
            with patch.object(apps_module, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 40):
                set_decimal_precision()
                assert getcontext().prec == 40
        finally:
            getcontext().prec = original_precision

    def test_does_not_change_precision_when_zero(self):
        """Test that precision is not changed when value is 0."""
        original_precision = getcontext().prec
        try:
            with patch.object(apps_module, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", 0):
                set_decimal_precision()
                assert getcontext().prec == original_precision
        finally:
            getcontext().prec = original_precision

    def test_does_not_change_precision_when_negative(self):
        """Test that precision is not changed when value is negative."""
        original_precision = getcontext().prec
        try:
            with patch.object(apps_module, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", -10):
                set_decimal_precision()
                assert getcontext().prec == original_precision
        finally:
            getcontext().prec = original_precision

    def test_does_not_change_precision_when_none(self):
        """Test that precision is not changed when value is None."""
        original_precision = getcontext().prec
        try:
            with patch.object(apps_module, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", None):
                set_decimal_precision()
                assert getcontext().prec == original_precision
        finally:
            getcontext().prec = original_precision

    def test_does_not_change_precision_when_string(self):
        """Test that precision is not changed when value is a string."""
        original_precision = getcontext().prec
        try:
            with patch.object(apps_module, "DJANGO_PINT_FIELD_DECIMAL_PRECISION", "40"):
                set_decimal_precision()
                assert getcontext().prec == original_precision
        finally:
            getcontext().prec = original_precision


class TestRegisterCompositeTypesOnce:
    """Test the register_composite_types_once function."""

    def test_idempotency_only_registers_once(self):
        """Test that composite types are only registered once."""
        # Reset the global flag
        original_flag = apps_module._composite_types_registered
        apps_module._composite_types_registered = False

        try:
            mock_register = MagicMock()
            # Patch in the models module where it's defined
            with patch("django_pint_field.models.register_pint_composite_types", mock_register):
                # First call should register
                register_composite_types_once(sender=None)

                # Second call should not register again
                register_composite_types_once(sender=None)

                # Third call should not register again
                register_composite_types_once(sender=None)

                # Should only be called once
                assert mock_register.call_count == 1
        finally:
            apps_module._composite_types_registered = original_flag

    def test_skips_registration_when_already_registered(self):
        """Test that registration is skipped when flag is already True."""
        original_flag = apps_module._composite_types_registered
        apps_module._composite_types_registered = True

        try:
            mock_register = MagicMock()
            with patch("django_pint_field.models.register_pint_composite_types", mock_register):
                register_composite_types_once(sender=None)
                mock_register.assert_not_called()
        finally:
            apps_module._composite_types_registered = original_flag

    def test_skips_registration_for_non_postgresql(self):
        """Test that registration is skipped for non-PostgreSQL databases."""
        original_flag = apps_module._composite_types_registered
        apps_module._composite_types_registered = False

        try:
            mock_connection = MagicMock()
            mock_connection.vendor = "sqlite"

            mock_register = MagicMock()
            with patch("django_pint_field.models.register_pint_composite_types", mock_register):
                register_composite_types_once(sender=None, connection=mock_connection)
                mock_register.assert_not_called()
                # Flag should still be False since we didn't register
                assert apps_module._composite_types_registered is False
        finally:
            apps_module._composite_types_registered = original_flag

    def test_handles_registration_errors_gracefully(self):
        """Test that registration errors are handled gracefully."""
        original_flag = apps_module._composite_types_registered
        apps_module._composite_types_registered = False

        try:
            mock_register = MagicMock(side_effect=Exception("Test error"))
            with patch("django_pint_field.models.register_pint_composite_types", mock_register):
                # Should not raise an exception
                register_composite_types_once(sender=None)

                # Flag should still be False since registration failed
                assert apps_module._composite_types_registered is False
        finally:
            apps_module._composite_types_registered = original_flag

    def test_sets_flag_on_successful_registration(self):
        """Test that the flag is set to True on successful registration."""
        original_flag = apps_module._composite_types_registered
        apps_module._composite_types_registered = False

        try:
            mock_register = MagicMock()
            with patch("django_pint_field.models.register_pint_composite_types", mock_register):
                register_composite_types_once(sender=None)
                assert apps_module._composite_types_registered is True
        finally:
            apps_module._composite_types_registered = original_flag


class TestDjangoPintFieldAppConfig:
    """Test the DjangoPintFieldAppConfig class."""

    def test_app_name(self):
        """Test that the app name is correct."""
        config = DjangoPintFieldAppConfig("django_pint_field", apps_module)
        assert config.name == "django_pint_field"

    def test_ready_connects_connection_created_signal(self):
        """Test that ready() connects the connection_created signal."""
        config = DjangoPintFieldAppConfig("django_pint_field", apps_module)

        with patch("django_pint_field.lookups.get_pint_field_lookups"):
            with patch.object(apps_module, "set_decimal_precision"):
                config.ready()

        # Check that our receiver is connected
        # Django signals deduplicate, so we check if the receiver is present
        receiver_funcs = [ref() for _, ref, _ in connection_created.receivers if ref() is not None]
        assert register_composite_types_once in receiver_funcs

    def test_ready_connects_post_migrate_signal(self):
        """Test that ready() connects the post_migrate signal."""
        config = DjangoPintFieldAppConfig("django_pint_field", apps_module)

        with patch("django_pint_field.lookups.get_pint_field_lookups"):
            with patch.object(apps_module, "set_decimal_precision"):
                config.ready()

        # Check that our receiver is connected
        # Django signals deduplicate, so we check if the receiver is present
        receiver_funcs = [ref() for _, ref, _ in post_migrate.receivers if ref() is not None]
        assert register_composite_types_once in receiver_funcs

    def test_ready_registers_lookups(self):
        """Test that ready() registers lookups."""
        config = DjangoPintFieldAppConfig("django_pint_field", apps_module)

        mock_get_lookups = MagicMock()
        with patch("django_pint_field.lookups.get_pint_field_lookups", mock_get_lookups):
            with patch.object(apps_module, "set_decimal_precision"):
                config.ready()

        mock_get_lookups.assert_called_once()

    def test_ready_sets_decimal_precision(self):
        """Test that ready() sets decimal precision."""
        config = DjangoPintFieldAppConfig("django_pint_field", apps_module)

        mock_set_precision = MagicMock()
        with patch("django_pint_field.lookups.get_pint_field_lookups"):
            with patch.object(apps_module, "set_decimal_precision", mock_set_precision):
                config.ready()

        mock_set_precision.assert_called_once()


class TestRegisterPintCompositeTypes:
    """Test the register_pint_composite_types function from models."""

    def test_accepts_connection_parameter(self):
        """Test that the function accepts a connection parameter."""
        from django_pint_field.models import register_pint_composite_types

        mock_connection = MagicMock()
        mock_connection.vendor = "sqlite"  # Use sqlite to skip actual registration

        # Should not raise an exception
        register_pint_composite_types(sender=None, connection=mock_connection)

    def test_skips_non_postgresql_connections(self):
        """Test that non-PostgreSQL connections are skipped."""
        from django_pint_field.models import register_pint_composite_types

        mock_connection = MagicMock()
        mock_connection.vendor = "mysql"

        # Should not raise an exception and should return early
        register_pint_composite_types(sender=None, connection=mock_connection)

    def test_skips_no_db_alias(self):
        """Test that NO_DB_ALIAS connections are skipped."""
        from django.db.backends.base.base import NO_DB_ALIAS

        from django_pint_field.models import register_pint_composite_types

        mock_connection = MagicMock()
        mock_connection.vendor = "postgresql"
        mock_connection.alias = NO_DB_ALIAS

        # Should not raise an exception and should return early
        register_pint_composite_types(sender=None, connection=mock_connection)


class TestAppInitializationIntegration:
    """Integration tests for app initialization."""

    def test_composite_types_registered_with_postgresql(self):
        """Test that composite types are registered when using PostgreSQL."""
        from django.db import connection

        # This test runs with a real PostgreSQL connection in the test environment
        if connection.vendor != "postgresql":
            pytest.skip("This test requires PostgreSQL")

        # The app should have registered the composite types during startup
        # We can verify by checking that we can create and query PintField models
        from example_project.example.models import IntegerPintFieldSaveModel

        # Create a test instance
        from django_pint_field.units import ureg

        obj = IntegerPintFieldSaveModel.objects.create(weight=ureg.Quantity(100, "gram"))
        assert obj.weight is not None

        # Clean up
        obj.delete()

    def test_lookups_registered(self):
        """Test that lookups are registered during app initialization."""
        from django_pint_field.models import IntegerPintField

        # Check that our custom lookups are registered
        registered_lookups = IntegerPintField.get_lookups()

        assert "gt" in registered_lookups
        assert "gte" in registered_lookups
        assert "lt" in registered_lookups
        assert "lte" in registered_lookups
        assert "exact" in registered_lookups
        assert "range" in registered_lookups
