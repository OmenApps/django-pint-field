"""Migration to consolidate PintField types into a single composite type."""

import functools
import logging
import typing

from django.contrib.postgres.signals import get_type_oids
from django.db import connection
from django.db import migrations


logger = logging.getLogger(__name__)


@functools.lru_cache
def get_pint_field_oids(connection_alias):
    """Return field and field array OIDs for new pint_field type."""
    return get_type_oids(connection_alias, "pint_field")


def clear_oids(apps, schema_editor):  # pylint: disable=W0613
    """Clear cached OIDs."""
    get_pint_field_oids.cache_clear()


def get_partition_info(cursor, schema: str, table: str) -> typing.Tuple[bool, list]:
    """Get partition information for a table."""
    # Check if table is partitioned
    cursor.execute(
        """
        SELECT partattrs, partstrat
        FROM pg_partitioned_table pt
        JOIN pg_class c ON c.oid = pt.partrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s;
        """,
        [schema, table]
    )
    result = cursor.fetchone()

    if not result:
        return False, []

    # Get list of partitions
    cursor.execute(
        """
        SELECT n.nspname, c.relname
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_namespace pn ON pn.oid = p.relnamespace
        WHERE pn.nspname = %s AND p.relname = %s;
        """,
        [schema, table]
    )

    partitions = cursor.fetchall()
    return True, partitions


def convert_column(schema: str, table: str, column: str, field_type: str) -> None:
    """Convert a single column with proper trigger handling."""
    with connection.cursor() as cursor:
        # First, verify the exact column name case and check if table exists
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
            AND lower(column_name) = lower(%s);
            """,
            [schema, table, column]
        )
        result = cursor.fetchone()
        if not result:
            logger.warning("Column %s not found in %s.%s", column, schema, table)
            return

        actual_column_name = result[0]
        temp_column = f"{actual_column_name}_new"

        # Check if table is partitioned
        is_partitioned, partitions = get_partition_info(cursor, schema, table)

        try:
            # Start transaction
            cursor.execute("BEGIN;")

            # Add new column to parent table
            logger.info("Converting %s.%s.%s from %s to pint_field", schema, table, actual_column_name, field_type)

            # For partitioned tables, we need to add the column to the parent first
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                ADD COLUMN "{temp_column}" pint_field;
                """
            )

            # Copy data with conversion in parent table
            cursor.execute(
                f"""
                UPDATE "{schema}"."{table}"
                SET "{temp_column}" = ROW(
                    ("{actual_column_name}").comparator,
                    ("{actual_column_name}").magnitude::decimal,
                    ("{actual_column_name}").units
                )::pint_field
                WHERE "{actual_column_name}" IS NOT NULL;
                """
            )

            # Verify data was copied correctly
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM "{schema}"."{table}"
                WHERE "{actual_column_name}" IS NOT NULL
                AND "{temp_column}" IS NULL;
                """
            )
            if cursor.fetchone()[0] > 0:
                raise Exception(f"Data copy verification failed for {schema}.{table}.{actual_column_name}")

            if is_partitioned:
                logger.info("Table %s.%s is partitioned, processing partitions...", schema, table)
                for part_schema, part_table in partitions:
                    logger.info("Processing partition %s.%s", part_schema, part_table)

                    # Copy data in partition
                    cursor.execute(
                        f"""
                        UPDATE "{part_schema}"."{part_table}"
                        SET "{temp_column}" = ROW(
                            ("{actual_column_name}").comparator,
                            ("{actual_column_name}").magnitude::decimal,
                            ("{actual_column_name}").units
                        )::pint_field
                        WHERE "{actual_column_name}" IS NOT NULL;
                        """
                    )

                    # Verify partition data
                    cursor.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM "{part_schema}"."{part_table}"
                        WHERE "{actual_column_name}" IS NOT NULL
                        AND "{temp_column}" IS NULL;
                        """
                    )
                    if cursor.fetchone()[0] > 0:
                        raise Exception(f"Data copy verification failed for partition {part_schema}.{part_table}")

            # After successful copy and verification, drop old column from parent
            # This will cascade to partitions
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                DROP COLUMN "{actual_column_name}" CASCADE;
                """
            )

            # Rename new column in parent - will cascade to partitions
            cursor.execute(
                f"""
                ALTER TABLE "{schema}"."{table}"
                RENAME COLUMN "{temp_column}" TO "{actual_column_name}";
                """
            )

            # Commit transaction
            cursor.execute("COMMIT;")

        except Exception as e:
            logger.error("Error converting column %s.%s.%s: %s", schema, table, actual_column_name, str(e))
            # Rollback transaction
            cursor.execute("ROLLBACK;")

            # Try to clean up on error - outside of failed transaction
            try:
                cursor.execute(
                    f"""
                    ALTER TABLE "{schema}"."{table}"
                    DROP COLUMN IF EXISTS "{temp_column}" CASCADE;
                    """
                )
            except Exception:
                pass  # Ignore cleanup errors
            raise


def convert_existing_data(apps, schema_editor):
    """Convert existing data to new pint_field type."""
    with connection.cursor() as cursor:
        # Get all tables using any of our types, including inherited tables
        cursor.execute(
            """
            WITH RECURSIVE inheritance_chain AS (
                -- Base case: tables directly using our types
                SELECT DISTINCT c.oid,
                       n.nspname AS table_schema,
                       c.relname AS table_name,
                       NULL::oid AS parent_oid
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')

                UNION ALL

                -- Recursive case: add inherited tables
                SELECT c.oid,
                       n.nspname,
                       c.relname,
                       i.inhparent
                FROM pg_inherits i
                JOIN pg_class c ON c.oid = i.inhrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN inheritance_chain p ON p.oid = i.inhparent
            )
            SELECT DISTINCT ic.table_schema,
                   ic.table_name,
                   a.attname AS column_name,
                   t.typname AS type_name
            FROM inheritance_chain ic
            JOIN pg_attribute a ON a.attrelid = ic.oid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')
            AND a.attnum > 0  -- Exclude system columns
            ORDER BY ic.table_schema, ic.table_name, a.attname;
            """
        )

        tables_to_convert = cursor.fetchall()

        # Convert each table
        for schema, table, column, type_name in tables_to_convert:
            convert_column(schema, table, column, type_name)


def validate_conversion(apps, schema_editor):
    """Validate that all columns were converted successfully."""
    with connection.cursor() as cursor:
        # Check for any remaining old-type columns, including in inherited tables
        cursor.execute(
            """
            WITH RECURSIVE inheritance_chain AS (
                SELECT DISTINCT c.oid,
                       n.nspname AS table_schema,
                       c.relname AS table_name,
                       NULL::oid AS parent_oid
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')

                UNION ALL

                SELECT c.oid,
                       n.nspname,
                       c.relname,
                       i.inhparent
                FROM pg_inherits i
                JOIN pg_class c ON c.oid = i.inhrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN inheritance_chain p ON p.oid = i.inhparent
            )
            SELECT DISTINCT ic.table_schema,
                   ic.table_name,
                   a.attname AS column_name,
                   t.typname AS type_name
            FROM inheritance_chain ic
            JOIN pg_attribute a ON a.attrelid = ic.oid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')
            AND a.attnum > 0;  -- Exclude system columns
            """
        )
        remaining_columns = cursor.fetchall()
        if remaining_columns:
            for schema, table, column, udt in remaining_columns:
                logger.error("Column %s.%s.%s still has type %s", schema, table, column, udt)
            raise Exception("Not all columns were converted successfully")


class Migration(migrations.Migration):
    """Consolidate PintField types into a single composite type."""

    atomic = False  # Disable atomic transactions

    dependencies = [
        ("django_pint_field", "0001_create_composite_fields"),
    ]

    operations = [
        # First create casting functions and new type
        migrations.RunSQL(
            sql=[
                # Create new type
                "DROP TYPE IF EXISTS pint_field CASCADE;",
                "CREATE TYPE pint_field AS (comparator decimal, magnitude decimal, units text);",

                # Create casting functions
                """
                CREATE OR REPLACE FUNCTION cast_decimal_pint_to_pint(decimal_pint_field)
                RETURNS pint_field AS $$
                    SELECT ROW($1.comparator, $1.magnitude, $1.units)::pint_field;
                $$ LANGUAGE SQL IMMUTABLE STRICT;
                """,
                """
                CREATE OR REPLACE FUNCTION cast_integer_pint_to_pint(integer_pint_field)
                RETURNS pint_field AS $$
                    SELECT ROW($1.comparator, $1.magnitude::decimal, $1.units)::pint_field;
                $$ LANGUAGE SQL IMMUTABLE STRICT;
                """,
                """
                CREATE OR REPLACE FUNCTION cast_bigint_pint_to_pint(big_integer_pint_field)
                RETURNS pint_field AS $$
                    SELECT ROW($1.comparator, $1.magnitude::decimal, $1.units)::pint_field;
                $$ LANGUAGE SQL IMMUTABLE STRICT;
                """,

                # Create the casts
                "CREATE CAST (decimal_pint_field AS pint_field) WITH FUNCTION cast_decimal_pint_to_pint(decimal_pint_field) AS IMPLICIT;",
                "CREATE CAST (integer_pint_field AS pint_field) WITH FUNCTION cast_integer_pint_to_pint(integer_pint_field) AS IMPLICIT;",
                "CREATE CAST (big_integer_pint_field AS pint_field) WITH FUNCTION cast_bigint_pint_to_pint(big_integer_pint_field) AS IMPLICIT;",
            ],
            reverse_sql=[
                "DROP CAST IF EXISTS (decimal_pint_field AS pint_field);",
                "DROP CAST IF EXISTS (integer_pint_field AS pint_field);",
                "DROP CAST IF EXISTS (big_integer_pint_field AS pint_field);",
                "DROP FUNCTION IF EXISTS cast_decimal_pint_to_pint(decimal_pint_field);",
                "DROP FUNCTION IF EXISTS cast_integer_pint_to_pint(integer_pint_field);",
                "DROP FUNCTION IF EXISTS cast_bigint_pint_to_pint(big_integer_pint_field);",
                "DROP TYPE IF EXISTS pint_field CASCADE;",
            ],
        ),
        # Convert existing data
        migrations.RunPython(convert_existing_data, reverse_code=migrations.RunPython.noop, atomic=False),
        # Validate conversion
        migrations.RunPython(validate_conversion, reverse_code=migrations.RunPython.noop),
        # Only drop old types after successful conversion
        migrations.RunSQL(
            sql=[
                "DROP TYPE IF EXISTS integer_pint_field CASCADE;",
                "DROP TYPE IF EXISTS big_integer_pint_field CASCADE;",
                "DROP TYPE IF EXISTS decimal_pint_field CASCADE;",
            ],
            reverse_sql=[
                """
                CREATE TYPE integer_pint_field AS (
                    comparator decimal,
                    magnitude integer,
                    units text
                );
                """,
                """
                CREATE TYPE big_integer_pint_field AS (
                    comparator decimal,
                    magnitude bigint,
                    units text
                );
                """,
                """
                CREATE TYPE decimal_pint_field AS (
                    comparator decimal,
                    magnitude decimal,
                    units text
                );
                """,
            ],
        ),
        # Clear OID cache
        migrations.RunPython(clear_oids),
    ]
