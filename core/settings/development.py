import os
from core.settings.base import *
from dotenv import load_dotenv

load_dotenv(Path.joinpath(BASE_DIR, '.env/env_devel'))

SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

STATIC_ROOT = Path.joinpath(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    Path.joinpath(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'