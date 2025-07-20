#!/usr/bin/env python3
"""
Script para gerar tráfego contínuo no Redis
Execute: python generate_redis_traffic.py
"""

import os
import time
import redis
import random
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def generate_continuous_traffic():
    """Gera tráfego contínuo no Redis."""
    print("🚀 Gerando Tráfego Contínuo no Redis")
    print("=" * 50)
    
    # Verifica variáveis de ambiente
    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
    
    if not redis_url:
        print("❌ Nenhuma URL do Redis configurada")
        return
    
    print(f"🔗 Conectando com: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
    
    try:
        # Conecta com Redis
        r = redis.from_url(redis_url)
        
        # Testa conexão
        if not r.ping():
            print("❌ Falha na conexão com Redis")
            return
        
        print("✅ Conectado com Redis")
        print("🔄 Iniciando geração de tráfego...")
        print("💡 Pressione Ctrl+C para parar")
        
        operation_count = 0
        start_time = time.time()
        
        while True:
            try:
                # Gera operações aleatórias
                operation_type = random.choice(['set', 'get', 'delete', 'ping'])
                
                if operation_type == 'set':
                    key = f"traffic_key_{random.randint(1, 1000)}"
                    value = f"traffic_value_{int(time.time())}"
                    r.set(key, value, ex=300)  # Expira em 5 minutos
                    print(f"  📝 SET: {key} = {value[:20]}...")
                
                elif operation_type == 'get':
                    key = f"traffic_key_{random.randint(1, 1000)}"
                    value = r.get(key)
                    if value:
                        print(f"  📖 GET: {key} = {value.decode()[:20]}...")
                    else:
                        print(f"  📖 GET: {key} = (não encontrado)")
                
                elif operation_type == 'delete':
                    key = f"traffic_key_{random.randint(1, 1000)}"
                    deleted = r.delete(key)
                    print(f"  🗑️  DELETE: {key} = {deleted} chaves removidas")
                
                elif operation_type == 'ping':
                    pong = r.ping()
                    print(f"  🏓 PING: {'pong' if pong else 'falha'}")
                
                operation_count += 1
                
                # Mostra estatísticas a cada 10 operações
                if operation_count % 10 == 0:
                    elapsed = time.time() - start_time
                    ops_per_sec = operation_count / elapsed
                    print(f"\n📊 Estatísticas: {operation_count} operações em {elapsed:.1f}s ({ops_per_sec:.1f} ops/s)")
                    
                    # Mostra algumas estatísticas do Redis
                    try:
                        info = r.info()
                        total_commands = info.get('total_commands_processed', 0)
                        print(f"  Redis total commands: {total_commands}")
                    except:
                        pass
                
                # Pausa entre operações
                time.sleep(random.uniform(0.5, 2.0))
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Parando geração de tráfego...")
                break
            except Exception as e:
                print(f"⚠️  Erro na operação: {e}")
                time.sleep(1)
                continue
        
        # Estatísticas finais
        elapsed = time.time() - start_time
        ops_per_sec = operation_count / elapsed
        print(f"\n📊 Estatísticas Finais:")
        print(f"  Total de operações: {operation_count}")
        print(f"  Tempo total: {elapsed:.1f} segundos")
        print(f"  Operações por segundo: {ops_per_sec:.1f}")
        print(f"  Tráfego gerado com sucesso! 🎉")
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Redis: {e}")

if __name__ == "__main__":
    generate_continuous_traffic() 