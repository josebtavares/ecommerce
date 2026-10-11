#!/bin/sh
# Arranque de produção (Railway) — web + worker no mesmo serviço (opção B).
# Quando o worker passar a ser um serviço próprio, basta voltar a arrancar só o daphne.

# Worker: conversão de vídeos + limpeza de ficheiros, em segundo plano e com prioridade baixa
# para não roubar CPU ao site. Se cair, volta a arrancar ao fim de 10s.
(
  while true; do
    nice -n 10 python manage.py processar_videos
    echo "[worker] terminou (código $?), a reiniciar em 10s"
    sleep 10
  done
) &

# Web
exec python -m daphne -b 0.0.0.0 -p "$PORT" clube.asgi:application
