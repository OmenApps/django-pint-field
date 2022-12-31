# django-pint-field

Use pint with Django's ORM

Modified from the fantastic [django-pint](https://github.com/CarliJoy/django-pint) with different goals.

Unlike django-pint, in this project we use a composite field to store both the magnitude and value of the field. For this reason, the project only works with Postgresql databases.


```python

```


## Run psql on the Postgres database

```
docker compose exec postgres psql -U postgres
```


## Rounding modes

decimal.ROUND_CEILING
Round towards Infinity.

decimal.ROUND_DOWN
Round towards zero.

decimal.ROUND_FLOOR
Round towards -Infinity.

decimal.ROUND_HALF_DOWN
Round to nearest with ties going towards zero.

decimal.ROUND_HALF_EVEN
Round to nearest with ties going to nearest even integer.

decimal.ROUND_HALF_UP
Round to nearest with ties going away from zero.

decimal.ROUND_UP
Round away from zero.

decimal.ROUND_05UP¶
Round away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise round towards zero.



Read more about rounding modes for decimals at the [decimal docs](https://docs.python.org/3/library/decimal.html#rounding-modes)
