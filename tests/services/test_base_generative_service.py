# tests/services/test_base_generative_service.py
import pytest
from unittest.mock import patch, MagicMock, ANY
from app.services.base_generative_service import BaseGenerativeService
import os
import logging
from app import cache

def test_base_service_init_success(app, caplog): # Adicionado 'app'
    """Testa inicialização bem-sucedida da BaseGenerativeService com caplog."""
    mock_model_instance = MagicMock()
    mock_model_instance.model_name = "gemini-test"

    with app.app_context(): # Adicionado contexto da aplicação
        with patch('os.getenv') as mock_getenv, \
             patch('google.generativeai.GenerativeModel', return_value=mock_model_instance) as mock_gen_model:

            def getenv_side_effect(key, default=None):
                if key == 'GOOGLE_API_KEY':
                    return "test_api_key"
                return os.environ.get(key, default)
            mock_getenv.side_effect = getenv_side_effect
            
            caplog.set_level(logging.INFO, logger="BaseGenerativeService")

            service = BaseGenerativeService(model_name="gemini-test")
            
            assert service.model is not None
            assert service._google_api_key == "test_api_key"
            mock_gen_model.assert_called_once()
            assert "Configuração da API Key do Google bem-sucedida" in caplog.text

def test_base_service_init_no_api_key(app): # Adicionado 'app'
    """Testa falha na inicialização se GOOGLE_API_KEY não estiver definida."""
    with app.app_context(): # Adicionado contexto da aplicação
        with patch('os.getenv', return_value=None):
            with pytest.raises(RuntimeError) as excinfo:
                BaseGenerativeService()
            assert "API Key do Google (GOOGLE_API_KEY) não configurada" in str(excinfo.value)


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_success(app, caplog): # Adicionado 'app'
    with app.app_context(): # Adicionado contexto da aplicação
        with patch('google.generativeai.GenerativeModel') as mock_gen_model_constructor:
            mock_model_instance = MagicMock()
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.text = "Resposta da IA"
            mock_response.parts = [mock_part]
            mock_response.prompt_feedback = None
            
            mock_model_instance.generate_content.return_value = mock_response
            mock_gen_model_constructor.return_value = mock_model_instance

            service = BaseGenerativeService()
            
            caplog.set_level(logging.INFO, logger=service.logger.name)
            result = service._call_generative_model("Meu prompt")
            
            assert result == "Resposta da IA"
            mock_model_instance.generate_content.assert_called_once_with("Meu prompt")
            assert "CACHE MISS. Enviando novo prompt" in caplog.text


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_is_cached(app):
    """Testa se a chamada para _call_generative_model é cacheada com sucesso."""
    with app.app_context():
        cache.clear()
        with patch('google.generativeai.GenerativeModel.generate_content') as mock_generate_content:
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.text = "Resposta da IA que deveria ser cacheada"
            mock_response.parts = [mock_part]
            mock_response.prompt_feedback = None
            mock_generate_content.return_value = mock_response

            service = BaseGenerativeService(model_name="gemini-test-cache")
            prompt = "Este é um prompt para teste de cache."

            # 1. Primeira chamada - deve ir para a API
            result1 = service._call_generative_model(prompt)
            mock_generate_content.assert_called_once()
            assert result1 == "Resposta da IA que deveria ser cacheada"

            # 2. Segunda chamada - deve vir do cache
            result2 = service._call_generative_model(prompt)
            mock_generate_content.assert_called_once()
            assert result2 == result1

            # 3. Limpa o cache e testa de novo
            cache.clear()
            result3 = service._call_generative_model(prompt)
            assert mock_generate_content.call_count == 2
            assert result3 == result1