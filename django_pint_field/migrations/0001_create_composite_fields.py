from django.db import migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                ("CREATE TYPE integer_pint_field as (magnitude integer, units text)"),
                ("CREATE TYPE big_integer_pint_field as (magnitude bigint, units text)"),
                ("CREATE TYPE decimal_pint_field as (magnitude decimal, units text)"),
            ],
            reverse_sql=[
                ("DROP TYPE integer_pint_field CASCADE;"),
                ("DROP TYPE big_integer_pint_field CASCADE;"),
                ("DROP TYPE decimal_pint_field CASCADE;"),
            ],
        )
    ]
