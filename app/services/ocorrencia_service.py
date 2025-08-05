# app/services/ocorrencia_service.py
import logging
from datetime import datetime

import pytz
from flask import current_app

logger = logging.getLogger(__name__)


def parse_date_string(date_str):
    """
    Tenta fazer o parse de uma string de data em diferentes formatos.
    
    :param date_str: String da data
    :return: datetime object ou None se falhar
    """
    if not date_str:
        return None
        
    # Lista de formatos possíveis
    date_formats = [
        '%Y-%m-%d',  # 2025-08-04 (ISO)
        '%d/%m/%Y',  # 04/08/2025 (Brasileiro)
        '%d-%m-%Y',  # 04-08-2025 (Alternativo)
        '%Y/%m/%d',  # 2025/08/04 (Alternativo)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Formato de data não reconhecido: '{date_str}'")
    return None


def apply_ocorrencia_filters(query, filters):
    """
    Aplica filtros a uma query de Ocorrência de forma centralizada.

    :param query: O objeto de query SQLAlchemy inicial.
    :param filters: Um dicionário contendo os filtros a serem aplicados.
    :return: O objeto de query com os filtros aplicados.
    """
    from app.models import \
        Ocorrencia  # Importação tardia para evitar importação circular

    # Filtros de ID e Status
    if filters.get("status"):
        query = query.filter(Ocorrencia.status == filters["status"])
    if filters.get("condominio_id"):
        query = query.filter(Ocorrencia.condominio_id == filters["condominio_id"])
    if filters.get("supervisor_id"):
        query = query.filter(Ocorrencia.supervisor_id == filters["supervisor_id"])
    if filters.get("tipo_id"):
        query = query.filter(Ocorrencia.ocorrencia_tipo_id == filters["tipo_id"])

    # Filtros de Data (com tratamento de timezone e múltiplos formatos)
    data_inicio_str = filters.get("data_inicio_str") or filters.get("data_inicio")
    if data_inicio_str:
        start_date_naive = parse_date_string(data_inicio_str)
        if start_date_naive:
            try:
                # Obtém o timezone da configuração da aplicação para flexibilidade
                default_tz_str = current_app.config.get(
                    "DEFAULT_TIMEZONE", "America/Sao_Paulo"
                )
                local_tz = pytz.timezone(default_tz_str)

                # Converte a data de início para um datetime ciente do fuso horário e em UTC
                start_date_aware = local_tz.localize(start_date_naive)
                start_date_utc = start_date_aware.astimezone(pytz.utc)

                query = query.filter(Ocorrencia.data_hora_ocorrencia >= start_date_utc)
                logger.info(f"Filtro de data de início aplicado: {data_inicio_str} -> {start_date_utc}")
            except Exception as e:
                logger.warning(
                    f"Erro ao processar data de início '{data_inicio_str}': {e}"
                )
        else:
            logger.warning(f"Formato de data de início inválido: '{data_inicio_str}'")

    data_fim_str = filters.get("data_fim_str") or filters.get("data_fim")
    if data_fim_str:
        end_date_naive = parse_date_string(data_fim_str)
        if end_date_naive:
            try:
                default_tz_str = current_app.config.get(
                    "DEFAULT_TIMEZONE", "America/Sao_Paulo"
                )
                local_tz = pytz.timezone(default_tz_str)

                # Para a data final, pegamos o final do dia (23:59:59)
                end_date_naive = end_date_naive.replace(
                    hour=23, minute=59, second=59
                )
                end_date_aware = local_tz.localize(end_date_naive)
                end_date_utc = end_date_aware.astimezone(pytz.utc)

                query = query.filter(Ocorrencia.data_hora_ocorrencia <= end_date_utc)
                logger.info(f"Filtro de data de fim aplicado: {data_fim_str} -> {end_date_utc}")
            except Exception as e:
                logger.warning(
                    f"Erro ao processar data de fim '{data_fim_str}': {e}"
                )
        else:
            logger.warning(f"Formato de data de fim inválido: '{data_fim_str}'")

    if filters.get("texto_relatorio"):
        query = query.filter(Ocorrencia.relatorio_final.ilike(f"%{filters['texto_relatorio']}%"))

    return query


def contar_ocorrencias_pendentes():
    """
    Conta o número de ocorrências com status 'Pendente' que precisam ser revisadas.
    
    :return: Número de ocorrências pendentes
    """
    from app.models import Ocorrencia  # Importação tardia para evitar importação circular
    
    return Ocorrencia.query.filter_by(status="Pendente").count()


def obter_ocorrencias_pendentes(limit=10):
    """
    Obtém as ocorrências pendentes mais recentes.
    
    :param limit: Número máximo de ocorrências a retornar
    :return: Lista de ocorrências pendentes
    """
    from app.models import Ocorrencia  # Importação tardia para evitar importação circular
    
    return Ocorrencia.query.filter_by(status="Pendente").order_by(
        Ocorrencia.data_hora_ocorrencia.desc()
    ).limit(limit).all()
