# Use uma imagem oficial do Python como base, agora com Debian Bullseye (mais atualizado)
FROM python:3.9-slim-bullseye

# Instala dependências do sistema necessárias para o psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Cria e define o diretório de trabalho para a aplicação backend
WORKDIR /app/Backend

# Copia o arquivo requirements.txt primeiro para otimização de cache
COPY Backend/requirements.txt ./

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação backend
COPY Backend/.env ./
COPY Backend/app.py ./
COPY Backend/config.py ./
COPY Backend/extensions.py ./
COPY Backend/models.py ./

# Cria os diretórios para o frontend dentro do diretório de trabalho do backend
# E copia os arquivos do frontend para os respectivos diretórios
RUN mkdir -p /app/Backend/static /app/Backend/templates /app/Backend/static/images /app/Backend/static/fonts
COPY Frontend/dashboard.html /app/Backend/templates/
COPY Frontend/index.html /app/Backend/templates/
COPY Frontend/script.js /app/Backend/static/
COPY Frontend/styles.css /app/Backend/static/
COPY Frontend/images/ /app/Backend/static/images/
COPY Frontend/fonts/ /app/Backend/static/fonts/

# Copia o script wait-for-it.sh para um local acessível globalmente
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Expõe a porta que a aplicação Flask irá rodar
EXPOSE 9001

# Comando para iniciar a aplicação:
# - Primeiro aguarda o DB.
# - Depois, 'carimba' o DB com a versão da migração mais recente (head) sem executar o upgrade.
#   Isso é ideal para quando o DB já existe e possui as tabelas.
# - Por fim, inicia a aplicação com Gunicorn.
CMD ["sh", "-c", "/usr/local/bin/wait-for-it.sh 212.85.1.215:5432 --timeout=60 --strict -- python3 -m flask db stamp head && gunicorn --bind 0.0.0.0:9001 app:app"]