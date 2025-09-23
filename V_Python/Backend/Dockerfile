# Use uma imagem oficial do Python como base
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema necessárias para PostgreSQL e outras libs
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Garante que os diretórios de arquivos estáticos existam
RUN mkdir -p /app/logs /app/static /app/templates

# Define permissões corretas
RUN chmod -R 755 /app/static /app/templates

# Define variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expõe a porta que a aplicação irá usar
EXPOSE 5001

# Comando para iniciar a aplicação
# Usa gunicorn para produção
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "app:app"]