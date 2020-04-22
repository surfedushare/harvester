"""
Django settings for warehouse project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from sentry_sdk.integrations.logging import ignore_logger

from surf.settings.configuration import environment, MODE

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
# In general: all defaults for secrets in this file are for development only, other defaults are production defaults
SECRET_KEY = environment.django.secret_key

# Become aware of the frontend that this backend is build for
# We whitelist this URL entirely to be able to share (login!) cookies
FRONTEND_DOMAIN = environment.django.frontend_domain
PROTOCOL = environment.django.protocol
FRONTEND_BASE_URL = "{}://{}".format(PROTOCOL, FRONTEND_DOMAIN)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = environment.django.debug

ALLOWED_HOSTS = [
    "localhost",
    environment.django.backend_domain
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# list of allowed endpoints to redirect
ALLOWED_REDIRECT_HOSTS = [
    FRONTEND_DOMAIN
]


# Application definition

INSTALLED_APPS = [
    'jet',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'ckeditor',
    'mptt',
    'social_django',

    'corsheaders',
    'rest_framework',
    'django_filters',

    'surf.vendor.surfconext',

    'surf',
    'surf.apps.users',
    'surf.apps.filters',
    'surf.apps.materials',
    'surf.apps.communities',
    'surf.apps.themes',
    'surf.apps.stats',
    'surf.apps.locale',
    'surf.apps.querylog',
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'user-agent',
    'accept-encoding',
    'response-type',
)
CORS_EXPOSE_HEADERS = (
    'content-disposition',
)
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    FRONTEND_DOMAIN
]

SESSION_COOKIE_SECURE = PROTOCOL == "https"
CSRF_COOKIE_SECURE = PROTOCOL == "https"
SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_SAMESITE = None
CSRF_TRUSTED_ORIGINS = [
    FRONTEND_DOMAIN
]

SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'surf.urls'


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "surf.settings.jinja2.environment",
            "extensions": [
                "webpack_loader.contrib.jinja2ext.WebpackExtension",
            ],
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


WSGI_APPLICATION = 'surf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'surf',
        'USER': environment.django.postgres_user,
        'PASSWORD': environment.django.postgres_password,
        'HOST': environment.django.postgres_host,
        'PORT': 5432,
    }
}


# Django Rest Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'surf.apps.core.pagination.SurfPageNumberPagination',
    'PAGE_SIZE': 20,

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'surf.apps.users.authentication.SessionTokenAuthentication',
    ),

    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),

}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', '..', 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_ALLOW_ALL_ORIGINS = True
STATICFILES_DIRS = []
# Inside containers we sneak the STATIC_ROOT into STATICFILES_DIRS.
# When running collectstatic inside containers the root will always be empty.
# During development having root as staticfile directory provides a work around to get to the frontend build.
if MODE == "container":
    STATICFILES_DIRS += [
        os.path.join('/usr/src/static')
    ]

MEDIA_ROOT = os.path.join(BASE_DIR, '..', '..', 'media')
MEDIA_URL = '/media/'


# Django Webpack loader
# https://github.com/owais/django-webpack-loader

PORTAL_BASE_DIR = os.path.join(STATIC_ROOT, "portal")

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': PORTAL_BASE_DIR + os.sep,  # must end with slash
        'STATS_FILE': os.path.join(PORTAL_BASE_DIR, 'portal.webpack-stats.json'),
    }
}


# Logging
# https://docs.djangoproject.com/en/2.2/topics/logging/
# https://docs.sentry.io/

if not DEBUG:
    # We kill all DisallowedHost logging on the servers,
    # because it happens so frequently that we can't do much about it
    ignore_logger('django.security.DisallowedHost')


# Social Auth
# https://python-social-auth.readthedocs.io/en/latest/index.html

AUTH_USER_MODEL = 'users.User'

SOCIAL_AUTH_POSTGRES_JSONFIELD = True
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_SURF_CONEXT_OIDC_ENDPOINT = "https://oidc.surfconext.nl"
SOCIAL_AUTH_LOGIN_ERROR_URL = FRONTEND_BASE_URL
SOCIAL_AUTH_SURF_CONEXT_KEY = environment.surfconext.client_id
SOCIAL_AUTH_SURF_CONEXT_SECRET = environment.surfconext.secret_key

AUTHENTICATION_BACKENDS = (
    'surf.vendor.surfconext.oidc.backend.SurfConextOpenIDConnectBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# https://python-social-auth.readthedocs.io/en/latest/pipeline.html
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'surf.vendor.surfconext.pipeline.require_data_permissions',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'surf.vendor.surfconext.pipeline.store_data_permissions',
    'social_core.pipeline.social_auth.associate_user',
    'surf.vendor.surfconext.pipeline.get_groups',
    'surf.vendor.surfconext.pipeline.assign_communities',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

LOGIN_REDIRECT_URL = FRONTEND_BASE_URL + "/login/success"
LOGOUT_REDIRECT_URL = "https://engine.surfconext.nl/logout"

VOOT_API_ENDPOINT = environment.surfconext.voot_api_endpoint


# Search
# https://developers.wiki.kennisnet.nl/index.php/Edurep:Hoofdpagina

SEARCH_CLIENT = environment.search.client

EDUREP_JSON_API_ENDPOINT = environment.edurep.json_api_endpoint
EDUREP_XML_API_ENDPOINT = environment.edurep.xml_api_endpoint
EDUREP_SOAP_API_ENDPOINT = environment.edurep.soap_api_endpoint
EDUREP_SOAP_SUPPLIER_ID = environment.edurep.soap_supplier_id

ELASTICSEARCH_USER = environment.elastic_search.username
ELASTICSEARCH_PASSWORD = environment.elastic_search.password
ELASTICSEARCH_URL = environment.elastic_search.host


# CKEditor
# https://github.com/django-ckeditor/django-ckeditor

CKEDITOR_CONFIGS = {
    "default": {
        "width": "600px",
        "height": "250px",
        'toolbar_SurfToolbar': [
            {'name': 'document', 'items': ['Source']},
            {'name': 'clipboard', 'items': ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
            {'name': 'insert',
             'items': ['Image', 'Table', 'HorizontalRule', 'SpecialChar']},
            '/',
            {'name': 'basicstyles',
             'items': ['Bold', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock']},
            {'name': 'links', 'items': ['Link', 'Unlink']},
            '/',
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
        ],
        'toolbar': 'SurfToolbar',  # put selected toolbar config here
    }
}


# Debug Toolbar
# https://django-debug-toolbar.readthedocs.io/en/latest/

if DEBUG:
    # Activation
    INSTALLED_APPS += [
        'debug_toolbar'
    ]
    MIDDLEWARE = MIDDLEWARE[0:4] + ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE[4:]

    # Configuration
    # NB: INTERAL_IPS doesn't work well for Docker containers
    INTERNAL_HOSTS = [
        '127.0.0.1:8080',
        'localhost:8080',
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: request.get_host() in INTERNAL_HOSTS
    }
