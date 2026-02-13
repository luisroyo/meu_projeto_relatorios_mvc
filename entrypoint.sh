#!/bin/bash
set -e

echo "=== INICIANDO DEPLOY ==="
echo "Porta: $PORT"
echo "Ambiente: $FLASK_ENV"

# Aguarda um pouco para o banco estar pronto
echo "Aguardando banco de dados..."
sleep 5

# Aplica migrations com timeout
echo "Aplicando migrations..."
# Entra no diretório da aplicação Flask (o backend interno)
cd backend/backend

echo "DEBUG: Current Directory is $(pwd)"
echo "DEBUG: Listing files in current directory:"
ls -la

# Adiciona diretório atual ao PYTHONPATH (caminho absoluto)
export PYTHONPATH=$PYTHONPATH:$(pwd)
export FLASK_APP="app:create_app()"

echo "DEBUG: Testing python imports..."
python -c "import sys; print('PYTHONPATH:', sys.path); import config; print('Check: config imported successfully')"

# Aplica migrations (assume que pasta migrations está aqui)
timeout 300 flask db upgrade -d migrations || {
    echo "ERRO: Timeout ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Inicia o Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn "app:create_app()" \
    --config gunicorn.conf.py

