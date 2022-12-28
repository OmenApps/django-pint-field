from django.db import connection
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql = [
                ("CREATE TYPE integer_pint_field as (magnitude integer, unit char)"),
                ("CREATE TYPE big_integer_pint_field as (magnitude bigint, unit char)"),
                ("CREATE TYPE decimal_pint_field as (magnitude decimal, unit char)"),
            ],
            reverse_sql = [
                ("DROP TYPE integer_pint_field CASCADE;"),
                ("DROP TYPE big_integer_pint_field CASCADE;"),
                ("DROP TYPE decimal_pint_field CASCADE;"),
            ]
        )
    ]
