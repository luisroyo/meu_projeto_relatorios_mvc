# app/services/ocorrencia_service.py
import logging
from datetime import datetime
import pytz
from flask import current_app

logger = logging.getLogger(__name__)

def apply_ocorrencia_filters(query, filters):
    """
    Aplica filtros a uma query de Ocorrência de forma centralizada.
    
    :param query: O objeto de query SQLAlchemy inicial.
    :param filters: Um dicionário contendo os filtros a serem aplicados.
    :return: O objeto de query com os filtros aplicados.
    """
    from app.models import Ocorrencia # Importação tardia para evitar importação circular

    # Filtros de ID e Status
    if filters.get('status'):
        query = query.filter(Ocorrencia.status == filters['status'])
    if filters.get('condominio_id'):
        query = query.filter(Ocorrencia.condominio_id == filters['condominio_id'])
    if filters.get('supervisor_id'):
        query = query.filter(Ocorrencia.supervisor_id == filters['supervisor_id'])
    if filters.get('tipo_id'):
        query = query.filter(Ocorrencia.ocorrencia_tipo_id == filters['tipo_id'])

    # Filtros de Data (com tratamento de timezone)
    data_inicio_str = filters.get('data_inicio')
    if data_inicio_str:
        try:
            # Obtém o timezone da configuração da aplicação para flexibilidade
            default_tz_str = current_app.config.get('DEFAULT_TIMEZONE', 'America/Sao_Paulo')
            local_tz = pytz.timezone(default_tz_str)
            
            # Converte a data de início para um datetime ciente do fuso horário e em UTC
            start_date_naive = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            start_date_aware = local_tz.localize(start_date_naive)
            start_date_utc = start_date_aware.astimezone(pytz.utc)
            
            query = query.filter(Ocorrencia.data_hora_ocorrencia >= start_date_utc)
        except (ValueError, TypeError) as e:
            logger.warning(f"Formato de data de início inválido fornecido: '{data_inicio_str}'. Erro: {e}")
            # Opcional: pode-se adicionar um flash de erro aqui se o contexto permitir

    data_fim_str = filters.get('data_fim')
    if data_fim_str:
        try:
            default_tz_str = current_app.config.get('DEFAULT_TIMEZONE', 'America/Sao_Paulo')
            local_tz = pytz.timezone(default_tz_str)

            # Para a data final, pegamos o final do dia (23:59:59)
            end_date_naive = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            end_date_aware = local_tz.localize(end_date_naive)
            end_date_utc = end_date_aware.astimezone(pytz.utc)
            
            query = query.filter(Ocorrencia.data_hora_ocorrencia <= end_date_utc)
        except (ValueError, TypeError) as e:
            logger.warning(f"Formato de data de fim inválido fornecido: '{data_fim_str}'. Erro: {e}")

    return query