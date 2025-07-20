#!/usr/bin/env python3
"""
Script para testar o funcionamento do cache
Execute: python test_cache.py
"""

import os
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_cache_functionality():
    """Testa o funcionamento do cache."""
    print("🧪 Testando Funcionamento do Cache")
    print("=" * 50)
    
    try:
        # Importa a aplicação
        from app import create_app, cache
        from app.services.patrimonial_report_service import PatrimonialReportService
        
        # Cria a aplicação
        app = create_app()
        
        with app.app_context():
            print("✅ Aplicação Flask criada com sucesso")
            
            # Verifica configuração do cache
            cache_type = app.config.get('CACHE_TYPE', 'Não configurado')
            print(f"📋 Tipo de Cache: {cache_type}")
            
            if cache_type == 'RedisCache':
                redis_url = app.config.get('CACHE_REDIS_URL', 'Não configurado')
                print(f"🔗 URL do Redis: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
            else:
                print("💾 Usando cache em memória (SimpleCache)")
            
            # Testa operações básicas do cache
            print("\n🔍 Testando operações básicas do cache...")
            
            # Teste 1: Set/Get
            test_key = "test_cache_key"
            test_value = "test_cache_value"
            
            cache.set(test_key, test_value, timeout=60)
            print(f"✅ Cache.set() executado para chave: {test_key}")
            
            retrieved_value = cache.get(test_key)
            if retrieved_value == test_value:
                print(f"✅ Cache.get() funcionando - valor recuperado: {retrieved_value}")
            else:
                print(f"❌ Cache.get() falhou - esperado: {test_value}, obtido: {retrieved_value}")
            
            # Teste 2: Verificar se existe
            exists = cache.get(test_key) is not None
            print(f"✅ Verificação de existência: {exists}")
            
            # Teste 3: Delete
            cache.delete(test_key)
            print(f"✅ Cache.delete() executado")
            
            # Verifica se foi deletado
            deleted_value = cache.get(test_key)
            if deleted_value is None:
                print(f"✅ Cache.delete() funcionando - valor removido")
            else:
                print(f"❌ Cache.delete() falhou - valor ainda existe: {deleted_value}")
            
            # Teste 4: Teste com serviço de IA
            print("\n🤖 Testando cache com serviço de IA...")
            
            service = PatrimonialReportService()
            test_prompt = "Este é um teste de cache para verificar se está funcionando."
            
            print(f"📝 Prompt de teste: {test_prompt}")
            
            # Primeira chamada (deve ser CACHE MISS)
            print("\n🔄 Primeira chamada (deve ser CACHE MISS):")
            start_time = time.time()
            result1 = service.gerar_relatorio_seguranca(test_prompt)
            time1 = time.time() - start_time
            print(f"⏱️  Tempo da primeira chamada: {time1:.2f} segundos")
            print(f"📊 Tamanho da resposta: {len(result1)} caracteres")
            
            # Segunda chamada (deve ser CACHE HIT)
            print("\n🔄 Segunda chamada (deve ser CACHE HIT):")
            start_time = time.time()
            result2 = service.gerar_relatorio_seguranca(test_prompt)
            time2 = time.time() - start_time
            print(f"⏱️  Tempo da segunda chamada: {time2:.2f} segundos")
            print(f"📊 Tamanho da resposta: {len(result2)} caracteres")
            
            # Compara resultados
            if result1 == result2:
                print("✅ Respostas idênticas - cache funcionando!")
            else:
                print("❌ Respostas diferentes - cache não funcionou")
            
            # Compara tempos
            if time2 < time1:
                print(f"🚀 Segunda chamada foi {time1/time2:.1f}x mais rápida!")
            else:
                print("⚠️  Segunda chamada não foi mais rápida")
            
            print("\n" + "=" * 50)
            print("🎉 Teste de cache concluído!")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

def check_cache_stats():
    """Verifica estatísticas do cache (se disponível)."""
    print("\n📊 Verificando estatísticas do cache...")
    
    try:
        from app import create_app, cache
        
        app = create_app()
        
        with app.app_context():
            # Tenta obter informações do cache
            cache_type = app.config.get('CACHE_TYPE', 'Não configurado')
            print(f"Tipo de Cache: {cache_type}")
            
            if cache_type == 'RedisCache':
                # Para Redis, podemos tentar algumas operações de debug
                print("🔍 Redis detectado - verificando conexão...")
                
                # Testa ping
                try:
                    import redis
                    redis_url = app.config.get('CACHE_REDIS_URL')
                    if redis_url:
                        r = redis.from_url(redis_url)
                        pong = r.ping()
                        print(f"Ping Redis: {'✅ Sucesso' if pong else '❌ Falha'}")
                        
                        # Tenta obter algumas estatísticas básicas
                        info = r.info()
                        print(f"Versão Redis: {info.get('redis_version', 'N/A')}")
                        print(f"Uptime: {info.get('uptime_in_seconds', 'N/A')} segundos")
                        print(f"Total de comandos: {info.get('total_commands_processed', 'N/A')}")
                        
                except Exception as e:
                    print(f"⚠️  Erro ao obter estatísticas do Redis: {e}")
            else:
                print("💾 SimpleCache - estatísticas limitadas")
                
    except Exception as e:
        print(f"❌ Erro ao verificar estatísticas: {e}")

if __name__ == "__main__":
    test_cache_functionality()
    check_cache_stats()
    
    print("\n💡 Dicas para monitorar o cache:")
    print("- Verifique os logs da aplicação para mensagens de cache")
    print("- Use o painel do Upstash para ver estatísticas do Redis")
    print("- Execute este script periodicamente para verificar funcionamento")
    print("- Monitore os tempos de resposta das consultas") 