# django-pint-field

Use pint with Django's ORM

Modified from the fantastic [django-pint](https://github.com/CarliJoy/django-pint) with different goals.

Unlike django-pint, in this project we use a composite field to store both the magnitude and value of the field, along with the equivalent value in base units for comparisons. For this reason, the project only works with Postgresql databases.


## Model Fields

- **IntegerPintField**: Stores a pint measurement as an integer (-2147483648 to 2147483647).
- **BigIntegerPintField**: Stores a pint measurement as a big integer (-9223372036854775808 to 9223372036854775807).
- **DecimalPintField**: Stores a pint measurement as a decimal.

## Form Fields

- **IntegerPintFormField**: Used in forms with IntegerPintField and BigIntegerPintField.
- **DecimalPintFormField**: Used in forms with DecimalPintField.


## Settings

*Note, postgres' "precision" is equivalent to django's "max_digits", and "scale" is equivalent to "decimal_places"*

### Comparator column settings

These set the maximum precision and scale for the decimals used in the comparator column of each pint field.

The comparitor column holds the equivalent value of your field's magnitude, converted to base units. You must consider what the potential maximum precision and scale might be, based on your use-cases.

For instance, if you allow users to input time in picoseconds, the base unit of time is seconds. A value of 1 picosecond is stored in the comparator column as 0.000000000001 seconds, and to get valid comparisons of values, your project would require a scale value of at least 12 and a precision value of at least 13.

You must also consider the precision of python decimals (which defaults to 28 places). To set higher precision, see the section on [Mitigating round-off error with increased precision](https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision) in the decimal docs, or use the `DJANGO_PINT_FIELD_SET_PROJECT_PRECISION` setting below.

<dl style="margin-left: 40px;">
  <dt><code>DJANGO_PINT_FIELD_COMPARATOR_PRECISION</code></dt>
  <dd>
    Specifies the maximum precision used in the comparator field column.<br>
    <em>* Type: int</em>
    <em>* Default: 28</em>
  </dd>

  <dt><code>DJANGO_PINT_FIELD_COMPARATOR_SCALE</code></dt>
  <dd>
    Specifies the maximum scale used in the comparator field column.<br>
    <em>* Type: int</em>
    <em>* Default: 16</em>
  </dd>
</dl>

### DecimalPintField settings

These set the maximum precision and scale for the decimals used in any decimal pint field.

Note that the precision and scale set here MUST be at least as long as the `max_digits` and `decimal_places` for any DecimalPintField you create in your project!

<dl>
  <dt><code>DJANGO_PINT_FIELD_DECIMAL_FIELD_PRECISION</code></dt>
  <dd>
    Specifies the maximum precision used in the comparator field column.<br>
    <em>* Type: int</em>
    <em>* Default: 16</em>
  </dd>

  <dt><code>DJANGO_PINT_FIELD_DECIMAL_FIELD_SCALE</code></dt>
  <dd>
    Specifies the maximum scale used in the comparator field column.<br>
    <em>* Type: int</em>
    <em>* Default: 4</em>
  </dd>
</dl>

### Other settings

<dl>
  <dt><code>DJANGO_PINT_FIELD_SET_PROJECT_PRECISION</code></dt>
  <dd>
    Determines whether django_pint_field should automatically set the precision of the project. If True, the decimal context will be set to the greater of: <code>DJANGO_PINT_FIELD_COMPARATOR_PRECISION</code>, <code>DJANGO_PINT_FIELD_DECIMAL_FIELD_PRECISION</code>, or <code>28</code>.<br>
    <em>* Type: bool</em>
    <em>* Default: False</em>
  </dd>



## Rounding modes

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


## Run psql on the Postgres database

```
docker compose exec postgres psql -U postgres
```



## ToDos:
- Lots