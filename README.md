# django-pint-field

[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-pint-field/)
[![PyPI](https://img.shields.io/pypi/v/django-pint-field)](https://pypi.org/project/django-pint-field/)

Store, validate, and convert physical quantities in Django using [Pint](https://pint.readthedocs.io/en/stable/).

## Why Django Pint Field?

Django Pint Field enables you to:

- Store quantities (like 1 gram, 3 miles, 8.120391 angstroms) in your Django models
- Edit quantities in forms with automatic unit conversion
- Compare quantities in different units (e.g., compare weights in pounds vs. kilograms)
- Display quantities in user-preferred units while maintaining accurate comparisons
- Perform aggregations and lookups across different units of measurement

The package uses a Postgres composite field to store both the magnitude and units, along with a base unit value for accurate comparisons. This approach ensures that users can work with their preferred units while maintaining data integrity and comparability. For this reason, the project only works with Postgresql databases.

## Requirements

- Python 3.10+
- Django 4.2+
- PostgreSQL database
- Pint 0.23+

## Installation

```bash
pip install django-pint-field
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_pint_field",
    # ...
]
```

Run migrations:

```bash
python manage.py migrate django_pint_field
```

```{caution}
Failure to run django-pint-field migrations before running migrations for models using PintFields will result in errors. The migration creates a required composite type in your PostgreSQL database.

Previous versions of the package added three composite types to the database. The newest migration modifies the columns with these types to use a single composite type.
```

### Tips for Upgrading from Legacy django-pint-field

```{warning}
If using [django-pgtrigger](https://django-pgtrigger.readthedocs.io/en/latest/commands/) or other packages that depend on it (e.g.: django-pghistory), we highly recommend that you temporarily uninstall all triggers before running the django-pint-field migrations. It is also a good practice to make a backup of your database before running the migration. Users freshly installing `django-pint-field` do not need to worry about this warning.
```

```bash
python manage.py pgtrigger uninstall
```

Then run the migrations:

```bash
python manage.py migrate django_pint_field
```

Reinstall the triggers after the migrations are complete:

```bash
python manage.py pgtrigger install
```

## Quick Start

1. Define your model:

```python
from decimal import Decimal
from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=Decimal("100"))
    weight = DecimalPintField(
        default_unit="gram",
        unit_choices=["gram", "kilogram", "pound", "ounce"],
    )
```

2. Use it in your code:

```python
from django_pint_field.units import ureg

# Create objects
product = Product.objects.create(
    name="Coffee Bag",
    weight=ureg.Quantity(Decimal("340"), "gram"),
)

# Query using different units
products = Product.objects.filter(
    weight__gte=ureg.Quantity(Decimal("0.5"), "kilogram"),
)

# Access values
print(product.weight)  # 3460 gram
print(product.weight.quantity)  # 3460 gram (accessing the Pint Quantity object)
# Convert to different units
print(product.weight.quantity.to("kilogram"))  # 0.346 kilogram
print(product.weight.kilogram)  # 0.346 kilogram
print(product.weight.kilogram__2)  # 0.35 kilogram  (rounded to 2 decimal places)
```

## Features

### Field Types

- **IntegerPintField**: For whole number quantities
- **DecimalPintField**: For precise decimal quantities
- **BigIntegerPintField**: For large whole number quantities (deprecated, use IntegerPintField instead)

### Form Fields and Widgets

- Built-in form fields with unit conversion
- TabledPintFieldWidget for displaying unit conversion tables
- Customizable validation and unit choices

#### Form Fields

- **IntegerPintFormField**: Used in forms with IntegerPintField and BigIntegerPintField.
- **DecimalPintFormField**: Used in forms with DecimalPintField.

#### Widgets

- **PintFieldWidget**: Default widget for all django pint field types.
- **TabledPintFieldWidget**: Provides a table showing conversion to each of the `unit_choices`.

![TabledPintFieldWidget](https://raw.githubusercontent.com/jacklinke/django-pint-field/main/media/TabledPintFieldWidget.png)

### Django REST Framework Integration

```python
from django_pint_field.rest import DecimalPintRestField


class ProductSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField()

    class Meta:
        model = Product
        fields = ["name", "weight"]
```

```{note}
The package is tested to work with both Django REST Framework and Django Ninja.
```

### Supported Lookups

- `exact`
- `gt`, `gte`
- `lt`, `lte`
- `range`
- `isnull`

### Aggregation Support

```python
from django_pint_field.aggregates import PintAvg, PintSum

Product.objects.aggregate(
    avg_weight=PintAvg("weight"),
    total_weight=PintSum("weight"),
)
```

#### Supported Aggregates

- `PintAvg`
- `PintCount`
- `PintMax`
- `PintMin`
- `PintSum`
- `PintStdDev`
- `PintVariance`

## Advanced Usage

### Custom Units

Create your own unit registry:

```python
from pint import UnitRegistry

custom_ureg = UnitRegistry(non_int_type=Decimal)
custom_ureg.define("custom_unit = [custom]")

# In settings.py
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
```

### Indexing

Django Pint Field supports creating indexes on the comparator components of Pint fields. Indexes can improve query performance when filtering, ordering, or joining on Pint field values.

#### Single Field Index

```python
from django_pint_field.indexes import PintFieldComparatorIndex


class Package(models.Model):
    weight = DecimalPintField("gram")

    class Meta:
        indexes = [PintFieldComparatorIndex(fields=["weight"])]
```

#### Multi-Field Index

```python
from django_pint_field.indexes import PintFieldComparatorIndex


class Package(models.Model):
    weight = DecimalPintField("gram")
    volume = DecimalPintField("liter")

    class Meta:
        indexes = [PintFieldComparatorIndex(fields=["weight", "volume"])]
```

You can also use additional index options, as usual. e.g.:

- `name`: Custom index name
- `condition`: Partial index condition
- `include`: Additional columns to include in the index
- `db_tablespace`: Custom tablespace for the index

### Settings

```python
# settings.py

# Set decimal precision for the entire project
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 40

# Configure custom unit registry
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg

# Set default format for quantity display
DJANGO_PINT_FIELD_DEFAULT_FORMAT = "D"  # Options: D, P, ~P, etc.
```

## Credits

Modified from [django-pint](https://github.com/CarliJoy/django-pint) with a focus on composite field storage and enhanced comparison capabilities.
