# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [MIT license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

[mit license]: https://opensource.org/licenses/MIT
[source code]: https://github.com/jacklinke/django-pint-field
[documentation]: https://django-pint-field.readthedocs.io/
[issue tracker]: https://github.com/OmenApps/django-pint-field/issues

## How to report a bug

Report bugs on the [Issue Tracker].

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

## How to request a feature

Request features on the [Issue Tracker].

## How to set up your development environment

You need Python 3.11+ and the following tools:

- [uv] - Fast Python package installer and resolver
- [Docker] and [Docker Compose] - For running PostgreSQL and the development environment
- [Nox] - For running test sessions

**Note:** This package requires PostgreSQL due to its use of composite types. We use Docker Compose to provide the complete development environment.

### Initial Setup

1. Clone the repository:
```console
$ git clone https://github.com/jacklinke/django-pint-field.git
$ cd django-pint-field
```

2. Start the Docker Compose services:
```console
$ docker compose up -d
```

This will start:
- Django application (port 8115)
- PostgreSQL database (port 5437)
- Redis cache (port 6390)

3. The development environment is now ready. Code changes in `src/` and `example_project/` are immediately reflected.

### Running Commands

Run commands inside the Django container:

```console
# Python shell
$ docker compose exec django uv run python manage.py shell_plus

# Django management commands
$ docker compose exec django uv run python manage.py migrate
$ docker compose exec django uv run python manage.py createsuperuser

# Run tests
$ docker compose exec django uv run pytest -v

# Access the application
# Visit http://localhost:8115 in your browser
```

For local development without Docker (requires PostgreSQL installed):

```console
$ uv sync
$ uv run pytest
```

[uv]: https://github.com/astral-sh/uv
[docker]: https://docs.docker.com/get-docker/
[docker compose]: https://docs.docker.com/compose/
[nox]: https://nox.thea.codes/

## How to test the project

**Important:** Tests must be run inside the Docker container where PostgreSQL is available.

Run the full test suite:

```console
$ docker compose exec django uv run pytest -vv
```

Run tests with coverage:

```console
$ docker compose exec django uv run coverage run -m pytest -vv
$ docker compose exec django uv run coverage report
```

Run nox test sessions (tests multiple Python/Django versions):

```console
$ docker compose exec django nox --session=tests
```

List the available Nox sessions:

```console
$ docker compose exec django nox --list-sessions
```

You can also run a specific Nox session:

```console
$ docker compose exec django nox --session=tests-3.13 -- -p django-5.2
```

Unit tests are located in the `example_project/` directory,
and are written using the [pytest] testing framework.

[pytest]: https://pytest.readthedocs.io/

## How to submit changes

Open a [pull request] to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- All tests must pass without errors and warnings.
- Include unit tests. This project maintains 80%+ code coverage.
- If your changes add functionality, update the documentation accordingly.
- Run the pre-commit hooks (linting, formatting) before submitting.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
$ nox --session=pre-commit -- install
```

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.

[pull request]: https://github.com/jacklinke/django-pint-field/pulls

<!-- github-only -->

[code of conduct]: CODE_OF_CONDUCT.md
