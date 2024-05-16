from pathlib import Path

from pint import UnitRegistry

PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_DATABASE = "postgres"
PG_HOST = "postgres"
PG_PORT = "5432"

import tests.demoapp

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
DEBUG = True
STATIC_URL = "/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": PG_USER,
        "NAME": PG_DATABASE,
        "HOST": PG_HOST,
        "PORT": PG_PORT,
        "PASSWORD": PG_PASSWORD,
        "TEST": {
            "NAME": "mytestdatabase",
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://rediscelery:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "MAX_ENTRIES": 5000,
            "CULL_FREQUENCY": 10,  # The fraction of entries (1 / CULL_FREQUENCY) culled when MAX_ENTRIES is reached
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "VERSION": 1,
        "TIMEOUT": 60 * 60,  # The default timeout, in seconds, to use for the cache.
    }
}

# Which tables to cache using django-cachalot
CACHALOT_ONLY_CACHABLE_TABLES = frozenset(
    (
        "demoapp_integerpintfieldcachedmodel",
        "demoapp_bigintegerpintfieldcachedmodel",
        "demoapp_decimalpintfieldcachedmodel",
    )
)


# not very secret in tests
SECRET_KEY = "5tb#evac8q447#b7u8w5#yj$yq3%by!a-5t7$4@vrj$al1-u3c"
USE_I18N = True
USE_L10N = True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_pint_field",
    "django_extensions",
    "rest_framework",
    "tests.demoapp",
    "cachalot",
]

ROOT_URLCONF = "tests.demoapp.urls"

custom_ureg = UnitRegistry()
custom_ureg.define("custom = [custom]")
custom_ureg.define("kilocustom = 1000 * custom")

DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg

WSGI_APPLICATION = "tests.demoapp.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
        }
    },
}
