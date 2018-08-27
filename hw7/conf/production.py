import json

from django.core.exceptions import ImproperlyConfigured

from .base import *


with open('secrets.json') as f:
    secrets_data = json.loads(f.read())


def get_secret(setting, secrets=secrets_data):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {0} variable'.format(setting)
        raise ImproperlyConfigured(error_msg)


DEBUG = False

SECRET_KEY = get_secret('SECRET_KEY')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': get_secret('DB_HOST'),
        'PORT': get_secret('DB_PORT'),
        'NAME': get_secret('DB_NAME'),
        'USER': get_secret('DB_USER'),
        'PASSWORD': get_secret('DB_PASSWORD')
    }
}

SEND_EMAIL = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = get_secret('EMAIL_PORT')
EMAIL_HOST_USER = get_secret('EMAIL_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_PASSWORD')


MEDIA_ROOT = os.path.join(BASE_DIR, "media")
