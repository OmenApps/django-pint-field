# Generated by Django 4.1.4 on 2023-01-01 23:53

from decimal import Decimal

from django.db import migrations, models

import django_pint_field.models


class Migration(migrations.Migration):
    dependencies = [
        ("demoapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DefaultsInModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20)),
                (
                    "weight_int",
                    django_pint_field.models.IntegerPintField(
                        blank=True,
                        default=1,
                        default_unit="gram",
                        null=True,
                        unit_choices=["gram"],
                        verbose_name="gram",
                    ),
                ),
                (
                    "weight_bigint",
                    django_pint_field.models.BigIntegerPintField(
                        blank=True,
                        default=1,
                        default_unit="gram",
                        null=True,
                        unit_choices=["gram"],
                        verbose_name="gram",
                    ),
                ),
                (
                    "weight_decimal",
                    django_pint_field.models.DecimalPintField(
                        blank=True,
                        decimal_places=2,
                        default=Decimal("1.0"),
                        default_unit="gram",
                        max_digits=10,
                        null=True,
                        unit_choices=["gram"],
                        verbose_name="gram",
                    ),
                ),
            ],
        ),
    ]
