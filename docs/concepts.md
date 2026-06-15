# How django-pint-field Works

This page explains the design decisions and internal architecture of django-pint-field. Understanding these concepts is not required to use the package, but it can help you make better decisions about field configuration, indexing, and performance.

## Why PostgreSQL?

django-pint-field stores quantities using a PostgreSQL [composite type](https://www.postgresql.org/docs/current/rowtypes.html). Composite types let you define a custom data type that bundles multiple values into a single column. This is central to how the package works, and it is a feature that SQLite, MySQL, and other databases do not support.

The alternative would be to store magnitude, units, and comparator in three separate columns. That approach works, but it makes queries harder to write correctly, migrations harder to manage, and it scatters what is conceptually a single value across multiple columns. The composite type keeps everything together.

## The Composite Field

Every PintField stores three components in a single PostgreSQL column:

```sql
CREATE TYPE pint_field AS (
    comparator numeric,  -- magnitude in base units, used for comparisons
    magnitude numeric,   -- the original magnitude the user provided
    units text           -- the original unit string the user provided
);
```

When you save a value like `2.5 pound`, the database stores:

| Component    | Value     | Purpose                                           |
| ------------ | --------- | ------------------------------------------------- |
| `comparator` | `1.13398` | 2.5 pounds converted to kilograms (the base unit) |
| `magnitude`  | `2.5`     | The original number the user entered              |
| `units`      | `"pound"` | The original unit the user chose                  |

The `magnitude` and `units` are preserved exactly as the user provided them, so retrieving a record gives back the same value and unit that were saved. The `comparator` exists solely for database-level operations.

## How Cross-Unit Comparison Works

The `comparator` is what makes it possible to compare and filter values stored in different units. When you write a query like:

```python
Product.objects.filter(weight__gt=ureg.Quantity("1 kilogram"))
```

django-pint-field converts `1 kilogram` to base units (1 kilogram), then compares against the `comparator` column. A product stored as `2.5 pound` has a comparator of `1.13398` kilograms, which is greater than `1` kilogram, so it matches.

This means all lookups (`exact`, `gt`, `gte`, `lt`, `lte`, `range`) work correctly across units without any Python-side conversion. The comparison happens entirely in the database using the indexed `comparator` column.

## The PintFieldProxy

When you access a PintField on a model instance, you don't get a raw Pint `Quantity` object. Instead, you get a `PintFieldProxy` that wraps the Quantity and adds extra functionality.

The proxy supports everything a normal Quantity does, plus attribute-based unit conversion:

```python
product = Product.objects.get(name="Flour")

# Standard Quantity operations
product.weight.magnitude    # Decimal('500.00')
product.weight.units        # gram

# Access the underlying Pint Quantity directly
product.weight.quantity.to("kilogram")  # 0.50 kilogram

# Proxy-specific attribute access
product.weight.kilogram     # 0.50 kilogram (returns a Quantity)
product.weight.kilogram__2  # 0.50 kilogram (returns a rounded Quantity)
```

The proxy also implements comparison and math operators (`__eq__`, `__lt__`, `__add__`, `__mul__`, etc.), so you can compare and combine quantities directly in Python code.

The same proxy is returned whether the instance was loaded from the database or just built in Python - `Product(weight=...)` before `save()`, or the instance returned by `objects.create()`. Because the attribute is always a proxy, reach for `product.weight.quantity` when you need the raw Pint `Quantity` (for example `product.weight.quantity.to("kilogram")` rather than `product.weight.to("kilogram")`): the proxy treats unknown attributes like `to` as unit names, so `.to(...)` is not forwarded.

## Dynamic Unit Properties

When a model class is created, `PintFieldMixin.add_properties()` automatically adds properties for unit conversion. For a field called `weight` with a default unit of `"gram"`, the model gets properties for all units with the same dimensionality (mass), such as:

- `weight__gram`
- `weight__kilogram`
- `weight__pound`
- `weight__ounce`
- (and other mass-compatible units in the registry)

These properties return the field value converted to the specified unit. They work in Django admin `list_display`, templates, and anywhere else you access model attributes.

## The Unit Registry

django-pint-field uses a global [Pint UnitRegistry](https://pint.readthedocs.io/en/stable/) instance to define and resolve units. By default, the package creates a registry configured with `non_int_type=Decimal`, which ensures all numeric operations use Python's `Decimal` type rather than floating-point.

You can replace the default registry with your own via the `DJANGO_PINT_FIELD_UNIT_REGISTER` setting. This is how you add custom units (see [Configuring and Working with PintFields](howto-fields)).

All PintFields in a project share the same registry. If you define custom units, they are available to every field. The registry is initialized once at startup and should not be modified at runtime.

## Why Decimal, Not Float

The package uses Python's `Decimal` type throughout instead of `float`. Floating-point arithmetic can introduce rounding errors that accumulate over conversions:

```python
# float: 0.1 + 0.2 = 0.30000000000000004
# Decimal: Decimal("0.1") + Decimal("0.2") = Decimal("0.3")
```

For physical measurements, these errors can matter, especially when comparing values across units or aggregating large datasets. Using `Decimal` keeps results predictable and precise.

The decimal precision can be configured globally via the `DJANGO_PINT_FIELD_DECIMAL_PRECISION` setting. See [Configuration](configuration) for details.

## Related Pages

- [Terminology and Definitions](terminology) for a glossary of terms used in this documentation
- [API Reference](reference) for the complete class and method reference
- [Configuration](configuration) for all available settings
