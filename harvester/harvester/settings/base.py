"""
Django settings for harvester project.

Generated by 'django-admin startproject' using Django 2.2.10.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys
import sentry_sdk
import requests
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import ignore_logger

from celery.schedules import crontab

from data_engineering.configuration import create_configuration_and_session, MODE, CONTEXT, PROJECT
from utils.packaging import get_package_info
from search_client.version import VERSION as SEARCH_CLIENT_VERSION
from search_client.opensearch.logging import OpensearchHandler, create_opensearch_handler

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Then we read some variables from the (build) environment
PACKAGE_INFO = get_package_info()
PACKAGE_INFO["versions"]["search-client"] = SEARCH_CLIENT_VERSION
GIT_COMMIT = PACKAGE_INFO.get("commit", "unknown-git-commit")
VERSION = PACKAGE_INFO.get("versions").get("harvester", "0.0.0")
environment, session = create_configuration_and_session()
credentials = session.get_credentials()
IS_AWS = environment.aws.is_aws
ENVIRONMENT = environment.service.env

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environment.secrets.django.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = MODE == "localhost"

# We're disabling the ALLOWED_HOSTS check, because containers will run in a VPC environment
# This environment is expected to be unreachable with disallowed hosts.
# It hurts to have this setting enabled on AWS, because health checks don't pass the domain check.
ALLOWED_HOSTS = ["*"]
SITE_ID = 1

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DOMAIN = environment.django.domain
PROTOCOL = environment.django.protocol


# Detect our own IP address
try:
    response = requests.get("https://api.ipify.org/?format=json")
    IP = response.json()["ip"]
except Exception:
    IP = None


# Application definition

INSTALLED_APPS = [
    'harvester',  # first to override runserver command
    'admin_confirm',  # needs to override admin templates
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'versatileimagefield',
    'mptt',
    'datagrowth',

    'core',
    'metadata',
    'search',
    'sources',

    'edurep',
    'sharekit',
    'anatomy_tool',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'harvester.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "harvester.jinja2.environment",
            "extensions": []
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'harvester.wsgi.application'

SILENCED_SYSTEM_CHECKS = [
    'rest_framework.W001'
]


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environment.postgres.database,
        'USER': environment.postgres.user,
        'PASSWORD': environment.secrets.postgres.password,
        'HOST': environment.postgres.host,
        'PORT': environment.postgres.port,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_ALLOW_ALL_ORIGINS = True

if environment.aws.is_aws:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_ROOT = ''
    MEDIA_URL = f'https://{environment.aws.harvest_content_bucket}.s3.eu-central-1.amazonaws.com/'
    AWS_STORAGE_BUCKET_NAME = environment.aws.harvest_content_bucket
    AWS_S3_REGION_NAME = 'eu-central-1'
    AWS_DEFAULT_ACL = None
else:
    DEFAULT_FILE_STORAGE = 'core.files.storage.OverwriteStorage'
    MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media', 'harvester')
    MEDIA_URL = '/media/harvester/'
    AWS_STORAGE_BUCKET_NAME = None


# Rest framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'PAGE_SIZE': 100
}


# OpenSearch (AWS ElasticSearch)

OPENSEARCH_HOST = environment.opensearch.host
OPENSEARCH_VERIFY_CERTS = environment.opensearch.verify_certs  # ignored when protocol != https
OPENSEARCH_ANALYSERS = {
    'en': 'english',
    'nl': 'dutch',
    'unk': 'standard'
}
OPENSEARCH_ENABLE_DECOMPOUND_ANALYZERS = environment.opensearch.enable_decompound_analyzers
OPENSEARCH_DECOMPOUND_WORD_LISTS = environment.opensearch.decompound_word_lists
OPENSEARCH_PASSWORD = environment.secrets.opensearch.password
OPENSEARCH_ALIAS_PREFIX = environment.opensearch.alias_prefix


# Logging
# https://docs.djangoproject.com/en/2.2/topics/logging/
# https://docs.sentry.io/

_logging_enabled = sys.argv[1:2] != ['test']
_log_level = environment.django.logging.level if _logging_enabled else 'CRITICAL'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'django_log_formatter_json.JSONFormatter',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'json': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'search_harvest': create_opensearch_handler(
            OPENSEARCH_HOST,
            f'harvest-logs-{environment.project.name}',
            OpensearchHandler.IndexNameFrequency.WEEKLY,
            environment.container.id,
            OPENSEARCH_PASSWORD
        ),
        'search_documents': create_opensearch_handler(
            OPENSEARCH_HOST,
            f'document-logs-{environment.project.name}',
            OpensearchHandler.IndexNameFrequency.YEARLY,
            environment.container.id,
            OPENSEARCH_PASSWORD
        ),
        'search_results': create_opensearch_handler(
            OPENSEARCH_HOST,
            f'harvest-results-{environment.project.name}',
            OpensearchHandler.IndexNameFrequency.YEARLY,
            environment.container.id,
            OPENSEARCH_PASSWORD
        ),
    },
    'loggers': {
        'harvester': {
            'handlers': ['search_harvest'] if environment.django.logging.is_opensearch else ['console'],
            'level': _log_level,
            'propagate': True,
        },
        'documents': {
            'handlers': ['search_documents'] if environment.django.logging.is_opensearch else ['console'],
            'level': _log_level,
            'propagate': True,
        },
        'results': {
            'handlers': ['search_results'] if environment.django.logging.is_opensearch else ['console'],
            'level': _log_level,
            'propagate': True,
        },
        'datagrowth.command': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
}

if not DEBUG:

    def strip_sensitive_data(event, hint):
        user_agent = event.get('request', {}).get('headers', {}).get('User-Agent', None)

        if user_agent:
            del event['request']['headers']['User-Agent']

        return event

    sentry_sdk.init(
        before_send=strip_sensitive_data,
        dsn=environment.django.sentry.dsn,
        environment=environment.service.env,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        send_default_pii=False  # GDPR requirement
    )
    # We kill all DisallowedHost logging on the servers,
    # because it happens so frequently that we can't do much about it
    ignore_logger('django.security.DisallowedHost')


# Project Open Leermaterialen

MIME_TYPE_TO_TECHNICAL_TYPE = {
    'unknown': 'unknown',
    'application/pdf': 'document',
    'application/x-pdf': 'document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'presentation',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow': 'presentation',
    'application/powerpoint': 'presentation',
    'application/vnd.ms-powerpoint.presentation.macroEnabled.12': 'presentation',
    'application/vnd.ms-powerpoint': 'presentation',
    'application/ppt': 'presentation',
    'application/msword': 'document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
    'application/rtf': 'document',
    'text/plain': 'document',
    'text/html': 'website',
    'application/vnd.ms-word': 'document',
    'application/vnd.ms-word.document.macroEnabled.12': 'document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template': 'document',
    'text/rtf': 'document',
    'application/xhtml+xml': 'website',
    'application/postscript': '?',
    'application/vnd.ms-publisher': 'document',
    'text/xml': 'website',
    'application/vnd.oasis.opendocument.spreadsheet': 'spreadsheet',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'spreadsheet',
    'application/vnd.ms-excel': 'spreadsheet',
    'video/vnd.youtube.yt': 'video',
    'video/flv': 'video',
    'video/x-flv': 'video',
    'video/quicktime': 'video',
    'video': 'video',
    'video/x-msvideo': 'video',
    'video/mpeg': 'video',
    'application/x-mplayer2': 'video',
    'video/mp4': 'video',
    'video/x-ms-wmv': 'video',
    'video/x-ms-asf': 'video',
    'image': 'image',
    'image/bmp': 'image',
    'image/pjpeg': 'image',
    'image/png': 'image',
    'image/x-icon': 'image',
    'image/x-ms-bmp': 'image',
    'image/tiff': 'image',
    'image/jpg': 'image',
    'image/gif': 'image',
    'image/jpeg': 'image',
    'application/zip': 'document',
    'application/x-zip': 'document',
    'application/x-tar': 'document',
    'application/x-stuffit': 'document',
    'application/x-rar-compressed': 'document',
    'application/x-Wikiwijs-Arrangement': 'document',
    'audio/mpeg': 'audio',
    'application/x-koan': 'audio',
    'application/vnd.koan': 'audio',
    'audio/midi': 'audio',
    'audio/x-wav': 'audio',
    'application/octet-stream': 'app',
    'application/x-yossymemo': 'app',
    'application/Inspire': 'app',
    'application/x-AS3PE': 'app',
    'application/x-Inspire': 'app',
    'application/x-smarttech-notebook': 'app',
    'application/x-zip-compressed': 'app',
    'application/x-ACTIVprimary3': 'app',
    'application/x-ibooks+zip': 'document',
    'message/rfc822': 'document',
    'application/vnd.google-earth.kmz': 'app',
    'application/x-java': 'app',
}

COPYRIGHT_VALUES = [
    "cc-by-40",
    "cc-by-30",
    "cc-by-nc-40",
    "cc-by-nc-30",
    "cc-by-nc-nd-40",
    "cc-by-nc-nd-30",
    "cc-by-nc-nd-sa-40",
    "cc-by-nc-nd-sa-30",
    "cc-by-nc-sa-40",
    "cc-by-nc-sa-30",
    "cc-by-nd-40",
    "cc-by-nd-30",
    "cc-by-nd-sa-40",
    "cc-by-nd-sa-30",
    "cc-by-sa-40",
    "cc-by-sa-30",
    "pdm-10",
    "cc0-10"
]


# Celery
# https://docs.celeryproject.org/en/v4.1.0/

CELERY_BROKER_URL = f'redis://{environment.redis.host}/0'
CELERY_RESULT_BACKEND = f'redis://{environment.redis.host}/0'
CELERY_TASK_DEFAULT_QUEUE = environment.project.name
CELERY_TASK_ROUTES = {
    'sync_indices': {'queue': f'{environment.project.name}-indexing'}
}
CELERY_BEAT_SCHEDULE = {
    'clean_data': {
        'task': 'clean_data',
        'schedule': crontab(
            hour=0,
            minute=0
        ),
    },
    'sync_indices': {
        'task': 'sync_indices',
        'schedule': 30,
    },
    'sync_metadata': {
        'task': 'sync_metadata',
        'schedule': crontab(minute=30)
    },
}
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50


# Debug Toolbar
# https://django-debug-toolbar.readthedocs.io/en/latest/

if DEBUG:
    # Activation
    INSTALLED_APPS += [
        'debug_toolbar'
    ]
    MIDDLEWARE = MIDDLEWARE[0:4] + ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE[4:]

    # Configuration
    # NB: INTERNAL_IPS doesn't work well for Docker containers
    INTERNAL_HOSTS = [
        '127.0.0.1:8888',
        'localhost:8888',
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: request.get_host() in INTERNAL_HOSTS
    }


# Datagrowth
# https://data-scope.com/datagrowth/index.html

DATAGROWTH_DATA_DIR = os.path.join(BASE_DIR, "..", "data", "harvester")
DATAGROWTH_BIN_DIR = os.path.join(BASE_DIR, "harvester", "bin")
DATA_RETENTION_PURGE_AFTER = environment.harvester.data_retention.purge_after or {}
DATA_RETENTION_KEEP_VERSIONS = environment.harvester.data_retention.keep_versions


# Internal credentials

HARVESTER_WEBHOOK_SECRET = environment.secrets.harvester.webhook_secret


# Sharekit

SHAREKIT_API_KEY = getattr(environment.secrets.sharekit, environment.project.name)
SHAREKIT_BASE_URL = environment.harvester.repositories.sharekit
SHAREKIT_WEBHOOK_ALLOWED_IPS = environment.sharekit.webhook_allowed_ips


# Edurep & Eduterm

EDUREP_BASE_URL = environment.harvester.repositories.edurep
EDUTERM_API_KEY = environment.secrets.eduterm.api_key


# Deepl

DEEPL_API_KEY = environment.secrets.deepl.api_key


# Google

GOOGLE_API_KEY = environment.secrets.google.api_key


# Robots
# https://pypi.org/project/django-x-robots-tag-middleware/

X_ROBOTS_TAG = ['noindex', 'nofollow']
MIDDLEWARE.append('x_robots_tag_middleware.middleware.XRobotsTagMiddleware')


# Versatile Image Field
# https://django-versatileimagefield.readthedocs.io/en/latest/installation.html

VERSATILEIMAGEFIELD_SETTINGS = {
    'sized_directory_name': 'thumbnails',
}


# Matomo

MATOMO_API_KEY = environment.secrets.matomo.api_key


# Hanze

HANZE_API_KEY = environment.secrets.hanze.api_key


# Teams webhooks

SEND_ADMIN_NOTIFICATIONS = environment.django.send_admin_notifications
TEAMS_HARVESTER_WEBHOOK = environment.secrets.teams_webhooks.harvester


# Sources

SOURCES = {
    "han": {
        "endpoint": environment.harvester.repositories.han,
        "api_key": None
    },
    "hva": {
        "endpoint": environment.harvester.repositories.hva,
        "api_key": environment.secrets.hva.api_key
    },
    "hku": {
        "endpoint": "https://octo.hku.nl",
        "api_key": None
    },
    "greeni": {
        "endpoint": "https://www.greeni.nl",
        "api_key": None
    },
    "buas": {
        "endpoint": "https://pure.buas.nl",
        "api_key": environment.secrets.buas.api_key
    },
    "hanze": {
        "endpoint": environment.harvester.repositories.hanze,
        "api_key": environment.secrets.hanze.api_key
    },
}
