import os

import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, 'secrets/.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')

MAIN_PROTOCOL = 'https'
MAIN_DOMAIN = "xoma163.xyz"
MAIN_SITE = f'{MAIN_PROTOCOL}://{MAIN_DOMAIN}'
DOMAINS_IPS = ['192.168.1.10', '85.113.60.5']
DOMAINS = ['xoma163.xyz', 'xoma163.site']
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

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.bot',
    'apps.birds',
    'apps.service',
    'apps.games',
    'apps.db_logger'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'petrovich.urls'

TEMPLATES = [
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

WSGI_APPLICATION = 'petrovich.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {'default': env.db('DATABASE_URL')}

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
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CORS_ORIGIN_ALLOW_ALL = True
VK_URL = "https://vk.com/"
TEST_CHAT_ID = 2

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
        'file-warn': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': ERROR_FILE,
            'formatter': 'commands',
        },
        'console-warn': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'commands-console',
        },
        'db_log': {
            'level': 'DEBUG',
            'class': 'apps.db_logger.db_log_handler.DatabaseLogHandler'
        },
    },
    'loggers': {
        'vk': {
            'handlers': ['file-debug', 'file-warn', 'console-warn', 'db_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tg': {
            'handlers': ['file-debug', 'file-warn', 'console-warn', 'db_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CORS_ORIGIN_ALLOW_ALL = True
VK_URL = "https://vk.com/"
TEST_CHAT_ID = 3
