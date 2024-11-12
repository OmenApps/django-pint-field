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


def clear_oids(apps, schema_editor):
    """Clear cached OIDs."""
    get_pint_field_oids.cache_clear()


def get_partition_info(cursor, schema: str, table: str) -> typing.Tuple[bool, list, str, str]:
    """Get partition information for a table.

    Returns:
        Tuple of (is_partitioned, partitions, parent_schema, parent_table)
    """
    # First check if this is a partition (child table)
    cursor.execute(
        """
        SELECT pn.nspname, p.relname
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_namespace pn ON pn.oid = p.relnamespace
        WHERE n.nspname = %s AND c.relname = %s;
        """,
        [schema, table],
    )
    result = cursor.fetchone()
    if result:
        # This is a partition, return its parent info
        return False, [], result[0], result[1]

    # Check if this is a partitioned table (parent table)
    cursor.execute(
        """
        SELECT partattrs
        FROM pg_partitioned_table pt
        JOIN pg_class c ON c.oid = pt.partrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s;
        """,
        [schema, table],
    )
    result = cursor.fetchone()
    if not result:
        # Not a partitioned table
        return False, [], None, None

    # Get all partitions of this table
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
        [schema, table],
    )
    partitions = cursor.fetchall()
    return True, partitions, None, None


def add_new_column(cursor, schema: str, table: str, column: str, not_null: bool) -> typing.Tuple[str, str, bool]:
    """Add new pint_field column.

    Returns:
        Tuple of (original_column_name, temp_column_name, is_nullable) or (None, None, None) if column not found
    """
    logger.info("Adding new column for %s.%s.%s", schema, table, column)
    cursor.execute(
        """
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name = %s
        AND lower(column_name) = lower(%s);
        """,
        [schema, table, column],
    )
    result = cursor.fetchone()
    if not result:
        logger.info("Column %s not found in %s.%s - skipping", column, schema, table)
        return None, None, None

    actual_column = result[0]
    is_nullable = result[1] == "YES"
    temp_column = f"{actual_column}_new"

    # Always add column as nullable initially
    cursor.execute(
        f"""
        ALTER TABLE "{schema}"."{table}"
        ADD COLUMN "{temp_column}" pint_field;
        """
    )

    return actual_column, temp_column, is_nullable


def get_actual_column_name(cursor, schema: str, table: str, column: str) -> str:
    """Get the actual case-sensitive column name."""
    logger.info("Checking for column %s in %s.%s", column, schema, table)
    cursor.execute(
        """
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name = %s
        AND lower(column_name) = lower(%s);
        """,
        [schema, table, column],
    )
    result = cursor.fetchone()
    if not result:
        logger.warning("Column %s not found in %s.%s", column, schema, table)
        return None
    return result[0]


def copy_column_data(cursor, schema: str, table: str, old_column: str, new_column: str) -> None:
    """Copy data from old column to new column."""
    logger.info("Copying data from %s.%s.%s to %s", schema, table, old_column, new_column)

    # First copy NULL values to preserve NULL semantics
    cursor.execute(
        f"""
        UPDATE "{schema}"."{table}"
        SET "{new_column}" = NULL
        WHERE "{old_column}" IS NULL;
        """
    )

    # Then copy non-NULL values with conversion
    cursor.execute(
        f"""
        UPDATE "{schema}"."{table}"
        SET "{new_column}" = ROW(
            ("{old_column}").comparator,
            ("{old_column}").magnitude::decimal,
            ("{old_column}").units
        )::pint_field
        WHERE "{old_column}" IS NOT NULL;
        """
    )


def verify_data_copy(cursor, schema: str, table: str, old_column: str, new_column: str) -> bool:
    """Verify data was copied correctly including NULL values."""
    logger.info("Verifying data copy for %s.%s.%s", schema, table, old_column)

    # Check that non-NULL values were copied correctly
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM "{schema}"."{table}"
        WHERE "{old_column}" IS NOT NULL
        AND "{new_column}" IS NULL;
        """
    )
    non_null_correct = cursor.fetchone()[0] == 0

    # Check that NULL values were preserved
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM "{schema}"."{table}"
        WHERE "{old_column}" IS NULL
        AND "{new_column}" IS NOT NULL;
        """
    )
    null_correct = cursor.fetchone()[0] == 0

    return non_null_correct and null_correct


def set_not_null_constraint(cursor, schema: str, table: str, column: str, is_nullable: bool) -> None:
    """Set or remove NOT NULL constraint after data is copied."""
    logger.info("Setting NOT NULL constraint on %s.%s.%s", schema, table, column)
    if not is_nullable:
        cursor.execute(
            f"""
            ALTER TABLE "{schema}"."{table}"
            ALTER COLUMN "{column}" SET NOT NULL;
            """
        )


def convert_table_columns(apps, schema_editor):
    """Convert columns while properly handling partitioned tables."""
    logger.info("Converting columns to pint_field")
    with connection.cursor() as cursor:
        # First get all parent tables (both regular and partitioned)
        cursor.execute(
            """
            WITH parent_tables AS (
                SELECT DISTINCT n.nspname as schema_name,
                       c.relname as table_name,
                       a.attname as column_name,
                       t.typname as type_name,
                       a.attnotnull as not_null
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')
                AND a.attnum > 0
                AND NOT EXISTS (
                    SELECT 1
                    FROM pg_inherits i
                    WHERE i.inhrelid = c.oid
                )
            )
            SELECT * FROM parent_tables
            ORDER BY schema_name, table_name, column_name;
            """
        )
        tables_to_convert = cursor.fetchall()

        # Process each parent table
        for schema, table, column, type_name, not_null in tables_to_convert:
            is_partitioned, partitions, parent_schema, parent_table = get_partition_info(cursor, schema, table)

            if parent_schema and parent_table:
                # This is a partition - skip it as it will be handled through its parent
                continue

            # Add column to parent table
            actual_column, temp_column, is_nullable = add_new_column(cursor, schema, table, column, not_null)
            if not actual_column:
                continue

            logger.info("Converting %s.%s.%s from %s to pint_field", schema, table, actual_column, type_name)

            # Copy data in parent
            copy_column_data(cursor, schema, table, actual_column, temp_column)
            if not verify_data_copy(cursor, schema, table, actual_column, temp_column):
                raise Exception(f"Data copy verification failed for {schema}.{table}.{actual_column}")

            # For partitioned tables, we don't need to add columns to partitions
            # as they inherit from the parent, but we do need to copy data
            if is_partitioned:
                logger.info("Processing partitions for %s.%s", schema, table)
                for part_schema, part_table in partitions:
                    logger.info("Copying data in partition %s.%s", part_schema, part_table)
                    copy_column_data(cursor, part_schema, part_table, actual_column, temp_column)
                    if not verify_data_copy(cursor, part_schema, part_table, actual_column, temp_column):
                        raise Exception(f"Data copy verification failed for partition {part_schema}.{part_table}")

            # Set NOT NULL constraint only if original column was NOT NULL
            if not is_nullable:
                set_not_null_constraint(cursor, schema, table, temp_column, is_nullable=False)


def finalize_column_conversion(apps, schema_editor):
    """Drop old columns and rename new ones, handling partitioned tables correctly."""
    logger.info("Finalizing column conversion")
    with connection.cursor() as cursor:
        # Get all tables with _new columns, excluding system tables/views
        cursor.execute(
            """
            SELECT DISTINCT n.nspname as schema_name,
                   c.relname as table_name,
                   a.attname as column_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE a.attname LIKE '%_new'
            AND a.attnum > 0
            AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            AND c.relkind IN ('r', 'p')  -- Only regular and partitioned tables
            AND NOT EXISTS (
                SELECT 1
                FROM pg_inherits i
                WHERE i.inhrelid = c.oid
            )
            ORDER BY schema_name, table_name, column_name;
            """
        )

        for schema, table, temp_column in cursor.fetchall():
            original_column = temp_column[:-4]  # Remove '_new' suffix
            try:
                # Drop old column with CASCADE to handle dependencies
                cursor.execute(
                    f"""
                    ALTER TABLE "{schema}"."{table}"
                    DROP COLUMN IF EXISTS "{original_column}" CASCADE;
                    """
                )

                # Rename new column to original name
                cursor.execute(
                    f"""
                    ALTER TABLE "{schema}"."{table}"
                    RENAME COLUMN "{temp_column}" TO "{original_column}";
                    """
                )
            except Exception as e:
                logger.error(
                    "Error finalizing column conversion for %s.%s.%s: %s", schema, table, original_column, str(e)
                )
                raise


class Migration(migrations.Migration):
    """Consolidate PintField types into a single composite type."""

    atomic = False

    dependencies = [
        ("django_pint_field", "0001_create_composite_fields"),
    ]

    operations = [
        # First create new type and casting functions
        migrations.RunSQL(
            sql=[
                "DROP TYPE IF EXISTS pint_field CASCADE;",
                """
                CREATE TYPE pint_field AS (
                    comparator decimal,
                    magnitude decimal,
                    units text
                );
                """,
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
        # Add new columns and copy data
        migrations.RunPython(convert_table_columns, reverse_code=migrations.RunPython.noop, atomic=False),
        # Drop old columns and rename new ones
        migrations.RunPython(finalize_column_conversion, reverse_code=migrations.RunPython.noop, atomic=False),
        # Drop old types
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
