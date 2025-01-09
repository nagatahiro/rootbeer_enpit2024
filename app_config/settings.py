"""
Django settings for app_config project.

Generated by 'django-admin startproject' using Django 4.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [ '127.0.0.1','localhost','waripoke.xyz','10.10.3.137','https://waripoke.xyz','162.43.90.122','10.10.0.179','192.168.0.110','10.10.1.143']

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024 # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

CSRF_TRUSTED_ORIGINS = [
    '127.0.0.1','localhost','waripoke.xyz','10.10.3.137','https://waripoke.xyz','162.43.90.122','10.10.0.179','192.168.0.110','10.10.1.143'  # または適切なドメイン
]

# Application definition


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app_folder.apps.AppFolderConfig',
    'corsheaders',
    'bootstrap4', #デザイン用
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

MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')


# settings.py

# CSRF_TRUSTED_ORIGINS: スキームを追加
CSRF_TRUSTED_ORIGINS = [
    "http://10.10.3.137",
    "http://10.10.0.179",
    "http://10.10.1.143",
    "http://127.0.0.1",
    "http://162.43.90.122",
    "http://192.168.0.110",
    "http://localhost",
    "https://waripoke.xyz",  # 必要なら https:// を使用
]

# CORS_ALLOWED_ORIGINS: スキームを追加
CORS_ALLOWED_ORIGINS = [
    "http://10.10.3.137",
    "http://10.232.65.0",
    "http://10.10.0.179",
    "http://10.10.1.143",
    "http://127.0.0.1",
    "http://162.43.90.122",
    "http://192.168.0.110",
    "http://localhost",
    "https://waripoke.xyz",  # 必要なら https:// を使用
]


ROOT_URLCONF = 'app_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'app_config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# メディアファイルに関する設定
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = "app_folder:login"      ### 追加
LOGIN_REDIRECT_URL = "app_folder:home"      ### 追加
LOGOUT_REDIRECT_URL = "app_folder:top"      ### 追加

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ##＃追加

STATIC_ROOT = os.path.join(BASE_DIR, 'static')


