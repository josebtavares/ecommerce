#!/bin/sh
# Arranque de produção (Railway) — serviço web: gunicorn com vários processos uvicorn (HTTP + WebSockets).
# O worker (vídeos, limpeza, subscrições) corre no serviço "worker" (start_worker.sh, railway.worker.json).
# Enquanto esse serviço não existir, WORKER_SEPARADO fica por definir e o worker continua a correr aqui.

# Ficheiros estáticos (admin, DRF) — servidos pelo WhiteNoise. O Dockerfile (partilhado com a dev)
# não corre o collectstatic e no build não há variáveis da prod, por isso corre aqui no arranque.
python manage.py collectstatic --noinput || echo "[static] collectstatic falhou — o site arranca na mesma"

if [ "$WORKER_SEPARADO" != "1" ]; then
  # Worker em segundo plano, com prioridade baixa para não roubar CPU ao site. Se cair, volta a arrancar ao fim de 10s.
  (
    while true; do
      nice -n 10 python manage.py processar_videos
      echo "[worker] terminou (código $?), a reiniciar em 10s"
      sleep 10
    done
  ) &
fi

# Web: WEB_CONCURRENCY processos (cada um atende HTTP e WebSockets; o channel layer no Redis liga-os).
#   --max-requests: recicla cada processo de vez em quando (evita crescer em memória); os WebSockets reconectam.
#   --graceful-timeout: num deploy, os pedidos em curso têm 30s para acabar.
exec gunicorn clube.asgi:application \
  --worker-class uvicorn_worker.UvicornWorker \
  --workers "${WEB_CONCURRENCY:-4}" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --forwarded-allow-ips '*' \
  --timeout 60 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --max-requests 5000 \
  --max-requests-jitter 500 \
  --access-logfile - \
  --error-logfile -
