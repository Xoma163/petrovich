import environ
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, 'secrets/.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')
MAIN_PROTOCOL = 'https'
MAIN_DOMAIN = "petrovich.andrewsha.net"
LOCAL_DOMAIN = "192.168.1.10"

ALLOWED_HOSTS = [MAIN_DOMAIN, LOCAL_DOMAIN]

if DEBUG:
    MAIN_SITE = f'https://{LOCAL_DOMAIN}'
else:
    MAIN_SITE = f'https://{MAIN_DOMAIN}'

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
    "django_extensions"
]

PROJECT_APPS = [
    'apps.bot',
    'apps.service',
    'apps.games'
]

INSTALLED_APPS = DJANGO_APPS + VENDORS_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres:///petrovich')
}

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
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            'format': '%(levelname)-8s %(asctime)-25s %(name)-10s %(filename)s:%(lineno)d %(message)s',
            "json_ensure_ascii": False
        },
        'color_simple': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)-8s %(name)-10s %(filename)s:%(lineno)d\n%(message)s',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        }
    },
    'handlers': {
        'file-debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'backupCount': 5,  # keep at most 10 log files
            'maxBytes': 10485760,  # 100*1024*1024 bytes (10MB)
            'filename': DEBUG_FILE,
            'formatter': 'json',
        },
        'file-error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': ERROR_FILE,
            'formatter': 'json',
        },
        'console-debug': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color_simple',
        },
    },
    'loggers': {
        'bot': {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'responses': {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'notifier': {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'subscribe_notifier': {
            'handlers': ['file-debug', 'file-error'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
if DEBUG:
    LOGGING['loggers']['bot']['handlers'].append('console-debug')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
