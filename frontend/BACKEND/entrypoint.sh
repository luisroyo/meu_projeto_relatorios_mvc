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
timeout 300 flask db upgrade || {
    echo "ERRO: Timeout ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Inicia o Gunicorn com configurações otimizadas
echo "Iniciando Gunicorn..."
exec gunicorn "app:create_app()" \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --workers 2 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload
