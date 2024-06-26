# Generated by Django 4.1.5 on 2023-01-28 14:16

from django.db import migrations

import django_pint_field.models


class Migration(migrations.Migration):
    dependencies = [
        ("demoapp", "0004_djangopintfieldwidgetcomparisonmodel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="tabled_weight_bigint",
            field=django_pint_field.models.BigIntegerPintField(
                blank=True,
                default_unit="gram",
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="tabled_weight_decimal",
            field=django_pint_field.models.DecimalPintField(
                blank=True,
                decimal_places=2,
                default_unit="gram",
                max_digits=10,
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="tabled_weight_int",
            field=django_pint_field.models.IntegerPintField(
                blank=True,
                default_unit="gram",
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="weight_bigint",
            field=django_pint_field.models.BigIntegerPintField(
                blank=True,
                default_unit="gram",
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="weight_decimal",
            field=django_pint_field.models.DecimalPintField(
                blank=True,
                decimal_places=2,
                default_unit="gram",
                max_digits=10,
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
        migrations.AlterField(
            model_name="djangopintfieldwidgetcomparisonmodel",
            name="weight_int",
            field=django_pint_field.models.IntegerPintField(
                blank=True,
                default_unit="gram",
                null=True,
                unit_choices=["gram", "kilogram", "milligram", "pounds"],
                verbose_name="gram",
            ),
        ),
    ]
