"""
Utilitários para padronização das APIs REST.
"""
from flask import jsonify
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

def api_response(
    success: bool = True,
    data: Optional[Any] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    code: Optional[str] = None,
    status_code: int = 200
) -> tuple:
    """
    Padroniza as respostas da API.
    
    Args:
        success: Se a operação foi bem-sucedida
        data: Dados da resposta
        message: Mensagem de sucesso
        error: Mensagem de erro
        code: Código de erro
        status_code: Código HTTP
    
    Returns:
        Tuple (response, status_code)
    """
    response = {"success": success}
    
    if success:
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
    else:
        if error:
            response["error"] = error
        if code:
            response["code"] = code
    
    return jsonify(response), status_code

def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple:
    """Resposta de sucesso padronizada."""
    return api_response(
        success=True,
        data=data,
        message=message,
        status_code=status_code
    )

def error_response(
    error: str,
    code: Optional[str] = None,
    status_code: int = 400
) -> tuple:
    """Resposta de erro padronizada."""
    return api_response(
        success=False,
        error=error,
        code=code,
        status_code=status_code
    )

def pagination_response(
    data: list,
    page: int,
    pages: int,
    total: int,
    per_page: int,
    has_next: bool,
    has_prev: bool,
    message: Optional[str] = None
) -> tuple:
    """Resposta com paginação padronizada."""
    return success_response(
        data=data,
        message=message,
        status_code=200
    )[0].json, {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "pages": pages,
            "total": total,
            "per_page": per_page,
            "has_next": has_next,
            "has_prev": has_prev
        }
    }

def validate_required_fields(data: Dict, required_fields: list) -> Optional[str]:
    """
    Valida campos obrigatórios.
    
    Args:
        data: Dados recebidos
        required_fields: Lista de campos obrigatórios
    
    Returns:
        Mensagem de erro ou None se válido
    """
    if not data:
        return "Dados não fornecidos"
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        return f"Campos obrigatórios: {', '.join(missing_fields)}"
    
    return None

def log_api_error(endpoint: str, error: Exception, user_id: Optional[int] = None):
    """Log padronizado para erros da API."""
    logger.error(
        f"API Error - Endpoint: {endpoint}, User: {user_id}, Error: {str(error)}"
    )

def log_api_success(endpoint: str, user_id: Optional[int] = None, details: Optional[str] = None):
    """Log padronizado para sucessos da API."""
    log_msg = f"API Success - Endpoint: {endpoint}, User: {user_id}"
    if details:
        log_msg += f", Details: {details}"
    logger.info(log_msg) 