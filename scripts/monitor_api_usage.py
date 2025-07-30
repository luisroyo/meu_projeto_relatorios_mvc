#!/usr/bin/env python3
"""
Script para monitorar o uso das APIs do Gemini
Execute: python scripts/monitor_api_usage.py
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def check_api_keys():
    """Verifica se as API keys estão configuradas."""
    print("🔍 Verificando Configuração das API Keys")
    print("=" * 50)
    
    api_key_1 = os.getenv("GOOGLE_API_KEY_1")
    api_key_2 = os.getenv("GOOGLE_API_KEY_2")
    
    print(f"GOOGLE_API_KEY_1: {'✅ Configurada' if api_key_1 else '❌ Não configurada'}")
    print(f"GOOGLE_API_KEY_2: {'✅ Configurada' if api_key_2 else '❌ Não configurada'}")
    
    if not api_key_1 and not api_key_2:
        print("\n⚠️  Nenhuma API key configurada!")
        print("Configure no arquivo .env:")
        print("GOOGLE_API_KEY_1=sua-chave-principal")
        print("GOOGLE_API_KEY_2=sua-chave-backup")
        return False
    
    return True

def check_cache_config():
    """Verifica a configuração do cache."""
    print("\n💾 Verificando Configuração do Cache")
    print("=" * 50)
    
    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
    
    if redis_url:
        print(f"✅ Redis configurado: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
        print("💡 Cache persistente ativo - respostas serão salvas")
    else:
        print("⚠️  Redis não configurado")
        print("💡 Usando SimpleCache (memória) - cache será perdido ao reiniciar")
        print("\nPara configurar Redis, adicione ao .env:")
        print("REDIS_URL=redis://usuario:senha@host:porta/0")
    
    return redis_url is not None

def show_usage_tips():
    """Mostra dicas para otimizar o uso das APIs."""
    print("\n💡 Dicas para Otimizar Uso das APIs")
    print("=" * 50)
    
    print("1. 🔄 Use Cache Efetivamente:")
    print("   - Configure Redis para cache persistente")
    print("   - O sistema já tem cache de 1 hora configurado")
    
    print("\n2. 📊 Monitore o Uso:")
    print("   - Acesse: https://aistudio.google.com/")
    print("   - Configure alertas no Google Cloud Console")
    
    print("\n3. 🔑 Use Múltiplas API Keys:")
    print("   - Configure GOOGLE_API_KEY_1 e GOOGLE_API_KEY_2")
    print("   - O sistema fará fallback automático")
    
    print("\n4. ⏰ Implemente Rate Limiting:")
    print("   - O sistema já tem rate limiting configurado")
    print("   - Limite: 45 requisições/dia por API key")
    
    print("\n5. 🎯 Otimize Prompts:")
    print("   - Use prompts específicos e concisos")
    print("   - Evite requisições desnecessárias")
    
    print("\n6. 📈 Considere Upgrade:")
    print("   - Plano gratuito: 50 req/dia")
    print("   - Planos pagos: até 15 req/min")

def show_current_limits():
    """Mostra os limites atuais do plano gratuito."""
    print("\n📋 Limites do Plano Gratuito")
    print("=" * 50)
    
    print("🔢 Requisições por dia: 50")
    print("⚡ Requisições por minuto: 15")
    print("📝 Tokens por requisição: 8192")
    print("🕐 Modelo: gemini-1.5-flash-latest")
    
    print("\n⚠️  Recomendações:")
    print("- Configure rate limiting para 45 req/dia (margem de segurança)")
    print("- Use cache para evitar requisições repetidas")
    print("- Monitore o uso regularmente")

def main():
    """Função principal."""
    print("🚀 Monitor de Uso das APIs Gemini")
    print("=" * 60)
    
    # Verifica configuração
    if not check_api_keys():
        return
    
    # Verifica cache
    cache_configured = check_cache_config()
    
    # Mostra limites
    show_current_limits()
    
    # Mostra dicas
    show_usage_tips()
    
    print("\n" + "=" * 60)
    print("✅ Verificação concluída!")
    
    if not cache_configured:
        print("⚠️  Recomenda-se configurar Redis para melhor performance")
    
    print("\n📞 Para suporte:")
    print("- Google AI Studio: https://aistudio.google.com/")
    print("- Documentação: https://ai.google.dev/gemini-api/docs/rate-limits")

if __name__ == "__main__":
    main() 