FROM python:3.8-slim

# install system dependencies

RUN apt-get update

RUN apt-get install -y build-essential libpq-dev curl gettext git postgresql-client

RUN pip3 install --upgrade wheel setuptools pip

RUN pip3 install pre-commit psycopg2-binary ipdb

WORKDIR /django-pint-field

# copy application files
COPY . /django-pint-field

# RUN pre-commit install

RUN pip install -e /django-pint-field
