"""
Settings de PRODUÇÃO — Railway
Ficheiro novo — não modificar o settings.py original.
Fica em: backend/clube/clube/settings_prod.py
"""

from .settings import *
import os
import dj_database_url

# ══════════════════════════════════════════════════════════════
# SEGURANÇA
# ══════════════════════════════════════════════════════════════

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# ══════════════════════════════════════════════════════════════
# BASE DE DADOS
# Railway injeta DATABASE_URL automaticamente quando adicionas PostgreSQL.
# O dj_database_url lê essa variável e configura tudo sozinho.
# ══════════════════════════════════════════════════════════════

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

# ══════════════════════════════════════════════════════════════
# CORS
# ══════════════════════════════════════════════════════════════

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# ══════════════════════════════════════════════════════════════
# FICHEIROS ESTÁTICOS — WhiteNoise serve CSS/JS do Django
# ══════════════════════════════════════════════════════════════

_idx = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(_idx + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ══════════════════════════════════════════════════════════════
# MEDIA — não persiste entre deploys (ok para testes)
# Para produção real: configurar Cloudflare R2 ou AWS S3
# ══════════════════════════════════════════════════════════════

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ══════════════════════════════════════════════════════════════
# REDIS
# Railway injeta REDIS_URL automaticamente quando adicionas Redis.
# ══════════════════════════════════════════════════════════════

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# ══════════════════════════════════════════════════════════════
# STRIPE — vem das variáveis de ambiente do Railway
# ══════════════════════════════════════════════════════════════

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# ══════════════════════════════════════════════════════════════
# EMAIL — console por agora, configurar Resend depois
# ══════════════════════════════════════════════════════════════

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@nosloja.pt')

# ══════════════════════════════════════════════════════════════
# FRONTEND
# ══════════════════════════════════════════════════════════════

FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', '')
