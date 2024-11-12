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


def get_partition_info(cursor, schema: str, table: str) -> typing.Tuple[bool, list]:
    """Get partition information for a table."""
    cursor.execute(
        """
        SELECT partattrs, partstrat
        FROM pg_partitioned_table pt
        JOIN pg_class c ON c.oid = pt.partrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s;
        """,
        [schema, table],
    )
    result = cursor.fetchone()

    if not result:
        return False, []

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
    return True, partitions


def add_new_column(cursor, schema: str, table: str, column: str, is_nullable: bool) -> str:
    """Add new pint_field column."""
    actual_column = get_actual_column_name(cursor, schema, table, column)
    if not actual_column:
        return None

    temp_column = f"{actual_column}_new"
    nullable_str = "" if is_nullable else " NOT NULL"

    cursor.execute(
        f"""
        ALTER TABLE "{schema}"."{table}"
        ADD COLUMN "{temp_column}" pint_field{nullable_str};
        """
    )
    return temp_column


def get_actual_column_name(cursor, schema: str, table: str, column: str) -> str:
    """Get the actual case-sensitive column name."""
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
    """Verify data was copied correctly."""
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM "{schema}"."{table}"
        WHERE "{old_column}" IS NOT NULL
        AND "{new_column}" IS NULL;
        """
    )
    return cursor.fetchone()[0] == 0


def convert_table_columns(apps, schema_editor):
    """First phase: Add new columns to all tables."""
    with connection.cursor() as cursor:
        # Get all tables using our types
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
                   t.typname AS type_name,
                   a.attnotnull AS not_null
            FROM inheritance_chain ic
            JOIN pg_attribute a ON a.attrelid = ic.oid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE t.typname IN ('integer_pint_field', 'big_integer_pint_field', 'decimal_pint_field')
            AND a.attnum > 0
            ORDER BY ic.table_schema, ic.table_name, a.attname;
            """
        )
        tables_to_convert = cursor.fetchall()

        for schema, table, column, type_name, not_null in tables_to_convert:
            is_partitioned, partitions = get_partition_info(cursor, schema, table)

            # Add new column to parent table
            temp_column = add_new_column(cursor, schema, table, column, not not_null)
            if not temp_column:
                continue

            # Copy data in parent
            copy_column_data(cursor, schema, table, column, temp_column)
            if not verify_data_copy(cursor, schema, table, column, temp_column):
                raise Exception(f"Data copy verification failed for {schema}.{table}.{column}")

            if is_partitioned:
                for part_schema, part_table in partitions:
                    logger.info("Processing partition %s.%s", part_schema, part_table)
                    copy_column_data(cursor, part_schema, part_table, column, temp_column)
                    if not verify_data_copy(cursor, part_schema, part_table, column, temp_column):
                        raise Exception(f"Data copy verification failed for partition {part_schema}.{part_table}")


def finalize_column_conversion(apps, schema_editor):
    """Second phase: Drop old columns and rename new ones."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ic.table_schema,
                   ic.table_name,
                   a.attname AS column_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE a.attname LIKE '%_new'
            AND a.attnum > 0
            ORDER BY ic.table_schema, ic.table_name, a.attname;
            """
        )

        for schema, table, temp_column in cursor.fetchall():
            original_column = temp_column[:-4]  # Remove '_new' suffix
            try:
                # Drop old column
                cursor.execute(
                    f"""
                    ALTER TABLE "{schema}"."{table}"
                    DROP COLUMN IF EXISTS "{original_column}" CASCADE;
                    """
                )

                # Rename new column
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
