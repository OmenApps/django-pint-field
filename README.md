
# django-pint-field

Use [pint](https://pint.readthedocs.io/en/stable/) with Django's ORM.

If you want to store quantities (1 gram, 3 miles, 8.120391 angstroms, etc) in a model, edit them in forms, and have the ability to convert to other quantities in your django projects, this is the package for you!

This package is modified from the fantastic [django-pint](https://github.com/CarliJoy/django-pint) with different goals. Unlike django-pint, in this project we use a composite Postgres field to store both the magnitude and the user's desired units, along with the equivalent value in base units. This third piece of data - the base units - makes it possible to conduct lookups comparing one instance that might be specified in "grams" with another that may be specified in "pounds", but display each instance in the units that the user desires. The units your users want to use are the units they see, while still allowing accurate comparisons of one quantity to another.

For this reason, the project only works with Postgresql databases.


## Install

`pip install django_pint_field`

Add `"django_pint_field",` to your list of installed apps.

Run `python manage.py migrate django_pint_field`

```{caution}
Failure to run this migration will result in errors for any model making use of django-pint-field when its migrations are run.
```


## Usage

Assuming we are starting with the following model:

```python
from django.db import models

from django_pint_field.models import IntegerPintField


class IntegerPintFieldSaveModel(models.Model):
    name = models.CharField(max_length=20)
    weight = IntegerPintField("gram")

    def __str__(self):
        return str(self.name)
```

We can do the following:

```python
from django_pint_field.units import ureg

from .models import IntegerPintFieldSaveModel

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
- gt
- gte
- lt
- lte
- range
- isnull

```python
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


## Aggregates

A number of aggregates have been implemented for the Django Pint Fields. Functionally they perform for Pint Fields the same way django's default aggregates work for other field types, and each is prepended with "Pint". The aggregates include:

- PintAvg
- PintCount
- PintMax
- PintMin
- PintStdDev
- PintSum
- PintVariance

```python
from django_pint_field.aggregates import PintAvg, PintCount, PintMax, PintMin, PintStdDev, PintSum, PintVariance

# Perform some queries
IntegerPintFieldSaveModel.objects.aggregate(PintAvg('weight'))
{'weight__pintavg': Decimal('0.50500000000000000000') <Unit('kilogram')>}

IntegerPintFieldSaveModel.objects.aggregate(PintCount('weight'))
{'weight__pintcount': 2}

IntegerPintFieldSaveModel.objects.aggregate(PintMax('weight'))
{'weight__pintmax': Decimal('1.0') <Unit('kilogram')>}

IntegerPintFieldSaveModel.objects.aggregate(PintMin('weight'))
{'weight__pintmin': Decimal('0.01') <Unit('kilogram')>}

IntegerPintFieldSaveModel.objects.aggregate(PintStdDev('weight'))
{'weight__pintstddev': Decimal('0.49500000000000000000') <Unit('kilogram')>}

IntegerPintFieldSaveModel.objects.aggregate(PintSum('weight'))
{'weight__pintsum': Decimal('1.01') <Unit('kilogram')>}

IntegerPintFieldSaveModel.objects.aggregate(PintVariance('weight'))
{'weight__pintvariance': Decimal('0.24502500000000000000') <Unit('kilogram')>}
```


## Use with Django Rest Framework


```python
from django_pint_field.rest import IntegerPintRestField

class DjangoPintFieldSerializer(serializers.ModelSerializer):
    # Let DRF know which type of serializer field to use
    weight = IntegerPintRestField()

    class Meta:
        model = IntegerPintFieldSaveModel
        fields = ["name", "weight"]
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

Then add the custom registry to your app's settings.py:

`DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg`


## Model Fields

- **IntegerPintField**: Stores a pint measurement as an integer (-2147483648 to 2147483647).
- **BigIntegerPintField**: Stores a pint measurement as a big integer (-9223372036854775808 to 9223372036854775807).
- **DecimalPintField**: Stores a pint measurement as a decimal. Like Django's DecimalField, DecimalPintField takes required `max_digits` and `decimal_places` parameters.


## Form Fields

- **IntegerPintFormField**: Used in forms with IntegerPintField and BigIntegerPintField.
- **DecimalPintFormField**: Used in forms with DecimalPintField.


## Widgets

- **PintFieldWidget**: Default widget for all django pint field types.
- **TabledPintFieldWidget**: Provides a table showing conversion to each of the `unit_choices`.

![TabledPintFieldWidget](https://raw.githubusercontent.com/jacklinke/django-pint-field/main/media/TabledPintFieldWidget.png)


Example usage:

```python
class WeightModel(models.Model):
    decimal_weight = DecimalPintField(
        "gram",
        blank=True,
        null=True,
        max_digits=10,
        decimal_places=2,
        unit_choices=[
            "kilogram",
            "milligram",
            "pounds"
        ],
    )

class TabledWeightForm(forms.ModelForm):
    class Meta:
        model = WeightModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If we want to use the tabled widget, we need to pass the 
        #   default_unit and unit_choices to the new widget
        default_unit = self.fields["decimal_weight"].default_unit
        unit_choices = self.fields["decimal_weight"].unit_choices
        self.fields["decimal_weight"].widget = TabledPintFieldWidget(
            default_unit=default_unit, unit_choices=unit_choices
        )
```

The template for this widget is located at https://github.com/jacklinke/django-pint-field/blob/main/django_pint_field/templates/tabled_django_pint_field_widget.html

If you want to override the template, add your own template in your project at: "templates/django_pint_field/tabled_django_pint_field_widget.html"

## DRF Serializer Fields

- **IntegerPintRestField**: Used in DRF with IntegerPintField and BigIntegerPintField.
- **DecimalPintRestField**: Used in DRF with DecimalPintField.


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


## More Details on the Composite Field

The composite field stores three pieces of data:

1. **comparator**: The magnitude of the quantity in base units, always stored as numeric type (aka: decimal)
2. **magnitude**: The magnitude of the quantity in the units specified by the user, with type determined by the model field type
3. **units**: The units of the quantity specified by the user, stored as a string

The first piece of data is mainly for internal use, and makes it possible to conduct lookups and comparisons between quantities that are 
specified in different units. For instance, we can perform aggregations for one model instance specified in nautical miles and another 
specified in light years, or compare which instance has the greater length. This is performed directly in the database, because the two 
instances share the same base units (meter). 

The second and third pieces of data are mainly user-facing, and are used for display.

Assuming we have the following model:

```python
from django.db import models

from django_pint_field.models import BigIntegerPintField


class GalaxyComparison(models.Model):
    name = models.CharField(max_length=20)
    length = BigIntegerPintField("meter")

    def __str__(self):
        return str(self.name)
```

We can do the following:

```python
from django_pint_field.aggregates import PintAvg, PintCount, PintMax, PintMin, PintStdDev, PintSum, PintVariance
from django_pint_field.units import ureg

from .models import GalaxyComparison

Quantity = ureg.Quantity

# Start by creating a few Pint Quantity objects
quantity_dict = {
    "me_to_refrigerator": Quantity(4_000_000_000 * ureg.micron),
    "seattle_to_dc": Quantity(4_421_000_000 * ureg.millimeter),
    "earth_to_moon": Quantity(384_398_905 * ureg.meter),
    "earth_to_sun": Quantity(14_712_000_000_000 * ureg.centimeter),
    "earth_to_alpha_centauri": Quantity(23_218_142_548_596 * ureg.nautical_mile),
}

# Create GalaxyComparison instance for each quantity in the dictionary
for key, value in quantity_dict.items():
    GalaxyComparison.objects.create(name=key, length=value)
    print(f"{key}: {int(value.to(ureg.meter).magnitude):_} meter")

# Output:
# me_to_refrigerator: 4_000 meter
# seattle_to_dc: 4_421_000 meter
# earth_to_moon: 384_398_905 meter
# earth_to_sun: 147_120_000_000 meter
# earth_to_alpha_centauri: 42_999_999_999_999_792 meter


# --- Following are some examples of lookups and comparisons --- #

# Annotate each instance in the queryset with length in the base unit (meters)
GalaxyComparison.objects.annotate(length_in_meters=F("length__comparator")).values("name", "length_in_meters")
<QuerySet [{'name': 'me_to_refrigerator', 'length_in_meters': Decimal('4000')}, {'name': 'seattle_to_dc', 'length_in_meters': Decimal('4421000')}, {'name': 'earth_to_moon', 'length_in_meters': Decimal('384398905')}, {'name': 'earth_to_sun', 'length_in_meters': Decimal('147120000000')}, {'name': 'earth_to_alpha_centauri', 'length_in_meters': Decimal('42999999999999792')}]>

# Filter for instances with a length greater than 1 billion meters
GalaxyComparison.objects.filter(length__gt=Quantity(1_000_000_000 * ureg.meter))
<QuerySet [<GalaxyComparison: earth_to_alpha_centauri>, <GalaxyComparison: earth_to_sun>]>

# Get the aggregate average length in the base unit (meters)
GalaxyComparison.objects.aggregate(PintAvg("length"))
{'length__pintavg': Decimal('8600029501763940.200000') <Unit('meter')>}

# Get the aggregate max length in the base unit (meters)
GalaxyComparison.objects.aggregate(PintMax("length"))
{'length__pintmax': Decimal('42999999999999792') <Unit('meter')>}

# Get the aggregate min length in the base unit (meters)
GalaxyComparison.objects.aggregate(PintMin("length"))
{'length__pintmin': Decimal('4.000000') <Unit('meter')>}
```


## Use the test app with docker compose

### Set up a virtual environment (recommended)

Make a virtual environment named `.venv`:

`python3 -m venv .venv`
    
Activate the new environment:

`source .venv/bin/activate`


### Install dependencies

*Requires [poetry](https://python-poetry.org/). If you do not yet have it installed, run `pip install poetry`.*

`poetry install --with dev`

### Build and bring up

```
docker compose build
docker compose run django python manage.py migrate
docker compose up -d
```

### Create superuser

```python
docker compose exec django python manage.py createsuperuser
```

Navigate to admin `127.0.0.1:8000/admin` and log in with the superuser credentials you just created.

### Test (assuming you have already performed `build`)

`docker compose exec django python manage.py test`
or
`docker compose exec django pytest --create-db`


## Run psql on the Postgres database

`docker compose exec postgres psql -U postgres`


## ToDos:
- Implement rounding modes
- Think through what it would take to build range types for these fields
- Add extensible widget template
