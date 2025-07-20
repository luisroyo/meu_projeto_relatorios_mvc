#!/usr/bin/env python3
"""
Script simples para testar o cache
Execute: python simple_cache_test.py
"""

import os
import time
import redis
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_redis_directly():
    """Testa o Redis diretamente."""
    print("🔍 Testando Redis Diretamente")
    print("=" * 40)
    
    # Verifica variáveis de ambiente
    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
    
    if not redis_url:
        print("❌ Nenhuma URL do Redis configurada")
        return
    
    print(f"🔗 Conectando com: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
    
    try:
        # Conecta com Redis
        r = redis.from_url(redis_url)
        
        # Testa ping
        pong = r.ping()
        print(f"Ping: {'✅ Sucesso' if pong else '❌ Falha'}")
        
        # Testa operações básicas
        test_key = "test_cache_monitoring"
        test_value = "test_value_" + str(int(time.time()))
        
        # Set
        r.set(test_key, test_value, ex=300)  # Expira em 5 minutos
        print(f"✅ Set executado: {test_key} = {test_value}")
        
        # Get
        retrieved = r.get(test_key)
        print(f"✅ Get executado: {test_key} = {retrieved}")
        
        # Verifica se é igual
        if retrieved and retrieved.decode() == test_value:
            print("✅ Set/Get funcionando corretamente")
        else:
            print("❌ Set/Get falhou")
        
        # Testa múltiplas operações para gerar tráfego
        print("\n🔄 Gerando tráfego no Redis...")
        for i in range(10):
            key = f"test_key_{i}"
            value = f"test_value_{i}_{int(time.time())}"
            r.set(key, value, ex=60)
            retrieved = r.get(key)
            print(f"  Operação {i+1}: {'✅' if retrieved else '❌'}")
            time.sleep(0.1)  # Pequena pausa
        
        # Limpa as chaves de teste
        for i in range(10):
            r.delete(f"test_key_{i}")
        r.delete(test_key)
        print("🧹 Chaves de teste removidas")
        
        # Mostra estatísticas
        info = r.info()
        print(f"\n📊 Estatísticas do Redis:")
        print(f"  Versão: {info.get('redis_version', 'N/A')}")
        print(f"  Uptime: {info.get('uptime_in_seconds', 'N/A')} segundos")
        print(f"  Total de comandos: {info.get('total_commands_processed', 'N/A')}")
        print(f"  Comandos por segundo: {info.get('instantaneous_ops_per_sec', 'N/A')}")
        print(f"  Clientes conectados: {info.get('connected_clients', 'N/A')}")
        
        print("\n🎉 Redis está funcionando e gerando tráfego!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Redis: {e}")

def test_cache_pattern():
    """Testa o padrão de cache usado na aplicação."""
    print("\n🧪 Testando Padrão de Cache da Aplicação")
    print("=" * 40)
    
    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
    
    if not redis_url:
        print("❌ Nenhuma URL do Redis configurada")
        return
    
    try:
        r = redis.from_url(redis_url)
        
        # Simula o padrão de cache usado na aplicação
        import hashlib
        
        test_prompt = "Este é um teste de cache para verificar se está funcionando."
        cache_key = hashlib.sha256(test_prompt.encode("utf-8")).hexdigest()
        
        print(f"📝 Prompt: {test_prompt}")
        print(f"🔑 Chave de cache: {cache_key[:16]}...")
        
        # Simula primeira chamada (CACHE MISS)
        print("\n🔄 Simulando primeira chamada (CACHE MISS):")
        start_time = time.time()
        
        # Simula processamento da IA
        time.sleep(2)  # Simula tempo de processamento
        ai_response = f"Resposta simulada da IA para: {test_prompt}"
        
        # Salva no cache
        r.set(cache_key, ai_response, ex=3600)  # 1 hora
        
        time1 = time.time() - start_time
        print(f"⏱️  Tempo da primeira chamada: {time1:.2f} segundos")
        print(f"💾 Resposta salva no cache")
        
        # Simula segunda chamada (CACHE HIT)
        print("\n🔄 Simulando segunda chamada (CACHE HIT):")
        start_time = time.time()
        
        # Recupera do cache
        cached_response = r.get(cache_key)
        
        time2 = time.time() - start_time
        print(f"⏱️  Tempo da segunda chamada: {time2:.2f} segundos")
        
        if cached_response:
            cached_text = cached_response.decode()
            print(f"🎯 CACHE HIT - Resposta recuperada: {cached_text[:50]}...")
            print(f"🚀 Segunda chamada foi {time1/time2:.1f}x mais rápida!")
        else:
            print("❌ CACHE MISS - Resposta não encontrada no cache")
        
        # Limpa o teste
        r.delete(cache_key)
        print("🧹 Chave de teste removida")
        
    except Exception as e:
        print(f"❌ Erro no teste de padrão: {e}")

if __name__ == "__main__":
    test_redis_directly()
    test_cache_pattern()
    
    print("\n" + "=" * 40)
    print("💡 Como monitorar o uso do Redis:")
    print("1. Execute este script periodicamente")
    print("2. Verifique o painel do Upstash")
    print("3. Monitore os logs da aplicação")
    print("4. Observe os tempos de resposta")
    print("5. Use o comando: python simple_cache_test.py") 