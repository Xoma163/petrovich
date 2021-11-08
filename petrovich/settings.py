import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from apps.bot.classes.consts.Consts import Platform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import environ

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, 'secrets/.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')

MAIN_PROTOCOL = 'https'
MAIN_DOMAIN = "andrewsha.net"
MAIN_SITE = f'{MAIN_PROTOCOL}://{MAIN_DOMAIN}'
DOMAINS_IPS = ['192.168.1.10', '46.0.113.246']
DOMAINS = [MAIN_DOMAIN]
SUBDOMAINS = [None, 'api', 'www', 'birds']
SUBDOMAINS_DOMAINS = []
for subdomain in SUBDOMAINS:
    for domain in DOMAINS:
        if subdomain:
            SUBDOMAINS_DOMAINS.append(f"{subdomain}.{domain}")
        else:
            SUBDOMAINS_DOMAINS.append(domain)

ALLOWED_HOSTS = DOMAINS_IPS + SUBDOMAINS_DOMAINS

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

VENDORS_APPS = [
    'django_hosts',
    'webpack_loader',
    'rest_framework',

]

PROJECT_APPS = [
    'apps.bot',
    'apps.birds',
    'apps.service',
    'apps.games',
    'apps.web',
]

INSTALLED_APPS = DJANGO_APPS + VENDORS_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]
DEFAULT_HOST = 'www'
ROOT_HOSTCONF = 'petrovich.hosts'
ROOT_URLCONF = 'petrovich.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), 'templates'],
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

WSGI_APPLICATION = 'petrovich.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {'default': env.db('DATABASE_URL', default='postgres:///petrovich')}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Samara'
DEFAULT_TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles')
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS_ORIGIN_ALLOW_ALL = True
VK_URL = "https://vk.com/"

# Logging
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

DEBUG_FILE = os.path.join(LOGS_DIR, 'commands-debug.log')
ERROR_FILE = os.path.join(LOGS_DIR, 'commands-error.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'commands': {
            'format': '%(levelname)-8s %(asctime)-25s %(message)s',
        },
        'commands-console': {
            'format': '%(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'file-debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': DEBUG_FILE,
            'formatter': 'commands',
        },
        'file-error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': ERROR_FILE,
            'formatter': 'commands',
        },
        'console-warn': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'commands-console',
        },
        'console-debug': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'commands-console',
        },
    },
    'loggers': {
        Platform.VK.name: {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': True,
        },
        Platform.TG.name: {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
if DEBUG:
    LOGGING['loggers'][Platform.TG.name]['handlers'].append('console-debug')
    LOGGING['loggers'][Platform.TG.name]['handlers'].append('console-debug')

CORS_ORIGIN_ALLOW_ALL = True
VK_URL = "https://vk.com/"

AMAZON_REGION = "eu-north-1"

WEBPACK_DEV_SERVER = DEBUG

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': '/',  # must end with slash
        'STATS_FILE': str(os.path.join(BASE_DIR, 'frontend/webpack-stats.json')),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map'],
    }
}

REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
