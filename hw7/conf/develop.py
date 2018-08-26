from .base import *


DEBUG = True
SECRET_KEY = '_^udofw1*%0_nfpmwl483h3b2*&8csh_u0gcv2kgd=*4)-a=$$'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

SEND_EMAIL = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = ''
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''


MEDIA_ROOT = os.path.join(BASE_DIR, "media")
