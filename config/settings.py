import os
import sys
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
try:
    import environ
    env = environ.Env(DEBUG=(bool, False))
    if (BASE_DIR / ".env").exists(): env.read_env(BASE_DIR / ".env")
    get = lambda key, default=None: env(key, default=default)
except ImportError:  # permits initial setup before requirements are installed
    get = lambda key, default=None: os.getenv(key, default)

SECRET_KEY = get("SECRET_KEY", get("DJANGO_SECRET_KEY", "unsafe-development-key"))
DEBUG = str(get("DEBUG", get("DJANGO_DEBUG", "true"))).lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in get("ALLOWED_HOSTS", get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,10.0.2.2")).split(",") if x.strip()]

INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "rest_framework", "rest_framework_simplejwt.token_blacklist", "django_filters", "corsheaders", "drf_spectacular", "accounts", "common", "audit_logs", "languages", "go_bag", "guidelines", "evacuation_centers", "emergency_contacts", "alerts"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"

if str(get("USE_SQLITE", "false")).lower() == "true":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", "NAME": get("DB_NAME", get("MYSQL_DATABASE", "hazard_hero")), "USER": get("DB_USER", get("MYSQL_USER", "root")), "PASSWORD": get("DB_PASSWORD", get("MYSQL_PASSWORD", "")), "HOST": get("DB_HOST", get("MYSQL_HOST", "127.0.0.1")), "PORT": get("DB_PORT", get("MYSQL_PORT", "3306")), "CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True, "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}}, {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}]
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "en-us", "UTC", True, True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = get("MEDIA_ROOT", str(BASE_DIR / "media")); MEDIA_URL = get("MEDIA_URL", "/media/")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"], "DEFAULT_PERMISSION_CLASSES": ["common.permissions.IsAdministratorResponder"], "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend", "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"], "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination", "PAGE_SIZE": int(get("PAGE_SIZE", 20)), "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema", "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler", "DEFAULT_RENDERER_CLASSES": ["common.renderers.EnvelopeJSONRenderer"]}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(get("ACCESS_TOKEN_LIFETIME_MINUTES", 30))), "REFRESH_TOKEN_LIFETIME": timedelta(days=int(get("REFRESH_TOKEN_LIFETIME_DAYS", 7))), "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True, "UPDATE_LAST_LOGIN": True}
SPECTACULAR_SETTINGS = {"TITLE": "Hazard Hero API", "DESCRIPTION": "Public Citizen and JWT-protected Administrator/Responder APIs", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False, "ENUM_NAME_OVERRIDES": {"GoBagCategoryEnum": "go_bag.models.GoBagItem.CATEGORIES", "GuidelineCategoryEnum": "guidelines.models.Guideline.CATEGORIES", "TranslationStatusEnum": "languages.models.TRANSLATION_STATUSES", "SupportedLanguageCodeEnum": "languages.models.LANGUAGE_CHOICES"}}
CORS_ALLOWED_ORIGINS = [x.strip() for x in get("CORS_ALLOWED_ORIGINS", "").split(",") if x.strip()]
CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
FILE_UPLOAD_MAX_MEMORY_SIZE = int(get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
FRONTEND_RESET_URL = get("FRONTEND_RESET_URL", "hazardhero://reset-password")
EMAIL_BACKEND = get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = get("DEFAULT_FROM_EMAIL", "noreply@hazardhero.local")
