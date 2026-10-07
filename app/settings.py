"""
Django settings for app project.

Configuração por variáveis de ambiente (nenhuma é obrigatória em desenvolvimento):

    DJANGO_DEBUG           1 (padrão, desenvolvimento) ou 0 (produção)
    DJANGO_SECRET_KEY      obrigatória quando DJANGO_DEBUG=0
    DJANGO_ALLOWED_HOSTS   hosts separados por vírgula, ex.: "sushibom.com.br,www.sushibom.com.br"
    DJANGO_HTTPS_PROXY     1 se o site estiver atrás de um proxy que envia X-Forwarded-Proto
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _ambiente_bool(nome, padrao):
    return os.environ.get(nome, str(int(padrao))).strip().lower() in ('1', 'true', 'yes', 'sim', 'on')


DEBUG = _ambiente_bool('DJANGO_DEBUG', True)

# Chave usada SOMENTE em desenvolvimento. Em produção, defina DJANGO_SECRET_KEY.
_CHAVE_DESENVOLVIMENTO = 'django-insecure-n!k=eh7#%f#*cxg9rpt=^lng%ts%8t0kc@yrx2q__95(#e$q4e'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or (_CHAVE_DESENVOLVIMENTO if DEBUG else None)
if not SECRET_KEY:
    raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY quando DJANGO_DEBUG=0.')

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cliente',
    'Principal',
    'produto',
    'categoria',
    'carrinho',
    'pedido',
    'itens_pedido',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

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

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static e media

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # destino do `manage.py collectstatic` em produção

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'app', 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Limites de upload (imagens de produto são validadas nos formulários)

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644


# Segurança

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True  # os formulários usam {% csrf_token %}; nenhum script lê o cookie
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    if _ambiente_bool('DJANGO_HTTPS_PROXY', False):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
