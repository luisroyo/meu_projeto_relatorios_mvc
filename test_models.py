#!/usr/bin/env python3
"""
Script para listar modelos disponíveis na API Gemini
Execute: python test_models.py
"""

import os
from google import genai
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

def list_available_models():
    """Lista todos os modelos disponíveis na conta"""
    
    # Tenta usar as API keys configuradas
    api_key = os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY_2")
    
    if not api_key:
        print("ERRO: GOOGLE_API_KEY_1 ou GOOGLE_API_KEY_2 não encontrada!")
        print("Configure uma das variáveis de ambiente:")
        print("export GOOGLE_API_KEY_1='sua_api_key_aqui'")
        print("ou")
        print("export GOOGLE_API_KEY_2='sua_api_key_aqui'")
        return
    
    try:
        print("Usando API Key configurada...")
        print(f"API Key (primeiros 10 chars): {api_key[:10]}...")
        
        # Cria cliente
        client = genai.Client(api_key=api_key)
        print("Cliente criado com sucesso!")
        
        # Lista modelos
        print("\nListando modelos disponíveis...")
        print("=" * 50)
        
        models = client.models.list()
        model_count = 0
        
        for model in models:
            model_count += 1
            print(f"{model_count:2d}. {model.name}")
            
            # Tenta obter mais informações se disponível
            if hasattr(model, 'display_name'):
                print(f"     Display Name: {model.display_name}")
            if hasattr(model, 'description'):
                print(f"     Description: {model.description}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"     Methods: {model.supported_generation_methods}")
            print()
        
        print("=" * 50)
        print(f"Total de modelos encontrados: {model_count}")
        
        # Testa alguns modelos específicos
        print("\nTestando modelos específicos...")
        test_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash", 
            "gemini-2.0-flash",
            "gemini-2.0-pro"
        ]
        
        for model_name in test_models:
            try:
                print(f"Testando {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents="Diga apenas 'OK' se funcionar."
                )
                print(f"SUCESSO {model_name}: FUNCIONA! Resposta: {response.text[:50]}...")
            except Exception as e:
                print(f"FALHOU {model_name}: FALHOU - {str(e)[:100]}...")
        
    except Exception as e:
        print(f"ERRO GERAL: {e}")
        import traceback
        print(f"\nTraceback completo:\n{traceback.format_exc()}")

if __name__ == "__main__":
    print("TESTE DE MODELOS GEMINI")
    print("=" * 50)
    list_available_models()
