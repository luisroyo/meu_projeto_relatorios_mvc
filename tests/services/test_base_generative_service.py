# tests/services/test_base_generative_service.py
import pytest
from unittest.mock import patch, MagicMock, ANY
from app.services.base_generative_service import BaseGenerativeService
import os
import logging
from app import cache # <-- Importar a instância de cache

def test_base_service_init_success(caplog):
    """Testa inicialização bem-sucedida da BaseGenerativeService com caplog."""
    mock_model_instance = MagicMock()
    mock_model_instance.model_name = "gemini-test" # Simula o atributo que será usado no log

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
        mock_gen_model.assert_called_once_with(
            model_name="gemini-test",
            safety_settings=ANY,
            generation_config=ANY
        )
        
        expected_log_api_key = "Configuração da API Key do Google bem-sucedida para o serviço."
        expected_log_model_init = f"Modelo Gemini '{mock_model_instance.model_name}' inicializado com sucesso para BaseGenerativeService."

        assert expected_log_api_key in caplog.text
        assert expected_log_model_init in caplog.text

def test_base_service_init_no_api_key(caplog):
    """Testa falha na inicialização se GOOGLE_API_KEY não estiver definida."""
    with patch('os.getenv') as mock_getenv:
        def getenv_side_effect(key, default=None):
            if key == 'GOOGLE_API_KEY':
                return None
            return os.environ.get(key, default)
        mock_getenv.side_effect = getenv_side_effect

        caplog.set_level(logging.CRITICAL, logger="BaseGenerativeService")

        with pytest.raises(RuntimeError) as excinfo:
            BaseGenerativeService()
        
        assert "API Key do Google (GOOGLE_API_KEY) não configurada" in str(excinfo.value)
        
        expected_critical_log_message = "Falha na inicialização do serviço (configuração da API): API Key do Google (GOOGLE_API_KEY) não configurada nas variáveis de ambiente."
        assert expected_critical_log_message in caplog.text


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_success(caplog):
    with patch('google.generativeai.GenerativeModel') as mock_gen_model_constructor:
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Resposta da IA"
        mock_response.parts = [mock_part]
        mock_response.text = None 
        mock_response.prompt_feedback = None
        
        mock_model_instance.generate_content.return_value = mock_response
        mock_gen_model_constructor.return_value = mock_model_instance

        service = BaseGenerativeService()
        
        caplog.set_level(logging.INFO, logger=service.logger.name)
        result = service._call_generative_model("Meu prompt")
        
        assert result == "Resposta da IA"
        mock_model_instance.generate_content.assert_called_once_with("Meu prompt")
        assert "Enviando prompt para o modelo Gemini" in caplog.text
        assert "Resposta da IA processada com sucesso (via response.parts)." in caplog.text


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_blocked_response(caplog):
    with patch('google.generativeai.GenerativeModel') as mock_gen_model_constructor:
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.parts = [] 
        mock_response.text = None 

        mock_feedback = MagicMock()
        mock_feedback.block_reason = "SAFETY"
        mock_feedback.block_reason_message = "Conteúdo bloqueado por segurança"
        mock_response.prompt_feedback = mock_feedback
        
        mock_model_instance.generate_content.return_value = mock_response
        mock_gen_model_constructor.return_value = mock_model_instance

        service = BaseGenerativeService()
        
        caplog.set_level(logging.WARNING, logger=service.logger.name)
        with pytest.raises(ValueError) as excinfo:
            service._call_generative_model("Prompt que será bloqueado")
        
        assert "O conteúdo gerado foi bloqueado pela IA. Motivo: Conteúdo bloqueado por segurança" in str(excinfo.value)
        assert "Conteúdo bloqueado pela IA (sem partes/texto, mas com feedback). Motivo: Conteúdo bloqueado por segurança" in caplog.text

@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_empty_prompt(caplog):
    service = BaseGenerativeService() 
    
    caplog.set_level(logging.WARNING, logger=service.logger.name)
    with pytest.raises(ValueError) as excinfo:
        service._call_generative_model("   ")
    assert "Prompt final para a IA não pode ser vazio" in str(excinfo.value)
    assert "Prompt final está vazio ou não é uma string." in caplog.text

# --- NOVO TESTE DE CACHE ---
@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
def test_call_generative_model_is_cached(app):
    """Testa se a chamada para _call_generative_model é cacheada com sucesso."""
    with app.app_context():
        # Garante um estado limpo antes do teste
        cache.clear()

        # Mock da chamada real à API do Gemini, que é o que queremos evitar repetir
        with patch('google.generativeai.GenerativeModel.generate_content') as mock_generate_content:
            # Configura um retorno mockado consistente
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
            # Verifica que a API foi chamada exatamente uma vez
            mock_generate_content.assert_called_once()
            assert result1 == "Resposta da IA que deveria ser cacheada"

            # 2. Segunda chamada com o MESMO prompt - deve vir do cache
            result2 = service._call_generative_model(prompt)
            # A contagem de chamadas à API deve permanecer em 1
            mock_generate_content.assert_called_once()
            assert result2 == result1 # O resultado deve ser o mesmo

            # 3. Limpa o cache
            cache.clear()

            # 4. Terceira chamada - deve ir para a API novamente, pois o cache foi limpo
            result3 = service._call_generative_model(prompt)
            # A contagem de chamadas agora deve ser 2
            assert mock_generate_content.call_count == 2
            assert result3 == result1