# django-pint-field

Use pint with Django's ORM

Modified from the fantastic [django-pint](https://github.com/CarliJoy/django-pint) with different goals.

Unlike django-pint, in this project we use a composite field to store both the magnitude and value of the field, along with the equivalent value in base units for lookups. For this reason, the project only works with Postgresql databases. It ensures that the units your users want to use are the units they see, while still allowing accurate comparisons of one quantity to another.

## Install

`pip install django_pint_field`


## Usage

```python
from decimal import Decimal
from django_pint_field.units import ureg
Quantity = ureg.Quantity

# Start by creating a few Pint Quantity objects
extra_small = Quantity(1 * ureg.gram)
small = Quantity(10 * ureg.gram)
medium = Quantity(100 * ureg.gram)
large = Quantity(1000 * ureg.gram)
extra_large = Quantity(10000 * ureg.gram)

# Create a couple objects
IntegerPintFieldSaveModel.objects.create(name="small", weight=small)
IntegerPintFieldSaveModel.objects.create(name="large", weight=large)

# Perform some queries
IntegerPintFieldSaveModel.objects.filter(weight__gt=medium)
<QuerySet [<IntegerPintFieldSaveModel: large>]>

IntegerPintFieldSaveModel.objects.filter(weight__gt=extra_small)
<QuerySet [<IntegerPintFieldSaveModel: small>, <IntegerPintFieldSaveModel: large>]>

IntegerPintFieldSaveModel.objects.filter(weight__gte=small)
<QuerySet [<IntegerPintFieldSaveModel: small>, <IntegerPintFieldSaveModel: large>]>

IntegerPintFieldSaveModel.objects.filter(weight__range=(small, medium))
<QuerySet [<IntegerPintFieldSaveModel: small>]>
```

## Valid Lookups

Other lookups will be added in the future. Currently available are:

- exact
- iexact
- gt
- gte
- lt
- lte
- range
- isnull

## Creating your own units

*Will be detailed soon*


## Model Fields

- **IntegerPintField**: Stores a pint measurement as an integer (-2147483648 to 2147483647).
- **BigIntegerPintField**: Stores a pint measurement as a big integer (-9223372036854775808 to 9223372036854775807).
- **DecimalPintField**: Stores a pint measurement as a decimal.

## Form Fields

- **IntegerPintFormField**: Used in forms with IntegerPintField and BigIntegerPintField.
- **DecimalPintFormField**: Used in forms with DecimalPintField.

## Widgets

- **PintFieldWidget**: Default widget for all django pint field types.


## Settings

<dl>
  <dt><code>DJANGO_PINT_FIELD_DECIMAL_PRECISION</code></dt>
  <dd>
    Determines whether django_pint_field should automatically set the python decimal precision for the project. If an integer greater than 0 is provided, the decimal context precision for the entire project will be set to that value. Otherwise, the precision remains at the default (usually 28).<br>
    <em>* Type: int</em>
    <em>* Default: 0</em>
  </dd>
</dl>


## Rounding modes (upcoming feature)

**decimal.ROUND_CEILING**
Round towards Infinity.

**decimal.ROUND_DOWN**
Round towards zero.

**decimal.ROUND_FLOOR**
Round towards -Infinity.

**decimal.ROUND_HALF_DOWN**
Round to nearest with ties going towards zero.

**decimal.ROUND_HALF_EVEN**
Round to nearest with ties going to nearest even integer.

**decimal.ROUND_HALF_UP**
Round to nearest with ties going away from zero.

**decimal.ROUND_UP**
Round away from zero.

**decimal.ROUND_05UP**
Round away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise round towards zero.

Read more about rounding modes for decimals at the [decimal docs](https://docs.python.org/3/library/decimal.html#rounding-modes)



## Use the test app with docker compose

### Build and bring up

```
docker compose build
docker compose run django python manage.py migrate
docker compose run django python manage.py createsuperuser
docker compose up -d
```

Navigate to `127.0.0.1:8000`

### Test (assuming you have already performed `build`)

`docker compose run django python manage.py test`

## Run psql on the Postgres database

`docker compose exec postgres psql -U postgres`


## ToDos:
- If a unit_choices value is an alias (e.g. pounds vs pound), the form widget will show the incorrect item selected. The correct value is saved in db, though.
- Implement rounding modes
- 