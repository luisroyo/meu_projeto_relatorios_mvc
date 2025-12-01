#!/bin/bash
set -e

echo "=== INICIANDO DEPLOY ==="
echo "Porta: $PORT"
echo "Ambiente: $FLASK_ENV"

# Aguarda um pouco para o banco estar pronto
echo "Aguardando banco de dados..."
sleep 5

# Ajusta PYTHONPATH para incluir o diretório backend
# Isso permite que os imports funcionem corretamente
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"

# Aplica migrations com timeout
echo "Aplicando migrations..."
# Muda para o diretório backend para executar os comandos Flask
cd backend

# Configura FLASK_APP para o módulo app
export FLASK_APP="app:create_app()"

timeout 300 flask db upgrade -d migrations || {
    echo "ERRO: Timeout ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Volta para o diretório raiz
cd ..

# Inicia o Gunicorn com configurações otimizadas
echo "Iniciando Gunicorn..."
# Garante que o PYTHONPATH está correto
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
# Muda para o diretório backend antes de iniciar o Gunicorn
cd backend
exec gunicorn "app:create_app()" \
    --config gunicorn.conf.py \
    --bind "0.0.0.0:${PORT:-5000}"
