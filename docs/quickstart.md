# Quickstart

## Prerequisites

- Python 3.11+
- Django 4.2+
- PostgreSQL (required; composite types are not available in SQLite or MySQL)

Your Django project must be configured to use a PostgreSQL database:

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "your_database",
        "USER": "your_user",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

## Installation

```bash
pip install django-pint-field
```

## Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    "django_pint_field",
    # ...
]
```

## Run Migrations

```bash
python manage.py migrate django_pint_field
```

```{caution}
Failure to run django-pint-field migrations before running migrations for models using PintFields will result in errors. The migration creates a required composite type in your PostgreSQL database.

Previous versions of the package added three composite types to the database. The newest migration modifies the columns with these types to use a single composite type.
```

## Basic Configuration

django-pint-field provides three settings you can add to your `settings.py`:

| Setting                               | Type         | Default                                   | Description                                                             |
| ------------------------------------- | ------------ | ----------------------------------------- | ----------------------------------------------------------------------- |
| `DJANGO_PINT_FIELD_UNIT_REGISTER`     | UnitRegistry | `pint.UnitRegistry(non_int_type=Decimal)` | The unit registry to use throughout your project                        |
| `DJANGO_PINT_FIELD_DECIMAL_PRECISION` | int          | 0                                         | Project-wide decimal precision. If > 0, sets Python's decimal precision |
| `DJANGO_PINT_FIELD_DEFAULT_FORMAT`    | str          | "D"                                       | Default format for displaying Quantity objects                          |

See the [configuration](configuration) page for full details on each setting.

## Quick Example

Define a model with a PintField:

```python
# models.py
from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        default_unit="gram",
        unit_choices=[
            ("Gram", "gram"),
            ("Kilogram", "kilogram"),
            ("Pound", "pound"),
        ],
        blank=True,
        null=True,
        display_decimal_places=2,
        rounding_method="ROUND_HALF_UP",
    )

    def __str__(self):
        return f"{self.name} ({self.weight})"
```

Create instances and query the model:

```python
from decimal import Decimal
from django_pint_field.units import ureg
from .models import Product

# Create a product
Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(Decimal("500"), "gram"),
)

# Query products
heavy_products = Product.objects.filter(
    weight__gte=ureg.Quantity(
        Decimal("1"),
        "kilogram",
    )
)
```

## Verifying Installation

1. Check that the migration has been applied:

```bash
python manage.py showmigrations django_pint_field
```

2. Verify the composite type exists in PostgreSQL. Open a database shell:

```bash
python manage.py dbshell
```

Then run:

```text
\dT+ pint_field
```

3. Test creating a model instance:

```python
from decimal import Decimal
from django_pint_field.units import ureg
from myapp.models import Product

Product.objects.create(
    name="Test Product",
    weight=ureg.Quantity(Decimal("100"), "gram"),
)
```

4. Verify unit conversion:

```python
product = Product.objects.get(name="Test Product")
print(product.weight.quantity.to("kilogram"))  # Should show 0.1 kilogram
print(product.weight.kilogram)  # Alternate method. Should show 0.1 kilogram
```

## Upgrading from Legacy Versions

```{admonition} Upgrading from legacy django-pint-field
:class: dropdown

If you are using [django-pgtrigger](https://django-pgtrigger.readthedocs.io/en/latest/commands/) or other packages that depend on it (e.g. django-pghistory), temporarily uninstall all triggers before running the django-pint-field migrations. Making a backup of your database beforehand is also a good practice. Users freshly installing django-pint-field do not need to worry about this.

Uninstall triggers:

`python manage.py pgtrigger uninstall`

Run migrations:

`python manage.py migrate django_pint_field`

Reinstall triggers:

`python manage.py pgtrigger install`
```

## Next Steps

Continue with the [tutorial](tutorial) for a guided walkthrough, or jump to the [how-to guides](howto-fields) for specific tasks.
