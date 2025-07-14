# app/services/dashboard/helpers/filters.py
from app.models import Ronda

def apply_ronda_filters(query, filters: dict, date_start_range, date_end_range):
    """
    Aplica filtros de data, turno, supervisor e condomínio a uma query de Ronda.
    
    Args:
        query: O objeto da query SQLAlchemy a ser filtrado.
        filters: Um dicionário contendo os filtros a serem aplicados.
        date_start_range: A data de início para o filtro de período.
        date_end_range: A data de fim para o filtro de período.

    Returns:
        O objeto da query com os filtros aplicados.
    """
    # Filtro de período obrigatório
    query = query.filter(Ronda.data_plantao_ronda.between(date_start_range, date_end_range))
    
    # Filtros opcionais
    turno_filter = filters.get('turno')
    if turno_filter:
        query = query.filter(Ronda.turno_ronda == turno_filter)

    supervisor_id_filter = filters.get('supervisor_id')
    if supervisor_id_filter:
        query = query.filter(Ronda.supervisor_id == supervisor_id_filter)

    condominio_id_filter = filters.get('condominio_id')
    if condominio_id_filter:
        query = query.filter(Ronda.condominio_id == condominio_id_filter)
        
    return query