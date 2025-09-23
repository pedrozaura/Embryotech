#!/bin/sh

# Aguarda o banco de dados
/usr/local/bin/wait-for-it.sh 212.85.1.215:5432 --timeout=60 --strict --

# Aplica o carimbo da migração
echo "Aplicando o carimbo do banco de dados..."
python3 -m flask db stamp head

# Inicia a aplicação com Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:9001 app:app