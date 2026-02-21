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
# Entra no diretório da aplicação Flask
cd backend

# Adiciona diretório atual ao PYTHONPATH (caminho absoluto)
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "APP DIR: $(pwd)"
echo "Conteúdo do diretório:"
ls -la

export FLASK_APP="app:create_app()"

# Aplica migrations (assume que pasta migrations está aqui)
# Tenta rodar o comando flask db upgrade
echo "Marcando migração atual como head (para pular criação no Supabase já povoado)..."
flask db stamp head -d migrations

echo "Rodando flask db upgrade..."
flask db upgrade -d migrations || {
    echo "ERRO: Falha ao aplicar migrations"
    exit 1
}

echo "Migrations aplicadas com sucesso!"

# Inicia o Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn "app:create_app()" \
    --config gunicorn.conf.py

