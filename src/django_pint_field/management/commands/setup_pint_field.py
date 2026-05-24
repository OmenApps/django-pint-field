"""Management command that prepares the database for django_pint_field."""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import connections

from django_pint_field.checks import pint_composite_type_exists


class Command(BaseCommand):
    """Run the app's migrations and verify the ``pint_field`` composite type."""

    help = "Create and verify the pint_field composite type required by django_pint_field."

    def add_arguments(self, parser):
        """Add the optional --database argument."""
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to set up (default: 'default').",
        )

    def handle(self, *args, **options):
        """Migrate the django_pint_field app and confirm the composite type."""
        alias = options["database"]
        connection = connections[alias]

        if connection.vendor != "postgresql":
            raise CommandError(
                f"django_pint_field requires PostgreSQL, but database {alias!r} uses the {connection.vendor!r} backend."
            )

        self.stdout.write("Applying django_pint_field migrations...")
        call_command("migrate", "django_pint_field", database=alias, verbosity=0)

        if pint_composite_type_exists(connection):
            self.stdout.write(
                self.style.SUCCESS(
                    "The 'pint_field' composite type exists - django_pint_field is ready. "
                    "You can now add IntegerPintField / DecimalPintField to your models."
                )
            )
        else:
            raise CommandError(
                "The 'pint_field' composite type is still missing after migration. "
                "Check that 'django_pint_field' is in INSTALLED_APPS and migrations ran."
            )
