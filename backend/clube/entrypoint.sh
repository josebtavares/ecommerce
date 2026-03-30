#!/bin/sh
# Script de arranque do container Django

set -e

echo "â³ A aguardar base de dados..."

while ! python -c "
import os, psycopg2
try:
    psycopg2.connect(
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
    )
except psycopg2.OperationalError:
    exit(1)
" 2>/dev/null; do
  echo "   PostgreSQL nao esta pronto -- a tentar novamente em 2s..."
  sleep 2
done

echo "âœ… PostgreSQL pronto!"

echo "â³ A aguardar Redis..."

while ! python -c "
import os, redis
try:
    r = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379)
    r.ping()
except Exception:
    exit(1)
" 2>/dev/null; do
  echo "   Redis nao esta pronto -- a tentar novamente em 2s..."
  sleep 2
done

echo "âœ… Redis pronto!"

echo "ðŸ”„ A correr migrations..."
python manage.py migrate --noinput

echo "ðŸ“ A recolher ficheiros estaticos..."
python manage.py collectstatic --noinput

echo "ðŸš€ A iniciar servidor com 4 workers..."
exec python -m daphne -b 0.0.0.0 -p 8000 clube.asgi:application