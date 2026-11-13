# ══════════════════════════════════════════════════════════════
# Dockerfile — Backend Django
# ══════════════════════════════════════════════════════════════
FROM python:3.11-slim

# evita ficheiros .pyc e output buffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# chave do repositório do PostgreSQL (PGDG) guardada no projeto — descarregá-la do postgresql.org durante o
# build falhava às vezes no Railway (SSL unexpected EOF). Impressão digital: B97B 0AFC AA1A 47F0 44F2 44A0 7FCC 7D46 ACCC 4CF8
COPY docker/pgdg.asc /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc

# instala dependências do sistema (psycopg2; ffmpeg para otimizar vídeos;
# pg_dump 18 — a mesma versão do Postgres da prod — para os backups, utils/backups.py)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg \
    curl \
    ca-certificates \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y postgresql-client-18 \
    && rm -rf /var/lib/apt/lists/*

# instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# copia o código
COPY . .

# porta que o Django vai usar
EXPOSE 8000

# script de arranque
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
