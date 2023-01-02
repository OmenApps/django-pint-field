FROM python:3.10-slim

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev \
  # needed for psql
  postgresql postgresql-contrib postgresql-client \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install psycopg2-binary ipdb poetry

WORKDIR ${APP_HOME}
COPY poetry.lock pyproject.toml ${APP_HOME}
COPY ./django_pint_field/* ${APP_HOME}

# Project initialization:
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# copy application files
COPY ./manage.py ${APP_HOME}
COPY ./tests/* ${APP_HOME}
COPY ./compose/* ${APP_HOME}

COPY ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

ENTRYPOINT ["/entrypoint"]
