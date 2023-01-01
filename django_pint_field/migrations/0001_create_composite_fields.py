from django.db import migrations
from django.conf import settings


comparator_precision = getattr(settings, "DJANGO_PINT_FIELD_COMPARATOR_PRECISION", 28)
comparator_scale = getattr(settings, "DJANGO_PINT_FIELD_COMPARATOR_SCALE", 16)

decimal_pint_field_precision = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_FIELD_PRECISION", 16)
decimal_pint_field_scale = getattr(settings, "DJANGO_PINT_FIELD_DECIMAL_FIELD_SCALE", 4)


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    f"CREATE TYPE integer_pint_field as (comparator decimal({comparator_precision}, {comparator_scale}), magnitude integer, units text)"
                ),
                (
                    f"CREATE TYPE big_integer_pint_field as (comparator decimal({comparator_precision}, {comparator_scale}), magnitude bigint, units text)"
                ),
                (
                    f"CREATE TYPE decimal_pint_field as (comparator decimal({comparator_precision}, {comparator_scale}), magnitude decimal({decimal_pint_field_precision}, {decimal_pint_field_scale}), units text)"
                ),
            ],
            reverse_sql=[
                ("DROP TYPE integer_pint_field CASCADE;"),
                ("DROP TYPE big_integer_pint_field CASCADE;"),
                ("DROP TYPE decimal_pint_field CASCADE;"),
            ],
        )
    ]
