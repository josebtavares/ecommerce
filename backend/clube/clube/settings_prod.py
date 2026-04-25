"""
Settings de PRODUÇÃO — Railway
Ficheiro novo — não modificar o settings.py original.
Fica em: backend/clube/clube/settings_prod.py
"""

from .settings import *
import os
import dj_database_url

# Adicionar storages ao INSTALLED_APPS
INSTALLED_APPS = INSTALLED_APPS + ['storages']

# Corrigir staticfiles storage


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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

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


# ══════════════════════════════════════════════════════════════
# CLOUDFLARE R2 — Storage para ficheiros media (imagens)
# Substitui a pasta media/ local por storage permanente na cloud
# ══════════════════════════════════════════════════════════════



AWS_ACCESS_KEY_ID     = os.environ.get('R2_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'nosloja-media')
AWS_S3_ENDPOINT_URL   = os.environ.get('R2_ENDPOINT_URL', '')
AWS_S3_REGION_NAME    = 'auto'
AWS_DEFAULT_ACL       = 'public-read'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH  = False  # URLs públicos sem assinatura

# URL público das imagens (usar o domínio público do bucket)
AWS_S3_CUSTOM_DOMAIN  = os.environ.get('R2_PUBLIC_DOMAIN', '')

# Usar R2 para ficheiros media
DEFAULT_FILE_STORAGE  = 'storages.backends.s3boto3.S3Boto3Storage'

# Media URL aponta para o R2
if AWS_S3_CUSTOM_DOMAIN:
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'

# Proxy headers para URLs correctos atrás do Railway
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ══════════════════════════════════════════════════════════════
# SENTRY — monitorização de erros em produção
# ══════════════════════════════════════════════════════════════
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', ''),
    traces_sample_rate=0.1,
    send_default_pii=False,
)