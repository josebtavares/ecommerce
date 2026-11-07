#!/bin/sh
# Arranque do serviço "worker" (Railway, railway.worker.json): conversão de vídeos, limpeza de ficheiros
# e ciclo das subscrições. Sem servidor web. Se o processo cair, o Railway reinicia o serviço (restartPolicy ALWAYS).
# As tarefas usam select_for_update(skip_locked) — é seguro haver mais do que um worker ao mesmo tempo.
exec python manage.py processar_videos
