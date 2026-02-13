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
export PYTHONPATH="backend:${PYTHONPATH}"
export FLASK_APP="app:create_app()"

timeout 300 flask db upgrade -d backend/migrations || {
    echo "ERRO: Timeout ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Inicia o Gunicorn com configurações otimizadas
echo "Iniciando Gunicorn..."
# Garante que backend/ está no PYTHONPATH
export PYTHONPATH="backend:${PYTHONPATH}"
exec gunicorn "app:create_app()" \
    --config backend/gunicorn.conf.py

