#!/usr/bin/env python3
"""
Script para testar conexão com Redis
Execute: python test_redis.py
"""

import os
import redis
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_redis_connection():
    """Testa a conexão com o Redis."""
    print("🔍 Testando configuração do Redis...")
    
    # Verifica variáveis de ambiente
    redis_url = os.getenv("REDIS_URL")
    cache_redis_url = os.getenv("CACHE_REDIS_URL")
    
    # URL final que será usada (prioridade para REDIS_URL, depois CACHE_REDIS_URL)
    final_redis_url = redis_url or cache_redis_url
    
    print(f"REDIS_URL: {'✅ Configurada' if redis_url else '❌ Não configurada'}")
    print(f"CACHE_REDIS_URL: {'✅ Configurada' if cache_redis_url else '❌ Não configurada'}")
    print(f"URL Final: {'✅ ' + final_redis_url.split('@')[1] if final_redis_url else '❌ Nenhuma configurada'}")
    
    # Testa conexão com Redis
    if final_redis_url:
        try:
            print(f"\n🔗 Tentando conectar com: {final_redis_url.split('@')[1] if '@' in final_redis_url else final_redis_url}")
            r = redis.from_url(final_redis_url)
            
            # Testa ping
            pong = r.ping()
            print(f"Ping: {'✅ Sucesso' if pong else '❌ Falha'}")
            
            # Testa operações básicas
            r.set('test_key', 'test_value', ex=60)  # Expira em 60 segundos
            value = r.get('test_key')
            print(f"Set/Get: {'✅ Sucesso' if value == b'test_value' else '❌ Falha'}")
            
            # Limpa o teste
            r.delete('test_key')
            print("🧹 Chave de teste removida")
            
            print("🎉 Redis está funcionando perfeitamente!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar com Redis: {e}")
            return False
    else:
        print("⚠️  REDIS_URL não configurada. O sistema usará SimpleCache (memória local).")
        return False

def check_cache_config():
    """Verifica a configuração de cache da aplicação."""
    print("\n📋 Verificando configuração de cache...")
    
    try:
        import sys
        import os
        # Adiciona o diretório raiz ao path para importar config
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from config import Config, DevelopmentConfig, ProductionConfig
        
        # Testa configuração base
        config = Config()
        print(f"Config Base - CACHE_TYPE: {config.CACHE_TYPE}")
        
        # Testa configuração de desenvolvimento
        dev_config = DevelopmentConfig()
        print(f"Development - CACHE_TYPE: {dev_config.CACHE_TYPE}")
        
        # Testa configuração de produção
        prod_config = ProductionConfig()
        print(f"Production - CACHE_TYPE: {prod_config.CACHE_TYPE}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar configuração: {e}")

if __name__ == "__main__":
    print("🚀 Teste de Configuração do Redis")
    print("=" * 40)
    
    test_redis_connection()
    check_cache_config()
    
    print("\n" + "=" * 40)
    print("💡 Dicas:")
    print("- Para usar Redis no Render, configure REDIS_URL nas variáveis de ambiente")
    print("- Para desenvolvimento local, o SimpleCache é suficiente")
    print("- O cache é usado principalmente para respostas da API Gemini") 