import functools

from django.db import connections, migrations


def get_type_oids(connection_alias, type_name):
    # From: https://github.com/django/django/blob/main/django/contrib/postgres/signals.py
    with connections[connection_alias].cursor() as cursor:
        cursor.execute("SELECT oid, typarray FROM pg_type WHERE typname = %s", (type_name,))
        oids = []
        array_oids = []
        for row in cursor:
            oids.append(row[0])
            array_oids.append(row[1])
        return tuple(oids), tuple(array_oids)


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
    # Clear cached, stale oids.
    get_integer_pint_field_oids.cache_clear()
    get_big_integer_pint_field_oids.cache_clear()
    get_decimal_pint_field_oids.cache_clear()


class Migration(migrations.Migration):
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
