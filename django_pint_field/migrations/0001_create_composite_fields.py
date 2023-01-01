from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                (f"CREATE TYPE integer_pint_field as (comparator decimal, magnitude integer, units text)"),
                (f"CREATE TYPE big_integer_pint_field as (comparator decimal, magnitude bigint, units text)"),
                (f"CREATE TYPE decimal_pint_field as (comparator decimal, magnitude decimal, units text)"),
            ],
            reverse_sql=[
                ("DROP TYPE integer_pint_field CASCADE;"),
                ("DROP TYPE big_integer_pint_field CASCADE;"),
                ("DROP TYPE decimal_pint_field CASCADE;"),
            ],
        )
    ]
