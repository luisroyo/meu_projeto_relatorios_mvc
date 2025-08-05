#!/usr/bin/env python3
"""
Script para monitorar a conexão com o banco de dados PostgreSQL.
Útil para detectar e resolver problemas de conexão SSL no Render.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy.exc import OperationalError, DisconnectionError
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection():
    """Testa a conexão com o banco de dados."""
    try:
        # Testa uma query simples
        result = db.session.execute(text('SELECT 1 as test'))
        row = result.fetchone()
        
        if row and row[0] == 1:
            logger.info("✅ Conexão com banco de dados OK")
            return True
        else:
            logger.error("❌ Query de teste falhou")
            return False
            
    except OperationalError as e:
        if "SSL connection has been closed" in str(e):
            logger.error("❌ Erro SSL: Conexão SSL fechada inesperadamente")
        else:
            logger.error(f"❌ Erro operacional: {e}")
        return False
        
    except DisconnectionError as e:
        logger.error(f"❌ Erro de desconexão: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False

def reconnect():
    """Tenta reconectar ao banco de dados."""
    logger.info("🔄 Tentando reconectar ao banco de dados...")
    
    try:
        # Fecha conexões existentes
        db.session.rollback()
        db.session.close()
        db.engine.dispose()
        
        # Aguarda um pouco
        time.sleep(2)
        
        # Testa nova conexão
        if test_connection():
            logger.info("✅ Reconexão bem-sucedida!")
            return True
        else:
            logger.error("❌ Falha na reconexão")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro durante reconexão: {e}")
        return False

def monitor_connection(duration_minutes=5, interval_seconds=30):
    """
    Monitora a conexão por um período específico.
    
    Args:
        duration_minutes: Duração do monitoramento em minutos
        interval_seconds: Intervalo entre testes em segundos
    """
    logger.info(f"🔍 Iniciando monitoramento por {duration_minutes} minutos...")
    logger.info(f"⏱️  Intervalo de teste: {interval_seconds} segundos")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    successful_tests = 0
    failed_tests = 0
    
    while time.time() < end_time:
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if test_connection():
            successful_tests += 1
            logger.info(f"[{current_time}] ✅ Teste {successful_tests + failed_tests} - OK")
        else:
            failed_tests += 1
            logger.warning(f"[{current_time}] ❌ Teste {successful_tests + failed_tests} - FALHOU")
            
            # Tenta reconectar
            if reconnect():
                logger.info("✅ Reconexão automática bem-sucedida")
            else:
                logger.error("❌ Falha na reconexão automática")
        
        # Aguarda até o próximo teste
        if time.time() < end_time:
            time.sleep(interval_seconds)
    
    # Relatório final
    total_tests = successful_tests + failed_tests
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    logger.info("=" * 60)
    logger.info("📊 RELATÓRIO FINAL DE MONITORAMENTO")
    logger.info("=" * 60)
    logger.info(f"⏱️  Duração: {duration_minutes} minutos")
    logger.info(f"🔢 Total de testes: {total_tests}")
    logger.info(f"✅ Testes bem-sucedidos: {successful_tests}")
    logger.info(f"❌ Testes falharam: {failed_tests}")
    logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 95:
        logger.info("🎉 Conexão estável!")
    elif success_rate >= 80:
        logger.warning("⚠️  Conexão com algumas instabilidades")
    else:
        logger.error("🚨 Conexão muito instável - verificar configurações!")

def check_environment():
    """Verifica as variáveis de ambiente."""
    logger.info("🔍 Verificando variáveis de ambiente...")
    
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Mascara a senha para segurança
        masked_url = database_url.replace(
            database_url.split("@")[0].split(":")[-1], 
            "***"
        ) if "@" in database_url else database_url
        
        logger.info(f"✅ DATABASE_URL configurada: {masked_url}")
        
        # Verifica se é Render
        if "render.com" in database_url or "onrender.com" in database_url:
            logger.info("🌐 Detectado ambiente Render")
            
            # Verifica parâmetros SSL
            if "sslmode=require" in database_url:
                logger.info("✅ SSL configurado corretamente")
            else:
                logger.warning("⚠️  SSL não configurado - adicionar ?sslmode=require")
        else:
            logger.info("🏠 Ambiente local detectado")
    else:
        logger.error("❌ DATABASE_URL não configurada!")
        return False
    
    return True

def main():
    """Função principal."""
    logger.info("🚀 Iniciando monitor de conexão com banco de dados")
    logger.info("=" * 60)
    
    # Verifica ambiente
    if not check_environment():
        logger.error("❌ Configuração de ambiente inválida")
        sys.exit(1)
    
    # Cria aplicação
    try:
        app = create_app()
        with app.app_context():
            logger.info("✅ Aplicação Flask criada com sucesso")
            
            # Teste inicial
            logger.info("🔍 Teste inicial de conexão...")
            if test_connection():
                logger.info("✅ Conexão inicial OK")
            else:
                logger.error("❌ Falha na conexão inicial")
                if not reconnect():
                    logger.error("❌ Não foi possível estabelecer conexão")
                    sys.exit(1)
            
            # Inicia monitoramento
            monitor_connection(duration_minutes=5, interval_seconds=30)
            
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar aplicação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 