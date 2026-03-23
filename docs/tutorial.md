# Tutorial: Your First PintField

This tutorial walks through defining a model with a PintField, creating
instances, retrieving values, converting units, and running basic queries. By
the end you will have a working product catalog that stores weights with full
unit support.

Prerequisites: a Django project with PostgreSQL, django-pint-field installed and
added to `INSTALLED_APPS`, and the django-pint-field migrations applied. See the
[quickstart guide](quickstart) if you have not done that yet.

## Defining the Model

django-pint-field provides two main field types. `IntegerPintField` stores
magnitudes as whole numbers and is a good fit when fractional values do not make
sense (item counts, for example). `DecimalPintField` stores magnitudes as
decimals and gives you control over display precision and rounding.

For a product weight, decimals are the natural choice:

```python
# catalog/models.py

from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        unit_choices=["gram", "kilogram", "pound"],
        display_decimal_places=2,
    )

    def __str__(self):
        return f"{self.name} ({self.weight})"
```

The first positional argument, `"gram"`, is the default unit. `unit_choices`
limits which units are available in forms and the admin. `display_decimal_places`
controls how many decimal places appear when the value is rendered as a string.

After saving the model, generate and apply migrations:

```bash
python manage.py makemigrations catalog
python manage.py migrate
```

## Creating Instances

You can assign a PintField value using a `Quantity` object or a plain string.

```python
from decimal import Decimal
from django_pint_field.units import ureg

# Using a Quantity object
Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(Decimal("500.00"), "gram"),
)

# Using string notation
Product.objects.create(
    name="Sugar",
    weight="750 gram",
)
```

Updating a value works the same way. Assign a new quantity and call `save()`:

```python
product = Product.objects.get(name="Flour")
product.weight = ureg.Quantity(Decimal("1.5"), "kilogram")
product.save()
```

The field accepts any unit compatible with the default unit's dimensionality.
Here we stored the flour weight in kilograms even though the default unit is
grams. Internally, the field converts the value to a base-unit comparator so
that cross-unit lookups work correctly.

## Retrieving and Inspecting Values

When you read a PintField from the database, you get a `PintFieldProxy` object.
It behaves like a quantity but adds some convenient extras.

```python
product = Product.objects.get(name="Flour")

print(product.weight)            # 1.5 kilogram
print(product.weight.magnitude)  # Decimal('1.5')
print(product.weight.units)      # kilogram
```

The underlying Pint `Quantity` is available as `product.weight.quantity` if you
need to pass it to code that expects a raw Pint object.

## Converting Between Units

There are two ways to convert. You can call `.to()` on the underlying quantity,
or you can use the proxy's attribute-access shortcut.

```python
# Using .to() on the quantity
in_grams = product.weight.quantity.to("gram")
print(in_grams)  # 1500.00 gram

# Using attribute access on the proxy
print(product.weight.gram)      # 1500.0 gram
print(product.weight.pound)     # ~3.31 pound
```

The attribute-access style also supports a double-underscore suffix to control
decimal places:

```python
print(product.weight.gram__2)   # 1500.00 gram
print(product.weight.pound__3)  # 3.307 pound
```

You can format the value in its current units the same way, using `digits__N`:

```python
print(product.weight.digits__4)  # 1.5000 kilogram
```

## Basic Queries

django-pint-field supports `exact`, `gt`, `gte`, `lt`, `lte`, `range`, and
`isnull` lookups. Provide a `Quantity` as the lookup value.

```python
from django_pint_field.units import ureg

# Exact match
Product.objects.filter(weight=ureg.Quantity("500 gram"))

# Greater than
Product.objects.filter(weight__gt=ureg.Quantity("1 kilogram"))

# Less than
Product.objects.filter(weight__lt=ureg.Quantity("100 gram"))

# Range
min_w = ureg.Quantity("100 gram")
max_w = ureg.Quantity("1 kilogram")
Product.objects.filter(weight__range=(min_w, max_w))
```

Comparisons work across units automatically. A filter for
`weight__gt=ureg.Quantity("1 kilogram")` will match a product stored as
`"1500 gram"` because the field stores a base-unit comparator internally and all
lookups operate against that comparator.

## Next Steps

You now have a model that stores, retrieves, converts, and queries physical
quantities. From here you can explore:

- [Configuring and Working with PintFields](howto-fields) for custom units, decimal precision, and validation
- [Querying, Filtering, and Aggregating](howto-queries) for aggregations and advanced queries
- [Forms, Widgets, and Templates](howto-forms-templates) for using PintFields in forms
- [Cheatsheet](cheatsheet) for a quick syntax reference
