from pathlib import Path
from pint import UnitRegistry

# Allow user specific postgres credentials to be provided
# in a local.py file
try:
    from .env import PG_PASSWORD, PG_USER
except ImportError:
    # Define the defaults Travis CI/CD if any parameter was unset
    PG_USER = "postgres"
    PG_PASSWORD = "postgres"

try:
    from .env import PG_DATABASE
except ImportError:
    PG_DATABASE = "postgres"

try:
    from .env import PG_HOST
except ImportError:
    PG_HOST = "postgres"

try:
    from .env import PG_PORT
except ImportError:
    PG_PORT = "5432"

import tests.dummyapp

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
    "tests.dummyapp",
]
ROOT_URLCONF = "tests.dummyapp.urls"

custom_ureg = UnitRegistry()
custom_ureg.define("custom = [custom]")
custom_ureg.define("kilocustom = 1000 * custom")

DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg

WSGI_APPLICATION = "tests.dummyapp.wsgi.application"

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
