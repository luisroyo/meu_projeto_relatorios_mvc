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
# Ajusta PYTHONPATH e FLASK_APP para novo layout em backend/
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
export FLASK_APP="backend.app:create_app()"

# Aplica migrations
timeout 300 flask db upgrade -d backend/migrations || {
    echo "ERRO: Timeout ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Inicia o Gunicorn com configurações otimizadas
echo "Iniciando Gunicorn..."
exec gunicorn "backend.app:create_app()" \
    --config backend/gunicorn.conf.py

