"""Django settings for core project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from decimal import Decimal
from pathlib import Path

from pint import UnitRegistry


# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = "django-insecure-r88%=*g)x(&-&67duelz$=8mat90+aq^wo+6niu!rd2v4(#f#t"  # nosec

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True

ALLOWED_HOSTS = ["*"]  # nosec

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "rest_framework",
    "ninja",
    "cachalot",
    "cacheops",
    "example_project.example",
    "example_project.laboratory",
    "django_pint_field",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "example_project.urls"

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

WSGI_APPLICATION = "example_project.wsgi.application"
ASGI_APPLICATION = "example_project.asgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_DATABASE = "postgres"
PG_HOST = "postgres"
PG_PORT = "5432"

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
        "LOCATION": "redis://redis:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "MAX_ENTRIES": 5000,
            "CULL_FREQUENCY": 10,  # The fraction of entries (1 / CULL_FREQUENCY) culled when MAX_ENTRIES is reached
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "PARSER_CLASS": "redis.connection._HiredisParser",
        },
        "VERSION": 1,
        "TIMEOUT": 60 * 60,  # The default timeout, in seconds, to use for the cache.
    }
}

# Which tables to cache using django-cachalot
CACHALOT_ONLY_CACHABLE_TABLES = frozenset(
    (
        "example_integerpintfieldcachalotmodel",
        "example_bigintegerpintfieldcachalotmodel",
        "example_decimalpintfieldcachalotmodel",
    )
)

# Which tables to cache using cacheops
CACHEOPS_REDIS = "redis://redis:6379/1"

CACHEOPS = {
    "example.integer_pint_field_cachops_model": {"ops": "all", "timeout": 60 * 15},
    "example.big_integer_pint_field_cacheops_model": {"ops": "all", "timeout": 60 * 15},
    "example.decimal_pint_field_cacheops_model": {"ops": "all", "timeout": 60 * 15},
    "*.*": {"timeout": 60 * 15},
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# django-pint-field settings
# https://django-pint-field.readthedocs.io/en/latest/
DJANGO_PINT_FIELD_DEFAULT_FORMAT = "P"

DJANGO_PINT_FIELD_UNIT_REGISTER = UnitRegistry(non_int_type=Decimal)
DJANGO_PINT_FIELD_UNIT_REGISTER.define("custom = [custom]")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("kilocustom = 1000 * custom")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("gram_per_milliliter = gram / milliliter = _ = g_per_ml")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("kilogram_per_cubic_meter = kilogram / meter**3 = _ = kg_per_cubic_m")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("gram_per_cubic_centimeter = gram / centimeter**3 = _ = g_per_cubic_cm")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("mole_per_liter_second = mole/(liter*second) = _ = mol_per_l_s")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("millimole_per_liter_second = millimole/(liter*second) = _ = mmol_per_l_s")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("square_meter = m**2 = square_m")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("square_centimeter = cm**2 = square_cm")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("square_millimeter = mm**2 = square_mm")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("cubic_meter = m**3 = cubic_m")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("cubic_centimeter = cm**3 = cubic_cm")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("cubic_millimeter = mm**3 = cubic_mm")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("acre_inch = acre_foot / 12 = ac_in = acre_inch = acre_in")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("pascal_second = pascal * second = Pa_s")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("roentgen_per_hour = roentgen / hour = R_per_h")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("milliroentgen_per_hour = milliroentgen / hour = mR_per_h")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("microroentgen_per_hour = microroentgen / hour = uR_per_h")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("kilowatt_hour = kilowatt * hour = kWh")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("millielectronvolt = eV / 1000 = meV")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("microelectronvolt = eV / 1000000 = ueV")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("teraelectronvolt = eV * 1000000000000 = TeV")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("gigaelectronvolt = eV * 1000000000 = GeV")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("megaelectronvolt = eV * 1000000 = MeV")

# Base unit of instruction
DJANGO_PINT_FIELD_UNIT_REGISTER.define("instruction = []")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("instructions_per_second = instruction / second = IPS")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("million_instructions_per_second = 1000000 * IPS = MIPS")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("giga_instructions_per_second = 1000000000 * IPS = GIPS")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("tera_instructions_per_second = 1000000000000 * IPS = TIPS")


DJANGO_PINT_FIELD_UNIT_REGISTER.define("inverse_meter_squared = 1 / meter**2")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("inverse_kilometer_squared = 1 / kilometer**2")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("megavolt_per_meter = megavolt / meter = MV_per_m")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("kilovolt_per_meter = kilovolt / meter = kV_per_m")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("volt_per_meter = volt / meter = V_per_m")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("microsievert_per_hour = microsievert / hour = uSv_per_h")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("millisievert_per_hour = millisievert / hour = mSv_per_h")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("sievert_per_hour = sievert / hour = Sv_per_h")

DJANGO_PINT_FIELD_UNIT_REGISTER.define("joule_per_cubic_meter = joule / meter**3 = J_per_m3")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("kilojoule_per_cubic_meter = kilojoule / meter**3 = kJ_per_m3")
DJANGO_PINT_FIELD_UNIT_REGISTER.define(
    "megajoule_per_cubic_meter = megajoule / meter**3 = MJ_per_m3 = megajoule_per_m3"
)

DJANGO_PINT_FIELD_UNIT_REGISTER.define("cubic_feet_per_second = cubic_foot / second = cfs = cubic_feet_per_sec")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("cubic_yards_per_second = cubic_yard / second = _ = cubic_yards_per_sec")
DJANGO_PINT_FIELD_UNIT_REGISTER.define("acre_inches_per_hour = acre_inch / hour = _ = acre_in_per_hour")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django_pint_field": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "example_project": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}
