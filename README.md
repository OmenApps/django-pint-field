# django-pint-field
Use pint with Django's ORM

Modified from [django-pint](https://github.com/CarliJoy/django-pint) with different goals.

Unlike django-pint, in this project we use a composite field to store both the magnitude and value of the field.


## Run psql on the Postgres database

```
docker compose exec postgres psql -U postgres
```
