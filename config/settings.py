import os
import sys
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
if (BASE_DIR / ".env").exists():
    env.read_env(BASE_DIR / ".env")


def get_setting(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


def get_bool(name, default=False):
    value = get_setting(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list(*names, default=""):
    value = get_setting(*names, default=default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = get_bool("DEBUG", get_bool("DJANGO_DEBUG", False))
SECRET_KEY = get_setting(
    "SECRET_KEY",
    "DJANGO_SECRET_KEY",
    default="unsafe-development-key",
)

if not DEBUG and SECRET_KEY == "unsafe-development-key":
    raise ImproperlyConfigured("Set SECRET_KEY when DEBUG is false.")

ALLOWED_HOSTS = get_list(
    "ALLOWED_HOSTS",
    "DJANGO_ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "accounts",
    "common",
    "audit_logs",
    "languages",
    "go_bag",
    "guidelines",
    "evacuation_centers",
    "emergency_contacts",
    "alerts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

if get_bool("USE_SQLITE", False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": get_setting("SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    database_options = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }
    database_ssl_ca = get_setting("DB_SSL_CA")
    if database_ssl_ca:
        database_options["ssl"] = {"ca": database_ssl_ca}

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": get_setting("DB_NAME", "MYSQL_DATABASE", default="hazard_hero"),
            "USER": get_setting("DB_USER", "MYSQL_USER", default="root"),
            "PASSWORD": get_setting("DB_PASSWORD", "MYSQL_PASSWORD", default=""),
            "HOST": get_setting("DB_HOST", "MYSQL_HOST", default="127.0.0.1"),
            "PORT": get_setting("DB_PORT", "MYSQL_PORT", default="3306"),
            "CONN_MAX_AGE": int(get_setting("DB_CONN_MAX_AGE", default="60")),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": database_options,
        }
    }

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = get_setting("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = Path(get_setting("MEDIA_ROOT", default=str(BASE_DIR / "media")))
MEDIA_URL = get_setting("MEDIA_URL", default="/media/")
SERVE_MEDIA = get_bool("SERVE_MEDIA", DEBUG)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "common.permissions.IsAdministratorResponder"
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": int(get_setting("PAGE_SIZE", default="20")),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["common.renderers.EnvelopeJSONRenderer"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(get_setting("ACCESS_TOKEN_LIFETIME_MINUTES", default="30"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(get_setting("REFRESH_TOKEN_LIFETIME_DAYS", default="7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Hazard Hero API",
    "DESCRIPTION": (
        "Public Citizen and JWT-protected Administrator/Responder APIs"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "GoBagCategoryEnum": "go_bag.models.GoBagItem.CATEGORIES",
        "GuidelineCategoryEnum": "guidelines.models.Guideline.CATEGORIES",
        "TranslationStatusEnum": "languages.models.TRANSLATION_STATUSES",
        "SupportedLanguageCodeEnum": "languages.models.LANGUAGE_CHOICES",
    },
}

CORS_ALLOWED_ORIGINS = get_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS = get_list("CSRF_TRUSTED_ORIGINS")

MAX_UPLOAD_SIZE = int(get_setting("MAX_UPLOAD_SIZE", default=str(10 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

FRONTEND_RESET_URL = get_setting(
    "FRONTEND_RESET_URL",
    default="hazardhero://reset-password",
)
EMAIL_BACKEND = get_setting(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = get_setting("EMAIL_HOST", default="")
EMAIL_PORT = int(get_setting("EMAIL_PORT", default="587"))
EMAIL_HOST_USER = get_setting("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = get_setting("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = get_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = get_setting(
    "DEFAULT_FROM_EMAIL",
    default="noreply@hazardhero.local",
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = get_bool("SECURE_SSL_REDIRECT", False)
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
SESSION_COOKIE_SECURE = get_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = get_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(
    get_setting("SECURE_HSTS_SECONDS", default="31536000" if not DEBUG else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    not DEBUG,
)
SECURE_HSTS_PRELOAD = get_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": get_setting("LOG_LEVEL", default="INFO"),
    },
}
