"""
Django settings for clube project.
Le configuracoes do ficheiro .env via variaveis de ambiente.
"""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════
# SEGURANCA
# ══════════════════════════════════════════════════════════════
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-muda-em-producao')
DEBUG      = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')


# ══════════════════════════════════════════════════════════════
# APPS
# ══════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'axes',
    # local
    'app',
]

MIDDLEWARE = [
    'axes.middleware.AxesMiddleware',                          # ← primeiro sempre
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF    = 'clube.urls'
WSGI_APPLICATION = 'clube.wsgi.application'
ASGI_APPLICATION = 'clube.asgi.application'


# ══════════════════════════════════════════════════════════════
# TEMPLATES
# ══════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════
# BASE DE DADOS
# ══════════════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : os.environ.get('DB_NAME',     'e_commerce'),
        'USER'    : os.environ.get('DB_USER',     'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST'    : os.environ.get('DB_HOST',     'localhost'),
        'PORT'    : os.environ.get('DB_PORT',     '5432'),
    }
}


# ══════════════════════════════════════════════════════════════
# CHANNELS (WebSocket)
# ══════════════════════════════════════════════════════════════
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', 'redis'), 6379)],
        },
    }
}


# ══════════════════════════════════════════════════════════════
# JWT
# ══════════════════════════════════════════════════════════════
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS' : True,
    'AUTH_HEADER_TYPES'     : ('Bearer',),
}


# ══════════════════════════════════════════════════════════════
# REST FRAMEWORK
# ══════════════════════════════════════════════════════════════
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}


# ══════════════════════════════════════════════════════════════
# CORS
# ══════════════════════════════════════════════════════════════
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:8080,http://127.0.0.1:8080'
).split(',')

CORS_ALLOW_CREDENTIALS = True


# ══════════════════════════════════════════════════════════════
# STRIPE
# ══════════════════════════════════════════════════════════════
STRIPE_SECRET_KEY     = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


# ══════════════════════════════════════════════════════════════
# EMAIL  (para reset de password)
# ══════════════════════════════════════════════════════════════
EMAIL_BACKEND       = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@ecommerce.com')

FRONTEND_BASE_URL   = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:8080')


# ══════════════════════════════════════════════════════════════
# FICHEIROS
# ══════════════════════════════════════════════════════════════
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ══════════════════════════════════════════════════════════════
# PASSWORDS
# ══════════════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ══════════════════════════════════════════════════════════════
# LOCALIZACAO
# ══════════════════════════════════════════════════════════════
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE     = 'Atlantic/Cape_Verde'
USE_I18N      = True
USE_TZ        = True


# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CACHE (Redis)
# ══════════════════════════════════════════════════════════════
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_HOST', 'redis')}:6379/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


# RATE LIMITING (django-axes)
# ══════════════════════════════════════════════════════════════
AXES_FAILURE_LIMIT        = 5        # bloqueia apos 5 tentativas falhadas
AXES_COOLOFF_TIME         = 1        # desbloqueia apos 1 hora
AXES_LOCKOUT_PARAMETERS   = ['ip_address']  # bloqueia por IP
AXES_RESET_ON_SUCCESS     = True     # reset do contador apos login com sucesso
AXES_LOCKOUT_CALLABLE     = None     # comportamento padrao (retorna 403)
AXES_ENABLE_ADMIN         = True     # ve tentativas bloqueadas no Django Admin
AXES_IGNORE_URLS = [                         # ← e isto
    '/app/utilizador/registar/',
    '/app/utilizador/recuperar_senha/',
    '/app/utilizador/recuperar_senha/confirmar/',
]