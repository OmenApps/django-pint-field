"""Tests for indexing models with Pint fields."""

import pytest
from django.db import connection
from django.db import migrations
from django.db import models
from django.db.models import Q

from django_pint_field.indexes import PintFieldComparatorIndex
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class SingleFieldModel(models.Model):
    """Model with a single Pint field."""

    measurement = DecimalPintField(default_unit="meter", max_digits=10, decimal_places=2)

    class Meta:
        """Meta class for SingleFieldModel."""

        indexes = [PintFieldComparatorIndex(fields=["measurement"])]
        app_label = "test_indexes"


class MultiFieldModel(models.Model):
    """Model with multiple Pint fields."""

    weight = DecimalPintField(default_unit="gram", max_digits=10, decimal_places=2)
    height = DecimalPintField(default_unit="meter", max_digits=10, decimal_places=2)

    class Meta:
        """Meta class for MultiFieldModel."""

        indexes = [PintFieldComparatorIndex(fields=["weight", "height"], name="weight_height_idx")]
        app_label = "test_indexes"


class ConditionalIndexModel(models.Model):
    """Model with a conditional index."""

    weight = DecimalPintField(default_unit="gram", max_digits=10, decimal_places=2)

    class Meta:
        """Meta class for ConditionalIndexModel."""

        indexes = [
            PintFieldComparatorIndex(
                fields=["weight"], condition=Q(weight__gt=ureg.Quantity("0 gram")), name="positive_weight_idx"
            )
        ]
        app_label = "test_indexes"


test_migration = migrations.Migration("test_indexes", "0001_initial")

test_migration.operations = [
    migrations.CreateModel(
        name="SingleFieldModel",
        fields=[
            ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("measurement", DecimalPintField(default_unit="meter", max_digits=10, decimal_places=2)),
        ],
    ),
    migrations.CreateModel(
        name="MultiFieldModel",
        fields=[
            ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("weight", DecimalPintField(default_unit="gram", max_digits=10, decimal_places=2)),
            ("height", DecimalPintField(default_unit="meter", max_digits=10, decimal_places=2)),
        ],
    ),
    migrations.CreateModel(
        name="ConditionalIndexModel",
        fields=[
            ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("weight", DecimalPintField(default_unit="gram", max_digits=10, decimal_places=2)),
        ],
    ),
]


@pytest.fixture(autouse=True)
def setup_test_models(django_db_setup, django_db_blocker):
    """Set up test models in the database."""
    with django_db_blocker.unblock():
        # Create tables for test models
        with connection.schema_editor() as schema_editor:
            for model in [SingleFieldModel, MultiFieldModel, ConditionalIndexModel]:
                if model._meta.db_table not in connection.introspection.table_names():
                    schema_editor.create_model(model)


@pytest.mark.django_db
class TestPintFieldComparatorIndex:
    """Test cases for PintFieldComparatorIndex."""

    def test_conditional_index_creation(self, setup_test_models):
        """Test creation of conditional index."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = 'test_indexes_conditionalindexmodel'
                AND indexname = 'positive_weight_idx'
                AND indexdef LIKE '%WHERE%'
            """
            )
            assert cursor.fetchone()[0] == 1

    @pytest.mark.parametrize(
        "model_class,field_names,sample_data",
        [
            (SingleFieldModel, ["measurement"], {"measurement": "10 meter"}),
            (MultiFieldModel, ["weight", "height"], {"weight": "100 gram", "height": "2 meter"}),
            (ConditionalIndexModel, ["weight"], {"weight": "25 gram"}),
        ],
    )
    def test_index_usage_in_queries(self, setup_test_models, model_class, field_names, sample_data):
        """Test index usage in queries."""
        # Insert multiple instances to populate the table
        instances = []
        for i in range(1000):
            instance = model_class()
            for field, value in sample_data.items():
                setattr(instance, field, ureg.Quantity(value) + i * ureg.Quantity(value))
            instances.append(instance)
        model_class.objects.bulk_create(instances)

        # Query using the first field (which should use the index)
        first_field = field_names[0]
        first_value = getattr(instance, first_field)

        with connection.cursor() as cursor:
            # Force analyze to ensure accurate query plans
            cursor.execute(f"ANALYZE {model_class._meta.db_table}")

        # Use Django's query.explain() to check index usage
        queryset = model_class.objects.filter(**{f"{first_field}__gt": first_value})
        explain_output = queryset.explain(analyze=True)

        # Check if index scan is being used
        assert "Index Scan" in explain_output

    def test_automatic_index_naming(self):
        """Test automatic index naming."""
        index = PintFieldComparatorIndex(fields=["field1", "field2"])
        assert not index.name  # Should be auto-generated during SQL creation

        # Test SQL generation includes auto-generated name
        sql = index.create_sql(SingleFieldModel, connection.schema_editor())
        assert "CREATE INDEX" in sql
        assert "_field1_field2_comparator_idx" in sql

    @pytest.mark.parametrize(
        "fields,expected",
        [
            # Valid cases
            (["field1"], True),
            (["field1", "field2"], True),
            (("field1", "field2"), True),
            # Invalid cases
            ([], False),
            ("field1", False),
            (None, False),
        ],
    )
    def test_field_validation(self, fields, expected):
        """Test field validation."""
        if expected:
            PintFieldComparatorIndex(fields=fields)
        else:
            with pytest.raises(ValueError):
                PintFieldComparatorIndex(fields=fields)

    def test_single_field_index_creation(self, setup_test_models):
        """Test creation of single-field index."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = 'test_indexes_singlefieldmodel'
                AND indexdef LIKE '%(measurement).comparator%'
            """
            )
            assert cursor.fetchone()[0] == 1

    def test_multi_field_index_creation(self, setup_test_models):
        """Test creation of multi-field index."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = 'test_indexes_multifieldmodel'
                AND indexname = 'weight_height_idx'
                AND indexdef LIKE '%(weight).comparator%'
                AND indexdef LIKE '%(height).comparator%'
            """
            )
            assert cursor.fetchone()[0] == 1

    @pytest.mark.parametrize(
        "include,tablespace,condition",
        [
            (("id",), None, None),
            ((), "test_space", None),
            ((), None, Q(measurement__gt=ureg.Quantity("0 meter"))),
            (("id",), "test_space", Q(measurement__gt=ureg.Quantity("0 meter"))),
        ],
    )
    def test_index_options(self, include, tablespace, condition):
        """Test index options."""
        index = PintFieldComparatorIndex(
            fields=["field"], name="test_idx", include=include, db_tablespace=tablespace, condition=condition
        )

        # Test deconstruction
        path, args, kwargs = index.deconstruct()
        assert path == "django_pint_field.indexes.PintFieldComparatorIndex"
        assert kwargs["fields"] == ["field"]
        assert kwargs["name"] == "test_idx"
        assert kwargs["include"] == include
        assert kwargs["db_tablespace"] == tablespace
        assert kwargs["condition"] == condition

    def test_remove_sql_generation(self):
        """Test SQL generation for removing the index."""
        index = PintFieldComparatorIndex(fields=["measurement"], name="test_remove_idx")
        sql = index.remove_sql(SingleFieldModel, connection.schema_editor())
        assert "DROP INDEX IF EXISTS" in sql
        assert "test_remove_idx" in sql
