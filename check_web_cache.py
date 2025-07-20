#!/usr/bin/env python3
"""
Script para verificar se o cache está sendo usado na aplicação web
Execute: python check_web_cache.py
"""

import os
import requests
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_web_cache():
    """Testa o cache da aplicação web."""
    print("🌐 Testando Cache da Aplicação Web")
    print("=" * 50)
    
    # URL da aplicação (ajuste conforme necessário)
    base_url = "https://processador-relatorios-ia.onrender.com"
    
    print(f"🔗 Testando aplicação: {base_url}")
    
    # Teste 1: Verificar se a aplicação está online
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200 or response.status_code == 302:
            print("✅ Aplicação está online")
        else:
            print(f"⚠️  Aplicação retornou status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erro ao acessar aplicação: {e}")
        return
    
    # Teste 2: Verificar Redis diretamente
    print("\n🔍 Verificando Redis...")
    try:
        import redis
        redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
        
        if redis_url:
            r = redis.from_url(redis_url)
            info = r.info()
            total_commands = info.get('total_commands_processed', 0)
            print(f"📊 Total de comandos Redis: {total_commands}")
            
            # Conta chaves de cache
            keys = r.keys("*")
            cache_keys = [k for k in keys if b'cache' in k.lower() or b'gemini' in k.lower()]
            print(f"🔑 Chaves de cache encontradas: {len(cache_keys)}")
            
            if cache_keys:
                print("✅ Cache está sendo usado!")
                for key in cache_keys[:5]:  # Mostra as primeiras 5 chaves
                    print(f"  - {key.decode()[:50]}...")
            else:
                print("⚠️  Nenhuma chave de cache encontrada")
        else:
            print("❌ Redis não configurado")
            
    except Exception as e:
        print(f"❌ Erro ao verificar Redis: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Como verificar manualmente:")
    print("1. Acesse a aplicação web")
    print("2. Faça login e use o processador de relatórios")
    print("3. Cole o mesmo texto duas vezes")
    print("4. Compare os tempos de resposta")
    print("5. Verifique os logs da aplicação")
    print("6. Monitore o painel do Upstash")

if __name__ == "__main__":
    test_web_cache() 