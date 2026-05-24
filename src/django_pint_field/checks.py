"""Django system checks for django_pint_field.

These run on ``manage.py check`` (and at server start) to surface the two most
common misconfigurations: a non-PostgreSQL backend and a missing composite type.
"""

from __future__ import annotations

from django.core.checks import Error
from django.core.checks import Warning as CheckWarning
from django.db import connections


def check_database_backend(app_configs, **kwargs):
    """Error if no configured database uses a PostgreSQL backend.

    django_pint_field stores quantities in a PostgreSQL composite type and
    cannot work on other backends. Multi-database projects are valid as long as
    at least one configured database is PostgreSQL, so the error fires only when
    none are (e.g. a SQLite-only project).

    Args:
        app_configs: The app configs passed by Django's check framework (unused).
        **kwargs: Additional keyword arguments from the check framework.

    Returns:
        A list containing a single ``Error`` when no configured database uses a
        PostgreSQL backend, otherwise an empty list.
    """
    errors = []
    if not any(connections[alias].vendor == "postgresql" for alias in connections):
        errors.append(
            Error(
                "django_pint_field requires a PostgreSQL database, but none of the "
                "configured databases use a PostgreSQL backend.",
                hint="Set a database ENGINE to a PostgreSQL backend (e.g. 'django.db.backends.postgresql').",
                id="django_pint_field.E001",
            )
        )
    return errors


def pint_composite_type_exists(connection) -> bool:
    """Return True if the ``pint_field`` composite type is visible in PostgreSQL.

    Uses ``to_regtype`` so the result respects the connection's ``search_path``
    (the type must be resolvable by name, not merely present in some schema).

    Args:
        connection: A database connection wrapper.

    Returns:
        True if ``pint_field`` resolves in the current search path, else False.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regtype(%s)", ["pint_field"])
        return cursor.fetchone()[0] is not None


def check_composite_type_registered(app_configs, databases=None, **kwargs):
    """Warn if the ``pint_field`` composite type is missing from PostgreSQL.

    Only runs when database access is requested (``manage.py check --database``
    or the deploy checks), so plain ``manage.py check`` stays offline-safe.

    Args:
        app_configs: The app configs passed by Django's check framework (unused).
        databases: Database aliases the check is allowed to query, or None.
        **kwargs: Additional keyword arguments from the check framework.

    Returns:
        A list of ``Warning`` objects for each PostgreSQL database missing the
        composite type, otherwise an empty list.
    """
    warnings = []
    if not databases:
        return warnings

    for alias in databases:
        connection = connections[alias]
        if connection.vendor != "postgresql":
            continue
        try:
            exists = pint_composite_type_exists(connection)
        except Exception:  # pylint: disable=broad-except
            # If we cannot introspect, stay silent rather than emit a false alarm.
            continue
        if not exists:
            warnings.append(
                CheckWarning(
                    f"The 'pint_field' composite type is missing from database {alias!r}.",
                    hint="Run `python manage.py migrate django_pint_field` (or "
                    "`python manage.py setup_pint_field`) before migrating models "
                    "that use PintFields.",
                    id="django_pint_field.W001",
                )
            )
    return warnings
