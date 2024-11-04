import functools

from django.contrib.postgres.signals import get_type_oids
from django.db import migrations
from django.db.backends.base.base import NO_DB_ALIAS
from psycopg.types import CompositeInfo, TypeInfo, hstore, register_composite

# See: https://github.com/django/django/blob/main/django/contrib/postgres/signals.py
# See: https://www.psycopg.org/psycopg3/docs/basic/pgtypes.html


@functools.lru_cache
def get_integer_pint_field_oids(connection_alias):
    """Return field and field array OIDs."""
    return get_type_oids(connection_alias, "integer_pint_field")


@functools.lru_cache
def get_big_integer_pint_field_oids(connection_alias):
    """Return field and field array OIDs."""
    return get_type_oids(connection_alias, "big_integer_pint_field")


@functools.lru_cache
def get_decimal_pint_field_oids(connection_alias):
    """Return field and field array OIDs."""
    return get_type_oids(connection_alias, "decimal_pint_field")


def clear_oids(apps, schema_editor):
    """Clear cached, stale oids."""
    get_integer_pint_field_oids.cache_clear()
    get_big_integer_pint_field_oids.cache_clear()
    get_decimal_pint_field_oids.cache_clear()


def register_type_handlers(connection, **kwargs):
    if connection.vendor != "postgresql" or connection.alias == NO_DB_ALIAS:
        return

    # register oids for integer_pint_field
    integer_pint_field = CompositeInfo.fetch(connection.connection, "integer_pint_field")
    register_composite(integer_pint_field, connection.connection)

    # register oids for big_integer_pint_field
    big_integer_pint_field = CompositeInfo.fetch(connection.connection, "big_integer_pint_field")
    register_composite(big_integer_pint_field, connection.connection)

    # register oids for decimal_pint_field
    decimal_pint_field = CompositeInfo.fetch(connection.connection, "decimal_pint_field")
    register_composite(decimal_pint_field, connection.connection)


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                ("DROP TYPE IF EXISTS integer_pint_field CASCADE;"),
                ("DROP TYPE IF EXISTS big_integer_pint_field CASCADE;"),
                ("DROP TYPE IF EXISTS decimal_pint_field CASCADE;"),
                ("CREATE TYPE integer_pint_field AS (comparator decimal, magnitude integer, units text);"),
                ("CREATE TYPE big_integer_pint_field as (comparator decimal, magnitude bigint, units text);"),
                ("CREATE TYPE decimal_pint_field as (comparator decimal, magnitude decimal, units text);"),
            ],
            reverse_sql=[
                ("DROP TYPE IF EXISTS integer_pint_field CASCADE;"),
                ("DROP TYPE IF EXISTS big_integer_pint_field CASCADE;"),
                ("DROP TYPE IF EXISTS decimal_pint_field CASCADE;"),
            ],
        ),
        migrations.RunPython(clear_oids),
    ]
