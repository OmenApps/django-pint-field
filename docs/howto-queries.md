# Querying, Filtering, and Aggregating

All PintField lookups compare against the stored **comparator** value, which is always
expressed in base units. This means a filter using kilograms and a filter using grams
will both resolve correctly against the same column, with no manual conversion required
on your part.

The examples below assume a model like this:

```python
from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
        unit_choices=["gram", "kilogram", "pound"],
    )
```

## Filtering by Exact Value

```python
from decimal import Decimal
from django_pint_field.units import ureg

# Explicit Decimal magnitude
Product.objects.filter(weight__exact=ureg.Quantity(Decimal("500.00"), "gram"))

# String shorthand (Pint parses the magnitude and unit)
Product.objects.filter(weight=ureg.Quantity("500.00 gram"))
```

The `__exact` lookup is the default, so `weight=` and `weight__exact=` are equivalent.

## Filtering by Comparison

Comparison lookups work across units transparently. When you pass a Quantity in
kilograms, the field converts it to the base-unit comparator before hitting the
database. A query for `weight__gt=1 kilogram` and `weight__gt=1000 gram` produce
the same SQL.

```python
# Greater than
Product.objects.filter(weight__gt=ureg.Quantity(Decimal("1.000"), "kilogram"))

# Greater than or equal to
Product.objects.filter(weight__gte=ureg.Quantity("1.000 kilogram"))

# Less than
Product.objects.filter(weight__lt=ureg.Quantity(Decimal("500.00"), "gram"))

# Less than or equal to
Product.objects.filter(weight__lte=ureg.Quantity("500.00 gram"))
```

## Filtering by Range

Range queries accept a two-element tuple of Quantity objects. The units do not need
to match each other; each boundary is independently converted to the comparator.

```python
min_weight = ureg.Quantity(Decimal("100.00"), "gram")
max_weight = ureg.Quantity(Decimal("1.000"), "kilogram")
Product.objects.filter(weight__range=(min_weight, max_weight))
```

## Checking for Null Values

If the field was defined with `null=True`, you can filter on presence:

```python
# Products with no weight recorded
Product.objects.filter(weight__isnull=True)

# Products that do have a weight
Product.objects.filter(weight__isnull=False)
```

## Combining Filters

Multiple keyword arguments in the same `.filter()` call are ANDed together.
For OR logic, use Django's `Q` objects.

```python
from django.db.models import Q

# AND: products between 250 g and 750 g
medium_products = Product.objects.filter(
    weight__gt=ureg.Quantity(Decimal("250.00"), "gram"),
    weight__lt=ureg.Quantity(Decimal("750.00"), "gram"),
)

# OR: products lighter than 100 g or heavier than 1 kg
mixed_products = Product.objects.filter(
    Q(weight__lt=ureg.Quantity(Decimal("100.00"), "gram"))
    | Q(weight__gt=ureg.Quantity(Decimal("1.000"), "kilogram"))
)
```

You can combine PintField lookups with lookups on regular fields in the same query:

```python
light_named = Product.objects.filter(
    name__icontains="flour",
    weight__lt=ureg.Quantity(Decimal("500.00"), "gram"),
)
```

## Using Aggregations

django-pint-field ships with unit-aware aggregate functions. Each one operates on
the comparator column and returns a Quantity (except `PintCount`, which returns an
integer).

```python
from django_pint_field.aggregates import (
    PintAvg,
    PintCount,
    PintMax,
    PintMin,
    PintStdDev,
    PintSum,
    PintVariance,
)

# Count non-null weights
Product.objects.aggregate(count=PintCount("weight"))

# Average weight
Product.objects.aggregate(avg=PintAvg("weight"))

# Total weight
Product.objects.aggregate(total=PintSum("weight"))

# Maximum weight
Product.objects.aggregate(max_w=PintMax("weight"))

# Minimum weight
Product.objects.aggregate(min_w=PintMin("weight"))

# Standard deviation (population by default; pass sample=True for sample std dev)
Product.objects.aggregate(std=PintStdDev("weight"))
Product.objects.aggregate(std=PintStdDev("weight", sample=True))

# Variance (population by default; pass sample=True for sample variance)
Product.objects.aggregate(var=PintVariance("weight"))
Product.objects.aggregate(var=PintVariance("weight", sample=True))
```

## Combining Aggregates with Unit Conversion

You can request several aggregates at once and convert the results to whatever unit
suits your display needs.

```python
from django_pint_field.aggregates import PintAvg, PintCount, PintMax, PintMin, PintSum


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        default_unit="gram",
        display_decimal_places=2,
        rounding_method="ROUND_HALF_UP",
    )

    @classmethod
    def get_weight_statistics(cls):
        """Aggregate weights and convert each result to a useful unit."""
        stats = cls.objects.aggregate(
            total_weight=PintSum("weight"),
            average_weight=PintAvg("weight"),
            min_weight=PintMin("weight"),
            max_weight=PintMax("weight"),
            product_count=PintCount("weight"),
        )

        return {
            "total": stats["total_weight"].quantity.to("kilogram"),
            "average": stats["average_weight"].quantity.to("gram"),
            "min": stats["min_weight"].quantity.to("gram"),
            "max": stats["max_weight"].quantity.to("kilogram"),
            "count": stats["product_count"],
        }
```

The same pattern works when you have multiple PintFields on a model. Here, weight and
volume aggregates feed into a derived density calculation:

```python
from django_pint_field.aggregates import PintAvg, PintCount, PintSum


class Shipment(models.Model):
    weight = DecimalPintField(default_unit="kilogram", display_decimal_places=2)
    volume = DecimalPintField(default_unit="cubic_meter", display_decimal_places=3)

    @classmethod
    def get_shipping_metrics(cls):
        """Aggregate shipments and derive average density."""
        metrics = cls.objects.aggregate(
            total_weight=PintSum("weight"),
            avg_weight=PintAvg("weight"),
            total_volume=PintSum("volume"),
            avg_volume=PintAvg("volume"),
            shipment_count=PintCount("id"),
        )

        if metrics["shipment_count"] > 0:
            total_weight_kg = metrics["total_weight"].quantity.to("kilogram")
            total_volume_m3 = metrics["total_volume"].quantity.to("cubic_meter")
            avg_density = (total_weight_kg / total_volume_m3).to("kg/m**3")
        else:
            avg_density = ureg.Quantity(0, "kg/m**3")

        return {
            **metrics,
            "average_density": avg_density,
        }
```

## Advanced Aggregation Patterns

### Parameterized output units

When you want the caller to control which unit the results come back in, accept
the unit as a function argument and convert after aggregation:

```python
from django_pint_field.aggregates import PintAvg, PintMax, PintMin, PintSum


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_weight = DecimalPintField(default_unit="gram", display_decimal_places=2)

    @classmethod
    def get_inventory_analysis(cls, output_unit="kilogram"):
        """
        Aggregate inventory weights and convert results to the requested unit.

        Args:
            output_unit: The unit string for all weight outputs.
        """
        base_stats = cls.objects.aggregate(
            total_items=models.Sum("quantity"),
            avg_unit_weight=PintAvg("unit_weight"),
            heaviest_unit=PintMax("unit_weight"),
            lightest_unit=PintMin("unit_weight"),
        )

        return {
            "total_items": base_stats["total_items"],
            "avg_unit_weight": base_stats["avg_unit_weight"].quantity.to(output_unit),
            "heaviest_unit": base_stats["heaviest_unit"].quantity.to(output_unit),
            "lightest_unit": base_stats["lightest_unit"].quantity.to(output_unit),
        }
```

### Choosing the output unit by magnitude

If the average measurement is large, display in kilograms; if small, display in grams.
This avoids showing values like "0.003 kilogram" or "450000 gram":

```python
import logging

from django_pint_field.aggregates import (
    PintAvg,
    PintCount,
    PintStdDev,
    PintSum,
    PintVariance,
)

logger = logging.getLogger(__name__)


class WeightMeasurement(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = DecimalPintField(default_unit="gram", display_decimal_places=2)

    @classmethod
    def analyze_measurements(cls, start_date=None, end_date=None):
        """
        Analyze weight measurements over an optional date window.
        Automatically picks grams or kilograms for readability.
        """
        queryset = cls.objects.all()

        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        try:
            stats = queryset.aggregate(
                count=PintCount("weight"),
                total=PintSum("weight"),
                average=PintAvg("weight"),
                std_dev=PintStdDev("weight"),
                variance=PintVariance("weight"),
            )

            if stats["average"]:
                avg_magnitude = stats["average"].quantity.to("gram").magnitude

                if avg_magnitude > 1000:
                    unit = "kilogram"
                else:
                    unit = "gram"

                stats = {
                    "count": stats["count"],
                    "total": stats["total"].quantity.to(unit),
                    "average": stats["average"].quantity.to(unit),
                    "std_dev": stats["std_dev"].quantity.to(unit),
                    "variance": stats["variance"],
                    "unit": unit,
                }

            return stats

        except Exception as e:
            logger.error(f"Error analyzing measurements: {str(e)}")
            return None
```

## Unsupported Lookups

PintFields store composite types (comparator, magnitude, units), not simple text or
date values. The following lookups do not apply and will raise a
`PintFieldLookupError` if you attempt them:

- `contains`, `icontains`
- `startswith`, `istartswith`
- `endswith`, `iendswith`
- `in`
- `regex`, `iregex`
- `search`, `isearch`
- `date`, `year`, `iso_year`, `month`, `quarter`, `week`, `week_day`, `iso_week_day`, `day`
- `hour`, `minute`, `second`
- `time`

Stick to the supported lookups: `exact`, `gt`, `gte`, `lt`, `lte`, `range`, and
`isnull`.

## Best Practices

**Index your PintFields for faster queries.** Use `PintFieldComparatorIndex` to create
an index on the comparator component, which is what all lookups and ordering
operate against. See [Production Deployment](howto-production) for details.

```python
from django_pint_field.indexes import PintFieldComparatorIndex


class InventoryItem(models.Model):
    weight = DecimalPintField("gram", display_decimal_places=2)

    class Meta:
        indexes = [
            PintFieldComparatorIndex(fields=["weight"]),
        ]
```

**Use `iterator()` for large result sets.** When you need to loop over thousands of
rows and convert units on each one, `iterator()` avoids loading everything into memory
at once:

```python
for item in InventoryItem.objects.all().iterator():
    converted = item.weight.kilogram
    print(f"Original: {item.weight}, Converted: {converted}")
```

**Build reusable range-query helpers.** Wrapping range logic in a classmethod keeps
your view code clean and ensures consistent precision handling:

```python
from decimal import Decimal
from django.core.exceptions import ValidationError
from django_pint_field.units import ureg


class Product(models.Model):
    weight = DecimalPintField("gram", display_decimal_places=2)

    @classmethod
    def get_by_weight_range(cls, min_weight, max_weight, unit="gram", precision=2):
        """
        Query products within a weight range, with explicit precision control.
        """
        try:
            fmt = Decimal(f"0.{'0' * precision}")
            min_q = ureg.Quantity(Decimal(min_weight).quantize(fmt), unit)
            max_q = ureg.Quantity(Decimal(max_weight).quantize(fmt), unit)
            return cls.objects.filter(weight__gte=min_q, weight__lte=max_q)
        except Exception as e:
            raise ValidationError(f"Invalid weight range: {str(e)}")

    @classmethod
    def get_weight_distribution(cls, ranges, unit="kilogram", precision=3):
        """
        Count products in each weight bucket.

        Args:
            ranges: list of (min, max) tuples in the given unit.
            unit: the unit for the range boundaries.
            precision: decimal places for quantizing boundaries.
        """
        distribution = {}
        for min_val, max_val in ranges:
            fmt = Decimal(f"0.{'0' * precision}")
            min_dec = Decimal(min_val).quantize(fmt)
            max_dec = Decimal(max_val).quantize(fmt)
            count = cls.get_by_weight_range(min_dec, max_dec, unit, precision).count()
            distribution[f"{min_dec}-{max_dec} {unit}"] = count
        return distribution
```

**Keep units compatible in your queries.** You can freely mix grams and kilograms
(or any units of the same dimensionality) in lookups because the comparator handles
conversion. However, passing a length Quantity to a weight field will raise an error.
Validate dimensionality before querying if the unit comes from user input.

---

- See [API Reference](reference) for the complete lookup and aggregate API.
- See [Concepts](concepts) for how the comparator enables cross-unit queries.
