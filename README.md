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

In [1]: IntegerPintFieldSaveModel.objects.first()
Out[1]: <IntegerPintFieldSaveModel: small>

In [2]: IntegerPintFieldSaveModel.objects.first().weight
Out[2]: 10 <Unit('gram')>

In [3]: IntegerPintFieldSaveModel.objects.first().weight.magnitude
Out[3]: 10

In [4]: IntegerPintFieldSaveModel.objects.first().weight.units
Out[4]: <Unit('gram')>

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


## Aggregates

A number of aggregates have been implemented for the Django Pint Fields. Functionally they should perform for Pint Fields the same way django's default aggregates work for other field types, and each is prepended with "Pint". The aggregates include:

- PintAvg
- PintCount
- PintMax
- PintMin
- PintStdDev
- PintSum
- PintVariance

### Example usage:

```python
from django_pint_field.aggregates import PintAvg, PintCount, PintMax, PintMin, PintStdDev, PintSum, PintVariance
IntegerPintFieldSaveModel.objects.aggregate(PintAvg('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintCount('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintMax('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintMin('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintStdDev('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintSum('weight'))
IntegerPintFieldSaveModel.objects.aggregate(PintVariance('weight'))
```


## Creating your own units

You can [create your own pint units](https://pint.readthedocs.io/en/stable/advanced/defining.html) if the [default units](https://github.com/hgrecco/pint/blob/master/pint/default_en.txt) in pint are not sufficient.

Anywhere within your project (ideally in settings or a file adjacent to settings), define the custom unit registry by importing Pint's default UnitRegistry and extending it:

```python
from pint import UnitRegistry

custom_ureg = UnitRegistry()
custom_ureg.define("custom = [custom]")
custom_ureg.define("kilocustom = 1000 * custom")
```

Then add the custom registry to settings:

`DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg`


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

  <dt><code>DJANGO_PINT_FIELD_UNIT_REGISTER</code></dt>
  <dd>
    The Unit Registry to use in the project. Defaults to pint.UnitRegistry.<br>
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