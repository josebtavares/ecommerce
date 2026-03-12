# ══════════════════════════════════════════════════════════════
# Dockerfile — Backend Django
# ══════════════════════════════════════════════════════════════
FROM python:3.11-slim

# evita ficheiros .pyc e output buffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# instala dependências do sistema (necessárias para psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
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
