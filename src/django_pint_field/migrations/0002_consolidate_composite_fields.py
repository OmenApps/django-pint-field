"""Migration to consolidate PintField types into a single composite type."""

import functools

from django.contrib.postgres.signals import get_type_oids
from django.db import connection
from django.db import migrations


@functools.lru_cache
def get_pint_field_oids(connection_alias):
    """Return field and field array OIDs for new pint_field type."""
    return get_type_oids(connection_alias, "pint_field")


def clear_oids(apps, schema_editor):  # pylint: disable=W0613
    """Clear cached OIDs."""
    get_pint_field_oids.cache_clear()


def convert_existing_data(apps, schema_editor):  # pylint: disable=W0613
    """Convert existing data to new pint_field type."""
    with connection.cursor() as cursor:
        # First, create temporary tables to store existing data
        cursor.execute(
            """
            CREATE TEMP TABLE temp_integer_fields AS
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE udt_name = 'integer_pint_field';

            CREATE TEMP TABLE temp_bigint_fields AS
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE udt_name = 'big_integer_pint_field';

            CREATE TEMP TABLE temp_decimal_fields AS
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE udt_name = 'decimal_pint_field';
        """
        )

        # Convert integer_pint_field columns
        cursor.execute(
            """
            SELECT table_schema, table_name, column_name
            FROM temp_integer_fields;
        """
        )
        for schema, table, column in cursor.fetchall():
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                ALTER COLUMN "{column}"
                TYPE pint_field
                USING ROW(
                    ({column}).comparator,
                    ({column}).magnitude::decimal,
                    ({column}).units
                )::pint_field;
            """
            )

        # Convert big_integer_pint_field columns
        cursor.execute(
            """
            SELECT table_schema, table_name, column_name
            FROM temp_bigint_fields;
        """
        )
        for schema, table, column in cursor.fetchall():
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                ALTER COLUMN "{column}"
                TYPE pint_field
                USING ROW(
                    ({column}).comparator,
                    ({column}).magnitude::decimal,
                    ({column}).units
                )::pint_field;
            """
            )

        # Convert decimal_pint_field columns
        cursor.execute(
            """
            SELECT table_schema, table_name, column_name
            FROM temp_decimal_fields;
        """
        )
        for schema, table, column in cursor.fetchall():
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                ALTER COLUMN "{column}"
                TYPE pint_field
                USING ({column})::pint_field;
            """
            )

        # Clean up temporary tables
        cursor.execute(
            """
            DROP TABLE temp_integer_fields;
            DROP TABLE temp_bigint_fields;
            DROP TABLE temp_decimal_fields;
        """
        )


class Migration(migrations.Migration):
    """Consolidate PintField types into a single composite type."""

    dependencies = [
        # Add your previous migration dependency here
        ("django_pint_field", "0001_create_composite_fields"),
    ]

    operations = [
        # Create new type first
        migrations.RunSQL(
            sql=["CREATE TYPE pint_field AS (comparator decimal, magnitude decimal, units text);"],
            reverse_sql=["DROP TYPE IF EXISTS pint_field CASCADE;"],
        ),
        # Convert existing data
        migrations.RunPython(convert_existing_data, reverse_code=migrations.RunPython.noop),
        # Drop old types after conversion
        migrations.RunSQL(
            sql=[
                "DROP TYPE IF EXISTS integer_pint_field CASCADE;",
                "DROP TYPE IF EXISTS big_integer_pint_field CASCADE;",
                "DROP TYPE IF EXISTS decimal_pint_field CASCADE;",
            ],
            reverse_sql=[
                # Recreate original types if rolling back
                "CREATE TYPE integer_pint_field AS (comparator decimal, magnitude integer, units text);",
                "CREATE TYPE big_integer_pint_field AS (comparator decimal, magnitude bigint, units text);",
                "CREATE TYPE decimal_pint_field AS (comparator decimal, magnitude decimal, units text);",
            ],
        ),
        # Clear OID cache
        migrations.RunPython(clear_oids),
    ]
