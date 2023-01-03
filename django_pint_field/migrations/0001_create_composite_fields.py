from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    """
                    DO $$ BEGIN
                        CREATE TYPE integer_pint_field AS (comparator decimal, magnitude integer, units text);
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                    """
                ),
                (
                    """
                    DO $$ BEGIN
                        CREATE TYPE big_integer_pint_field as (comparator decimal, magnitude bigint, units text);
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                    """
                ),
                (
                    """
                    DO $$ BEGIN
                        CREATE TYPE decimal_pint_field as (comparator decimal, magnitude decimal, units text);
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                    """
                ),
            ],
            # reverse_sql=[
            #     ("DROP TYPE integer_pint_field CASCADE;"),
            #     ("DROP TYPE big_integer_pint_field CASCADE;"),
            #     ("DROP TYPE decimal_pint_field CASCADE;"),
            # ],
        )
    ]
