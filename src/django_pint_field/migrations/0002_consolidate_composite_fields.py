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
        # Deal with inherited tables.
        # Identify all tables and their inheritance information.
        cursor.execute(
            """
            WITH RECURSIVE inheritance_chain AS (
                -- Base case: tables with no parent
                SELECT c.oid as table_oid,
                       c.relname as table_name,
                       n.nspname as schema_name,
                       NULL::oid as parent_oid,
                       0 as level
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM pg_inherits
                      WHERE inhrelid = c.oid
                  )

                UNION ALL

                -- Recursive case: child tables
                SELECT c.oid,
                       c.relname,
                       n.nspname,
                       i.inhparent,
                       ic.level + 1
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_inherits i ON i.inhrelid = c.oid
                JOIN inheritance_chain ic ON ic.table_oid = i.inhparent
                WHERE c.relkind = 'r'
            )
            SELECT DISTINCT ON (schema_name, table_name)
                   schema_name,
                   table_name,
                   parent_oid IS NOT NULL as is_child
            FROM inheritance_chain
            ORDER BY schema_name, table_name, level DESC;
            """
        )
        tables_info = cursor.fetchall()

        # Create temporary tables to store field information
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

        def convert_column(schema, table, column, is_child):
            if is_child:
                # For child tables, handle the parent first
                cursor.execute(
                    """
                    SELECT n.nspname, c.relname
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_inherits i ON i.inhparent = c.oid
                    WHERE i.inhrelid = (
                        SELECT oid
                        FROM pg_class
                        WHERE relname = %s
                        AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                    );
                    """,
                    [table, schema]
                )
                parent_info = cursor.fetchone()
                if parent_info:
                    convert_column(parent_info[0], parent_info[1], column, False)

            # Add a new column with the new type
            temp_column = f"{column}_new"
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                ADD COLUMN "{temp_column}" pint_field;

                UPDATE "{schema}"."{table}"
                SET "{temp_column}" = ROW(
                    ({column}).comparator,
                    ({column}).magnitude::decimal,
                    ({column}).units
                )::pint_field;
                """
            )

            # Drop the old column and rename the new one
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}" DROP COLUMN "{column}";
                ALTER TABLE "{schema}"."{table}" RENAME COLUMN "{temp_column}" TO "{column}";
                """
            )

        # Process each type of field
        for field_type in ['integer', 'bigint', 'decimal']:
            cursor.execute(
                f"""
                SELECT table_schema, table_name, column_name
                FROM temp_{field_type}_fields;
                """
            )
            fields = cursor.fetchall()

            for schema, table, column in fields:
                # Find if this table is a child table
                is_child = next(
                    (info[2] for info in tables_info
                     if info[0] == schema and info[1] == table),
                    False
                )
                convert_column(schema, table, column, is_child)

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
                "CREATE TYPE integer_pint_field AS (comparator decimal, magnitude integer, units text);",
                "CREATE TYPE big_integer_pint_field AS (comparator decimal, magnitude bigint, units text);",
                "CREATE TYPE decimal_pint_field AS (comparator decimal, magnitude decimal, units text);",
            ],
        ),
        # Clear OID cache
        migrations.RunPython(clear_oids),
    ]
