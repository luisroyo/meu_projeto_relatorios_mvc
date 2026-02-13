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
    Funciona tanto com a tabela Ocorrencia quanto com a view VWOcorrenciasDetalhadas.

    :param query: O objeto de query SQLAlchemy inicial.
    :param filters: Um dicionário contendo os filtros a serem aplicados.
    :return: O objeto de query com os filtros aplicados.
    """
    from app.models import Ocorrencia  # Importação tardia para evitar importação circular
    from app.models.vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas

    # Detecta se estamos usando a view ou a tabela
    # Para queries com func.count() ou outras funções, precisamos verificar de forma diferente
    logger.info("🔍 DEBUG: apply_ocorrencia_filters - Detectando view vs tabela")
    logger.info(f"   Filtros recebidos: {filters}")
    
    is_view = False
    
    # Verificar se a query tem a view como entidade principal
    if hasattr(query, 'column_descriptions') and query.column_descriptions:
        logger.info(f"   Column descriptions: {query.column_descriptions}")
        # Verificar se a primeira coluna é da view
        first_col = query.column_descriptions[0]
        logger.info(f"   Primeira coluna: {first_col}")
        
        if 'entity' in first_col and first_col['entity']:
            entity = first_col['entity']
            logger.info(f"   Entity encontrada: {entity}")
            logger.info(f"   Entity type: {type(entity)}")
            
            if hasattr(entity, '__tablename__'):
                tablename = entity.__tablename__
                is_view = tablename == 'vw_ocorrencias_detalhadas'
                logger.info(f"   Tablename: {tablename}, É view? {is_view}")
            elif hasattr(entity, '__name__'):
                # Para casos onde entity é a classe da view
                entity_name = str(entity)
                is_view = 'VWOcorrenciasDetalhadas' in entity_name
                logger.info(f"   Entity name: {entity_name}, É view? {is_view}")
    
    # Se não conseguiu detectar, verificar se a query SQL contém a view
    if not is_view:
        query_str = str(query)
        is_view = 'vw_ocorrencias_detalhadas' in query_str.lower()
        logger.info(f"   Fallback - Query SQL contém view? {is_view}")
        logger.info(f"   Query SQL: {query_str}")
    
    logger.info(f"   RESULTADO FINAL - É view? {is_view}")
    
    if is_view:
        # Usando a view
        if filters.get("status"):
            query = query.filter(VWOcorrenciasDetalhadas.status == filters["status"])
        if filters.get("condominio_id"):
            # Na view, condominio é uma string, então filtramos por nome
            from app.models import Condominio
            condominio = Condominio.query.get(filters["condominio_id"])
            if condominio:
                query = query.filter(VWOcorrenciasDetalhadas.condominio == condominio.nome)
        if filters.get("supervisor_id"):
            # Na view, supervisor é uma string, então filtramos por username
            from app.models import User
            supervisor = User.query.get(filters["supervisor_id"])
            if supervisor:
                query = query.filter(VWOcorrenciasDetalhadas.supervisor == supervisor.username)
        if filters.get("tipo_id"):
            # Na view, tipo é uma string, então filtramos por nome
            from app.models import OcorrenciaTipo
            tipo = OcorrenciaTipo.query.get(filters["tipo_id"])
            if tipo:
                query = query.filter(VWOcorrenciasDetalhadas.tipo == tipo.nome)
    else:
        # Usando a tabela original
        if filters.get("status"):
            query = query.filter(Ocorrencia.status == filters["status"])
        if filters.get("condominio_id"):
            query = query.filter(Ocorrencia.condominio_id == filters["condominio_id"])
        if filters.get("supervisor_id"):
            query = query.filter(Ocorrencia.supervisor_id == filters["supervisor_id"])
        if filters.get("tipo_id"):
            query = query.filter(Ocorrencia.ocorrencia_tipo_id == filters["tipo_id"])

    # Filtros de Data (com tratamento de timezone e múltiplos formatos)
    logger.info("🔍 DEBUG: Aplicando filtros de data")
    
    data_inicio_str = filters.get("data_inicio_str") or filters.get("data_inicio")
    if data_inicio_str:
        logger.info(f"   Data início recebida: {data_inicio_str}")
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

                logger.info(f"   Data início processada: {start_date_naive} -> {start_date_utc}")
                logger.info(f"   Aplicando filtro de data início (is_view={is_view})")

                if is_view:
                    query = query.filter(VWOcorrenciasDetalhadas.data_hora_ocorrencia >= start_date_utc)
                    logger.info("   ✅ Filtro aplicado na VIEW")
                else:
                    query = query.filter(Ocorrencia.data_hora_ocorrencia >= start_date_utc)
                    logger.info("   ✅ Filtro aplicado na TABELA")
                    
                logger.info(f"Filtro de data de início aplicado: {data_inicio_str} -> {start_date_utc}")
            except Exception as e:
                logger.warning(
                    f"Erro ao processar data de início '{data_inicio_str}': {e}"
                )
        else:
            logger.warning(f"Formato de data de início inválido: '{data_inicio_str}'")

    data_fim_str = filters.get("data_fim_str") or filters.get("data_fim")
    if data_fim_str:
        logger.info(f"   Data fim recebida: {data_fim_str}")
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

                logger.info(f"   Data fim processada: {end_date_naive} -> {end_date_utc}")
                logger.info(f"   Aplicando filtro de data fim (is_view={is_view})")

                if is_view:
                    query = query.filter(VWOcorrenciasDetalhadas.data_hora_ocorrencia <= end_date_utc)
                    logger.info("   ✅ Filtro aplicado na VIEW")
                else:
                    query = query.filter(Ocorrencia.data_hora_ocorrencia <= end_date_utc)
                    logger.info("   ✅ Filtro aplicado na TABELA")
                    
                logger.info(f"Filtro de data de fim aplicado: {data_fim_str} -> {end_date_utc}")
            except Exception as e:
                logger.warning(
                    f"Erro ao processar data de fim '{data_fim_str}': {e}"
                )
        else:
            logger.warning(f"Formato de data de fim inválido: '{data_fim_str}'")

    if filters.get("texto_relatorio"):
        # Agora a view tem o campo relatorio_final, então podemos filtrar
        if is_view:
            query = query.filter(VWOcorrenciasDetalhadas.relatorio_final.ilike(f"%{filters['texto_relatorio']}%"))
        else:
            query = query.filter(Ocorrencia.relatorio_final.ilike(f"%{filters['texto_relatorio']}%"))

    logger.info("🔍 DEBUG: apply_ocorrencia_filters - Finalizando")
    logger.info(f"   Query final: {query}")
    logger.info(f"   SQL final: {str(query)}")
    
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
