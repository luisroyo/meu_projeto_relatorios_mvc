#!/usr/bin/env python3
"""
Script para gerenciar o banco de dados PostgreSQL local.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, check=True):
    """Executa um comando e retorna o resultado."""
    print(f"🔄 Executando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"✅ Saída: {result.stdout.strip()}")
    
    if result.stderr:
        print(f"⚠️  Erro: {result.stderr.strip()}")
    
    if check and result.returncode != 0:
        print(f"❌ Comando falhou com código {result.returncode}")
        return False
    
    return True

def start_local_db():
    """Inicia o banco de dados local."""
    print("🚀 Iniciando PostgreSQL local...")
    
    # Verificar se Docker está rodando
    if not run_command("docker info", check=False):
        print("❌ Docker não está rodando. Inicie o Docker Desktop primeiro.")
        return False
    
    # Iniciar o container
    if run_command("docker-compose up -d postgres_local"):
        print("✅ PostgreSQL local iniciado com sucesso!")
        print("📊 URL: postgresql://postgres:postgres123@localhost:5432/relatorios_dev")
        return True
    else:
        print("❌ Falha ao iniciar PostgreSQL local")
        return False

def stop_local_db():
    """Para o banco de dados local."""
    print("🛑 Parando PostgreSQL local...")
    
    if run_command("docker-compose down"):
        print("✅ PostgreSQL local parado com sucesso!")
        return True
    else:
        print("❌ Falha ao parar PostgreSQL local")
        return False

def reset_local_db():
    """Reseta o banco de dados local (remove todos os dados)."""
    print("🔄 Resetando PostgreSQL local...")
    
    if run_command("docker-compose down -v"):
        print("✅ Volumes removidos")
        
        if run_command("docker-compose up -d postgres_local"):
            print("✅ PostgreSQL local reiniciado com sucesso!")
            return True
    
    print("❌ Falha ao resetar PostgreSQL local")
    return False

def check_local_db():
    """Verifica o status do banco de dados local."""
    print("🔍 Verificando status do PostgreSQL local...")
    
    # Verificar se o container está rodando
    result = subprocess.run("docker ps --filter name=relatorios_postgres_local --format '{{.Status}}'", 
                          shell=True, capture_output=True, text=True)
    
    if result.stdout.strip():
        print(f"✅ Container rodando: {result.stdout.strip()}")
        return True
    else:
        print("❌ Container não está rodando")
        return False

def setup_local_env():
    """Configura o ambiente local."""
    print("⚙️  Configurando ambiente local...")
    
    # Verificar se .env.local existe
    env_local = Path(".env.local")
    env_example = Path("env.local.example")
    
    if not env_local.exists() and env_example.exists():
        print("📝 Criando .env.local a partir do exemplo...")
        run_command(f"copy env.local.example .env.local")
        print("✅ Arquivo .env.local criado!")
        print("💡 Edite o arquivo .env.local se necessário")
    else:
        print("✅ Arquivo .env.local já existe")

def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("""
🔧 Gerenciador de Banco de Dados Local

Uso: python scripts/manage_local_db.py <comando>

Comandos disponíveis:
  start    - Inicia o PostgreSQL local
  stop     - Para o PostgreSQL local
  reset    - Reseta o banco (remove todos os dados)
  check    - Verifica o status do banco
  setup    - Configura o ambiente local
  all      - Executa setup + start + check

Exemplo:
  python scripts/manage_local_db.py start
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_local_db()
    elif command == "stop":
        stop_local_db()
    elif command == "reset":
        reset_local_db()
    elif command == "check":
        check_local_db()
    elif command == "setup":
        setup_local_env()
    elif command == "all":
        setup_local_env()
        if start_local_db():
            time.sleep(5)  # Aguardar inicialização
            check_local_db()
    else:
        print(f"❌ Comando desconhecido: {command}")

if __name__ == "__main__":
    main() 