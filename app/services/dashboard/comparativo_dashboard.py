# app/services/dashboard/comparativo_dashboard.py
from sqlalchemy import func
from datetime import datetime

from app import db
from app.models import Ronda, Ocorrencia

def _get_monthly_aggregation(model, date_column, year):
    """
    Função genérica para agregar dados de um modelo por mês.
    Usa TO_CHAR para compatibilidade com PostgreSQL.
    """
    # [CORREÇÃO] Substituído func.strftime por func.to_char
    return db.session.query(
        func.to_char(date_column, 'YYYY-MM'),
        func.count(model.id)
    ).filter(
        func.to_char(date_column, 'YYYY') == str(year)
    ).group_by(
        func.to_char(date_column, 'YYYY-MM')
    ).order_by(
        func.to_char(date_column, 'YYYY-MM')
    ).all()

def _prepare_monthly_series(query_result, year):
    """Prepara uma série de 12 meses, preenchendo com zeros onde não há dados."""
    monthly_map = {f"{year}-{month:02d}": 0 for month in range(1, 13)}
    
    for month_str, count in query_result:
        if month_str in monthly_map:
            monthly_map[month_str] = count
            
    return list(monthly_map.values())

def get_monthly_comparison_data(year=None):
    """
    Busca e processa dados de rondas e ocorrências para comparação mensal.
    """
    if not year:
        year = datetime.now().year
    
    # 1. Busca e processa dados de Rondas
    rondas_raw = _get_monthly_aggregation(Ronda, Ronda.data_plantao_ronda, year)
    rondas_series = _prepare_monthly_series(rondas_raw, year)

    # 2. Busca e processa dados de Ocorrências
    ocorrencias_raw = _get_monthly_aggregation(Ocorrencia, Ocorrencia.data_hora_ocorrencia, year)
    ocorrencias_series = _prepare_monthly_series(ocorrencias_raw, year)
    
    # 3. Prepara labels para os gráficos (meses do ano)
    month_labels = [
        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
    ]
    
    return {
        'selected_year': year,
        'month_labels': month_labels,
        'rondas_data': rondas_series,
        'ocorrencias_data': ocorrencias_series
    }