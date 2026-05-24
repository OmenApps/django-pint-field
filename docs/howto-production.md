# Performance, Deployment, and Troubleshooting

## Indexing PintField Queries

Since django-pint-field stores quantities as a PostgreSQL composite type with a `comparator` component (the magnitude converted to base units), proper indexing targets that comparator to speed up filtering and ordering.

### Basic Indexes

Because PintField lookups compare against `(field).comparator`, a plain `db_index=True` or `models.Index(fields=["field"])` targets the full composite value, not the comparator expression your queries use. For query acceleration, prefer `PintFieldComparatorIndex`.

```python
from django.db import models
from django_pint_field.indexes import PintFieldComparatorIndex
from django_pint_field.models import DecimalPintField

class OptimizedMeasurement(models.Model):
    value = DecimalPintField("meter", display_decimal_places=2)

    class Meta:
        indexes = [
            PintFieldComparatorIndex(fields=["value"]),
        ]
```

### PintFieldComparatorIndex

`PintFieldComparatorIndex` is a specialized index that targets the `comparator` component directly, giving the query planner a better path for range queries and ordering.

```python
from django.db import models
from django_pint_field.indexes import PintFieldComparatorIndex

class AdvancedMeasurement(models.Model):
    weight = DecimalPintField("gram", display_decimal_places=2)
    height = DecimalPintField("meter", display_decimal_places=2)
    volume = DecimalPintField("liter", display_decimal_places=2)
    temperature = DecimalPintField("celsius", display_decimal_places=2)

    class Meta:
        indexes = [
            # Single field index
            PintFieldComparatorIndex(fields=["weight"]),
            # Multi-field composite index
            PintFieldComparatorIndex(
                fields=["weight", "height"],
                name="measurement_weight_height_idx",
            ),
            # Partial index for non-null weights
            PintFieldComparatorIndex(
                fields=["weight"],
                condition=models.Q(weight__isnull=False),
                name="non_null_weight_idx",
            ),
            # Covering index (avoids table lookups for included columns)
            PintFieldComparatorIndex(
                fields=["volume"],
                include=["id", "temperature"],
                name="volume_covering_idx",
            ),
            # Custom tablespace
            PintFieldComparatorIndex(
                fields=["weight", "volume"],
                db_tablespace="measurement_space",
                name="weight_volume_space_idx",
            ),
        ]
```

### Querying with Indexes

Structure your queries to take advantage of these indexes:

```python
from django.db.models import Q
from django_pint_field.units import ureg

class IndexedQueryOptimizer:
    @staticmethod
    def efficient_multi_field_query(min_weight, max_weight, min_height, max_height):
        """Uses the composite index on weight + height."""
        return AdvancedMeasurement.objects.filter(
            Q(weight__gte=ureg.Quantity(min_weight, "gram"))
            & Q(weight__lte=ureg.Quantity(max_weight, "gram"))
            & Q(height__gte=ureg.Quantity(min_height, "meter"))
            & Q(height__lte=ureg.Quantity(max_height, "meter"))
        ).order_by("weight", "height")

    @staticmethod
    def covering_index_query():
        """Avoids table lookups entirely via the covering index."""
        return AdvancedMeasurement.objects.filter(
            volume__gt=ureg.Quantity("1 liter")
        ).values("id", "temperature")

    @staticmethod
    def partial_index_query():
        """Benefits from the smaller, filtered partial index."""
        return AdvancedMeasurement.objects.filter(
            weight__gt=ureg.Quantity("0 gram")
        ).order_by("weight")
```

### Index Best Practices

Match index field order in your queries. If your index covers `["weight", "height"]`, filter and order by `weight` first, then `height`:

```python
measurements = AdvancedMeasurement.objects.filter(
    weight__gt=ureg.Quantity("100 gram"),
    height__gt=ureg.Quantity("1 meter"),
).order_by("weight", "height")
```

Use covering indexes for fields you read frequently alongside filters. Use partial indexes when most queries target a specific subset (e.g., only positive values).

Monitor index size to balance storage cost against query performance:

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT pg_size_pretty(pg_total_relation_size('measurement_weight_height_idx'));
    """)
    index_size = cursor.fetchone()[0]
```

Multi-field indexes are most effective when all indexed fields appear in the query. If you only ever filter on `weight`, a single-field index is more efficient than a composite one.

## Optimizing Query Patterns

Let the database do the work. Filter using the indexed comparator field rather than pulling rows into Python and converting there.

```python
from django.db.models import Q
from django_pint_field.units import ureg

# Good: uses the indexed comparator field
Measurement.objects.filter(value__gte=ureg.Quantity("10 meter")).select_related()

# Good: combines multiple conditions with Q objects
Measurement.objects.filter(
    Q(value__gte=ureg.Quantity("10 meter"))
    & Q(value__lte=ureg.Quantity("20 meter"))
).select_related()

# Bad: fetches all rows, then converts in a Python loop
[m for m in Measurement.objects.all() if m.value.quantity.to("feet").magnitude > 32.8]

# Good: performs the conversion before querying
Measurement.objects.filter(value__gt=ureg.Quantity("10 meter"))
```

## Bulk Operations

Use `bulk_create` and `bulk_update` inside `transaction.atomic()` to reduce database round trips when handling many records.

```python
from django.db import transaction
from django_pint_field.units import ureg
from typing import List

class BulkOperationHandler:
    @staticmethod
    def bulk_create_measurements(data: List[dict], batch_size=1000):
        """Bulk creation with chunking for large datasets."""
        measurements = []
        for item in data:
            measurements.append(
                Measurement(value=ureg.Quantity(item["value"], item["unit"]))
            )
            if len(measurements) >= batch_size:
                with transaction.atomic():
                    Measurement.objects.bulk_create(measurements, batch_size=batch_size)
                measurements = []
        if measurements:
            with transaction.atomic():
                Measurement.objects.bulk_create(measurements, batch_size=batch_size)

    @staticmethod
    def bulk_update_measurements(queryset, new_value: ureg.Quantity):
        """Bulk update via queryset."""
        with transaction.atomic():
            queryset.update(value=new_value)

    @staticmethod
    def optimized_deletion(criteria: dict):
        """Deletion with criteria inside a transaction."""
        with transaction.atomic():
            Measurement.objects.filter(**criteria).delete()

# Usage
handler = BulkOperationHandler()
handler.bulk_create_measurements([
    {"value": 10, "unit": "meter"},
    {"value": 20, "unit": "meter"},
])
handler.optimized_deletion({"value__lt": ureg.Quantity("5 meter")})
```

## Caching Strategies

Cache converted values to avoid repeated unit conversion for the same record:

```python
from django.core.cache import cache
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg
from typing import Optional

class CachedMeasurement(models.Model):
    value = DecimalPintField("meter", display_decimal_places=2)

    def get_cached_conversion(self, unit: str, timeout: int = 3600) -> Optional[ureg.Quantity]:
        """Get or cache converted value."""
        cache_key = f"measurement_{self.pk}_{unit}"
        cached_value = cache.get(cache_key)
        if cached_value is None and self.value is not None:
            converted = self.value.quantity.to(unit)
            cache.set(cache_key, converted, timeout)
            return converted
        return cached_value

    def clear_conversion_cache(self) -> None:
        """Clear cached conversions."""
        cache.delete_pattern(f"measurement_{self.pk}_*")

    def save(self, *args, **kwargs):
        self.clear_conversion_cache()
        super().save(*args, **kwargs)
```

## Production Setup

### Verifying your setup

django_pint_field registers Django system checks. Run them as part of deploy:

```bash
python manage.py check --database default
```

- **E001** - the default database is not PostgreSQL (hard error).
- **W001** - the `pint_field` composite type is missing from the database.

To create and verify the composite type in one step, run this before migrating
any model that uses a PintField:

```bash
python manage.py setup_pint_field
```

It applies the `django_pint_field` migrations and confirms the `pint_field`
composite type exists (pass `--database <alias>` for a non-default database).

Use `PintFieldMonitor` to track conversion performance and field statistics:

```python
import logging
import time
from django.db.models import Count
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PintFieldMonitor:
    @staticmethod
    def log_conversion_time(func):
        """Decorator to log conversion times."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info("Unit conversion took %.3f seconds", duration)
            return result
        return wrapper

    @staticmethod
    def get_field_statistics(model) -> Dict[str, Any]:
        """Get statistics for PintField usage."""
        stats = {
            "total_records": model.objects.count(),
            "null_values": model.objects.filter(value__isnull=True).count(),
        }
        return stats
```

You can integrate with Sentry or similar services for breadcrumbs on PintField operations:

```python
import sentry_sdk

def log_pint_operation(operation: str, data: Dict[str, Any]) -> None:
    sentry_sdk.add_breadcrumb(
        category="pint_field",
        message=f"PintField operation: {operation}",
        data=data,
        level="info",
    )
```

Things to monitor in production:

- Conversion performance (use `log_conversion_time` on hot paths)
- Database query patterns (watch for N+1 queries involving unit conversion)
- Error rates around unit compatibility and precision issues
- Cache hit rates if using the caching strategy above
- Index usage statistics via PostgreSQL's `pg_stat_user_indexes`

## Backup Strategies

PostgreSQL-native backups such as `pg_dump` preserve the composite type automatically. If you are exporting records to JSON yourself, serialize PintField values as plain magnitude/unit pairs and rebuild `Quantity` objects on restore:

```python
from decimal import Decimal
from typing import Dict, Any
from django_pint_field.units import ureg

class PintFieldBackupHandler:
    def serialize_quantity(self, value) -> Dict[str, Any] | None:
        """Serialize a PintField value for JSON export."""
        if value is None:
            return None
        quantity = value.quantity if hasattr(value, "quantity") else value
        return {
            "magnitude": str(quantity.magnitude),
            "units": str(quantity.units),
        }

    def deserialize_quantity(self, value: Dict[str, Any] | None):
        """Rebuild a Quantity object from exported JSON data."""
        if value is None:
            return None
        return ureg.Quantity(Decimal(value["magnitude"]), value["units"])
```

## Troubleshooting Common Issues

A good first resource for issues with conversions, units, and Quantity objects is the [Pint documentation](https://pint.readthedocs.io/en/stable/).

### Unit Compatibility Issues

Use `check_matching_unit_dimension` to verify that a value's units match a field's base unit before saving:

```python
from django_pint_field.helpers import check_matching_unit_dimension
from django_pint_field.units import ureg

def validate_unit_compatibility(value: ureg.Quantity, base_unit: str) -> bool:
    """Check if units are compatible."""
    try:
        check_matching_unit_dimension(ureg, base_unit, [str(value.units)])
        return True
    except ValidationError:
        return False

# Returns False for incompatible units
validate_unit_compatibility(ureg.Quantity("100 gram"), "meter")
```

### Precision Loss

With `Decimal` values, do not use Python's built-in `round`. Use `Decimal.quantize` instead, which properly truncates and optionally rounds:

```python
from decimal import Decimal, ROUND_HALF_UP

def preserve_precision(value: ureg.Quantity, decimal_places: int = 2) -> ureg.Quantity:
    """Preserve decimal precision."""
    if value is None:
        return None
    magnitude = Decimal(str(value.magnitude))
    rounded = magnitude.quantize(
        Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP
    )
    return ureg.Quantity(rounded, value.units)
```

### Debugging Strategies

**Value inspection** with a `debug_info` method:

```python
class DebugMeasurement(models.Model):
    value = DecimalPintField(default_unit="meter", display_decimal_places=2)

    def debug_info(self) -> dict:
        if self.value is None:
            return {"error": "No value set"}
        return {
            "magnitude": self.value.magnitude,
            "units": str(self.value.units),
            "dimensionality": str(self.value.quantity.dimensionality),
            "base_value": self.value.quantity.to_base_units(),
            "valid_units": [unit for _label, unit in self._meta.get_field("value").unit_choices],
        }
```

**Query logging** decorator to count SQL queries:

```python
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def log_queries(func):
    def wrapper(*args, **kwargs):
        queries_before = len(connection.queries)
        result = func(*args, **kwargs)
        queries_after = len(connection.queries)
        logger.debug(
            f"{func.__name__} executed {queries_after - queries_before} queries"
        )
        for query in connection.queries[queries_before:]:
            logger.debug(f"Query: {query['sql']}")
        return result
    return wrapper

@log_queries
def fetch_measurements():
    return Measurement.objects.filter(value__gt=ureg.Quantity("10 meter"))
```

**Validation testing** to verify conversion accuracy:

```python
from django.test import TestCase

class MeasurementTests(TestCase):
    def test_unit_conversion(self):
        measurement = Measurement.objects.create(value=ureg.Quantity("1000 meter"))
        km_value = measurement.value.quantity.to("kilometer")
        self.assertEqual(km_value.magnitude, 1)
        mile_value = measurement.value.quantity.to("mile")
        self.assertAlmostEqual(mile_value.magnitude, 0.621371, places=6)
```

---

See [Concepts](concepts) for why comparator-based indexing matters.
See [API Reference](reference) for `PintFieldComparatorIndex` parameters.
