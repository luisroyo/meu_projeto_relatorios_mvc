# app/services/dashboard/comparativo_dashboard.py
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple

from sqlalchemy import func

from app import db
from app.models import Ocorrencia, Ronda, Condominio, User, OcorrenciaTipo


def _apply_ronda_filters(query, filters):
    """Aplica filtros à query de rondas."""
    if filters.get("condominio_id"):
        query = query.filter(Ronda.condominio_id == filters["condominio_id"])
    
    if filters.get("supervisor_id"):
        query = query.filter(Ronda.supervisor_id == filters["supervisor_id"])
    
    if filters.get("turno"):
        query = query.filter(Ronda.turno_ronda == filters["turno"])
    
    if filters.get("data_inicio_str"):
        try:
            from datetime import datetime
            start_date = datetime.strptime(filters["data_inicio_str"], "%Y-%m-%d")
            query = query.filter(Ronda.data_plantao_ronda >= start_date)
        except ValueError:
            pass
    
    if filters.get("data_fim_str"):
        try:
            from datetime import datetime
            end_date = datetime.strptime(filters["data_fim_str"], "%Y-%m-%d")
            query = query.filter(Ronda.data_plantao_ronda <= end_date)
        except ValueError:
            pass
    
    return query


def _apply_ocorrencia_filters(query, filters):
    """Aplica filtros à query de ocorrências."""
    if filters.get("condominio_id"):
        query = query.filter(Ocorrencia.condominio_id == filters["condominio_id"])
    
    if filters.get("supervisor_id"):
        query = query.filter(Ocorrencia.supervisor_id == filters["supervisor_id"])
    
    if filters.get("tipo_ocorrencia_id"):
        query = query.filter(Ocorrencia.ocorrencia_tipo_id == filters["tipo_ocorrencia_id"])
    
    if filters.get("status"):
        query = query.filter(Ocorrencia.status == filters["status"])
    
    if filters.get("turno"):
        query = query.filter(Ocorrencia.turno == filters["turno"])
    
    if filters.get("data_inicio_str"):
        try:
            from datetime import datetime
            start_date = datetime.strptime(filters["data_inicio_str"], "%Y-%m-%d")
            query = query.filter(Ocorrencia.data_hora_ocorrencia >= start_date)
        except ValueError:
            pass
    
    if filters.get("data_fim_str"):
        try:
            from datetime import datetime
            end_date = datetime.strptime(filters["data_fim_str"], "%Y-%m-%d")
            query = query.filter(Ocorrencia.data_hora_ocorrencia <= end_date)
        except ValueError:
            pass
    
    return query


def _get_monthly_aggregation_with_filters(model, date_column, year, filters, is_ronda=True):
    """
    Função genérica para agregar dados de um modelo por mês com filtros.
    """
    if is_ronda:
        # Para rondas, usa total_rondas_no_log (soma das rondas individuais)
        query = db.session.query(
            func.to_char(date_column, "YYYY-MM"), 
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)
        )
    else:
        # Para ocorrências, conta registros
        query = db.session.query(
            func.to_char(date_column, "YYYY-MM"), 
            func.count(model.id)
        )
    
    # Aplica filtros específicos
    if is_ronda:
        query = _apply_ronda_filters(query, filters)
    else:
        query = _apply_ocorrencia_filters(query, filters)
    
    # Filtro de ano
    query = query.filter(func.to_char(date_column, "YYYY") == str(year))
    
    return (
        query.group_by(func.to_char(date_column, "YYYY-MM"))
        .order_by(func.to_char(date_column, "YYYY-MM"))
        .all()
    )


def _prepare_monthly_series(query_result, year):
    """Prepara uma série de 12 meses, preenchendo com zeros onde não há dados."""
    monthly_map = {f"{year}-{month:02d}": 0 for month in range(1, 13)}

    for month_str, count in query_result:
        if month_str in monthly_map:
            monthly_map[month_str] = count

    return list(monthly_map.values())


def _calculate_working_days_in_period(start_date, end_date):
    """
    Calcula o número de dias trabalhados em um período, considerando escala 12x36.
    Na escala 12x36, o supervisor trabalha 1 dia a cada 2 dias (12h trabalho + 36h folga = 48h total).
    """
    if not start_date or not end_date:
        return 0
    
    total_days = (end_date - start_date).days + 1
    # Na escala 12x36, trabalha 1 dia a cada 2 dias
    working_days = total_days // 2
    # Se sobrar 1 dia, considera como dia trabalhado (assumindo que começa trabalhando)
    if total_days % 2 == 1:
        working_days += 1
    
    return working_days


def _calculate_supervisor_specific_metrics(total_rondas, filters, year):
    """
    Calcula métricas específicas para um supervisor quando há filtro de supervisor.
    """
    if filters.get("supervisor_id"):
        # Se há filtro de supervisor, calcula baseado apenas nos dias que ele trabalhou
        dias_trabalhados = db.session.query(
            func.count(func.distinct(Ronda.data_plantao_ronda))
        ).filter(
            func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year),
            Ronda.supervisor_id == filters["supervisor_id"]
        ).scalar()
        
        media_rondas_dia_trabalhado = round(total_rondas / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
        return media_rondas_dia_trabalhado, dias_trabalhados
    else:
        # Se não há filtro de supervisor, usa o cálculo geral
        dias_trabalhados = db.session.query(
            func.count(func.distinct(Ronda.data_plantao_ronda))
        ).filter(
            func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year),
            Ronda.supervisor_id.isnot(None)
        ).scalar()
        
        media_rondas_dia_trabalhado = round(total_rondas / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
        return media_rondas_dia_trabalhado, dias_trabalhados


def _calculate_comparison_metrics(rondas_series: List[int], ocorrencias_series: List[int], filters: Dict = None) -> Dict:
    """Calcula métricas comparativas entre rondas e ocorrências."""
    total_rondas = sum(rondas_series)
    total_ocorrencias = sum(ocorrencias_series)
    
    # Calcula médias mensais
    meses_com_dados = len([x for x in rondas_series if x > 0])
    media_rondas_mensal = round(total_rondas / meses_com_dados, 1) if meses_com_dados > 0 else 0
    
    meses_com_ocorrencias = len([x for x in ocorrencias_series if x > 0])
    media_ocorrencias_mensal = round(total_ocorrencias / meses_com_ocorrencias, 1) if meses_com_ocorrencias > 0 else 0
    
    # Calcula média por dia real trabalhado (baseado nos dados reais da tabela)
    from datetime import datetime
    current_year = datetime.now().year
    
    # Usa função específica para calcular dias trabalhados
    media_rondas_dia_trabalhado, dias_trabalhados = _calculate_supervisor_specific_metrics(
        total_rondas, filters or {}, current_year
    )
    
    # Encontra meses com mais atividade
    mes_mais_rondas = "N/A"
    mes_mais_ocorrencias = "N/A"
    
    if rondas_series:
        max_rondas = max(rondas_series)
        if max_rondas > 0:
            mes_index = rondas_series.index(max_rondas)
            month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_mais_rondas = f"{month_names[mes_index]} ({max_rondas})"
    
    if ocorrencias_series:
        max_ocorrencias = max(ocorrencias_series)
        if max_ocorrencias > 0:
            mes_index = ocorrencias_series.index(max_ocorrencias)
            month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_mais_ocorrencias = f"{month_names[mes_index]} ({max_ocorrencias})"
    
    # Calcula tendências
    tendencia_rondas = _calculate_trend(rondas_series)
    tendencia_ocorrencias = _calculate_trend(ocorrencias_series)
    
    # Calcula proporção
    proporcao_ocorrencias_por_ronda = round((total_ocorrencias / total_rondas) * 100, 1) if total_rondas > 0 else 0
    
    return {
        "total_rondas": total_rondas,
        "total_ocorrencias": total_ocorrencias,
        "media_rondas_mensal": media_rondas_mensal,
        "media_ocorrencias_mensal": media_ocorrencias_mensal,
        "media_rondas_dia_trabalhado": media_rondas_dia_trabalhado,
        "dias_trabalhados_periodo": dias_trabalhados,
        "mes_mais_rondas": mes_mais_rondas,
        "mes_mais_ocorrencias": mes_mais_ocorrencias,
        "tendencia_rondas": tendencia_rondas,
        "tendencia_ocorrencias": tendencia_ocorrencias,
        "proporcao_ocorrencias_por_ronda": proporcao_ocorrencias_por_ronda,
    }


def _calculate_trend(data_series: List[int]) -> str:
    """Calcula a tendência baseada nos últimos 3 meses vs primeiros 3 meses."""
    if len(data_series) < 6:
        return "Insuficiente"
    
    primeiros_3 = sum(data_series[:3])
    ultimos_3 = sum(data_series[-3:])
    
    if ultimos_3 > primeiros_3 * 1.1:
        return "Crescimento"
    elif ultimos_3 < primeiros_3 * 0.9:
        return "Queda"
    else:
        return "Estável"


def _get_detailed_breakdown(year: int, filters: Dict) -> Dict:
    """Busca breakdown detalhado por diferentes critérios."""
    
    # Rondas por condomínio
    rondas_por_condominio = (
        db.session.query(
            Condominio.nome,
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total")
        )
        .join(Ronda, Condominio.id == Ronda.condominio_id)
        .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
    )
    rondas_por_condominio = _apply_ronda_filters(rondas_por_condominio, filters)
    rondas_por_condominio = (
        rondas_por_condominio.group_by(Condominio.nome)
        .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
        .limit(10)
        .all()
    )
    
    # Ocorrências por condomínio
    ocorrencias_por_condominio = (
        db.session.query(
            Condominio.nome,
            func.count(Ocorrencia.id).label("total")
        )
        .join(Ocorrencia, Condominio.id == Ocorrencia.condominio_id)
        .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
    )
    ocorrencias_por_condominio = _apply_ocorrencia_filters(ocorrencias_por_condominio, filters)
    ocorrencias_por_condominio = (
        ocorrencias_por_condominio.group_by(Condominio.nome)
        .order_by(func.count(Ocorrencia.id).desc())
        .limit(10)
        .all()
    )
    
    # Rondas por supervisor
    rondas_por_supervisor = (
        db.session.query(
            User.username,
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total")
        )
        .join(Ronda, User.id == Ronda.supervisor_id)
        .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
    )
    rondas_por_supervisor = _apply_ronda_filters(rondas_por_supervisor, filters)
    rondas_por_supervisor = (
        rondas_por_supervisor.group_by(User.username)
        .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
        .limit(10)
        .all()
    )
    
    # Ocorrências por supervisor
    ocorrencias_por_supervisor = (
        db.session.query(
            User.username,
            func.count(Ocorrencia.id).label("total")
        )
        .join(Ocorrencia, User.id == Ocorrencia.supervisor_id)
        .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
    )
    ocorrencias_por_supervisor = _apply_ocorrencia_filters(ocorrencias_por_supervisor, filters)
    ocorrencias_por_supervisor = (
        ocorrencias_por_supervisor.group_by(User.username)
        .order_by(func.count(Ocorrencia.id).desc())
        .limit(10)
        .all()
    )
    
    # Ocorrências por tipo
    ocorrencias_por_tipo = (
        db.session.query(
            OcorrenciaTipo.nome,
            func.count(Ocorrencia.id).label("total")
        )
        .join(Ocorrencia, OcorrenciaTipo.id == Ocorrencia.ocorrencia_tipo_id)
        .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
    )
    ocorrencias_por_tipo = _apply_ocorrencia_filters(ocorrencias_por_tipo, filters)
    ocorrencias_por_tipo = (
        ocorrencias_por_tipo.group_by(OcorrenciaTipo.nome)
        .order_by(func.count(Ocorrencia.id).desc())
        .limit(10)
        .all()
    )
    
    # Rondas por turno
    rondas_por_turno = (
        db.session.query(
            Ronda.turno_ronda,
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total")
        )
        .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
    )
    rondas_por_turno = _apply_ronda_filters(rondas_por_turno, filters)
    rondas_por_turno = (
        rondas_por_turno.group_by(Ronda.turno_ronda)
        .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
        .all()
    )
    
    # Ocorrências por status
    ocorrencias_por_status = (
        db.session.query(
            Ocorrencia.status,
            func.count(Ocorrencia.id).label("total")
        )
        .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
    )
    ocorrencias_por_status = _apply_ocorrencia_filters(ocorrencias_por_status, filters)
    ocorrencias_por_status = (
        ocorrencias_por_status.group_by(Ocorrencia.status)
        .order_by(func.count(Ocorrencia.id).desc())
        .all()
    )
    
    return {
        "rondas_por_condominio": rondas_por_condominio,
        "ocorrencias_por_condominio": ocorrencias_por_condominio,
        "rondas_por_supervisor": rondas_por_supervisor,
        "ocorrencias_por_supervisor": ocorrencias_por_supervisor,
        "rondas_por_turno": rondas_por_turno,
        "ocorrencias_por_tipo": ocorrencias_por_tipo,
        "ocorrencias_por_status": ocorrencias_por_status,
    }


def get_monthly_comparison_data(year=None, filters=None, selected_months=None, comparison_mode=None):
    """
    Busca e processa dados de rondas e ocorrências para comparação mensal detalhada com filtros avançados.
    
    Args:
        year: Ano para análise
        filters: Filtros aplicados
        selected_months: Lista de meses selecionados (1-12)
        comparison_mode: 'single' para um mês, 'comparison' para múltiplos meses
    """
    if not year:
        year = datetime.now().year
    
    if not filters:
        filters = {}
    
    if not selected_months:
        selected_months = []
    
    if not comparison_mode:
        comparison_mode = 'all'  # 'all', 'single', 'comparison'

    # 1. Busca dados básicos mensais com filtros
    if comparison_mode == 'single' and selected_months:
        # Modo de mês único
        month = selected_months[0]
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Aplica filtros de data para o mês específico
        filters['data_inicio_str'] = start_date.strftime('%Y-%m-%d')
        filters['data_fim_str'] = end_date.strftime('%Y-%m-%d')
        
        # Busca dados apenas para o mês selecionado
        rondas_raw = _get_monthly_aggregation_with_filters(Ronda, Ronda.data_plantao_ronda, year, filters, is_ronda=True)
        ocorrencias_raw = _get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, filters, is_ronda=False
        )
        
        # Prepara série apenas para o mês selecionado
        rondas_series = [0] * 12
        ocorrencias_series = [0] * 12
        
        for mes_str, total in rondas_raw:
            mes_num = int(mes_str.split('-')[1])
            rondas_series[mes_num - 1] = total
        
        for mes_str, total in ocorrencias_raw:
            mes_num = int(mes_str.split('-')[1])
            ocorrencias_series[mes_num - 1] = total
            
    elif comparison_mode == 'comparison' and len(selected_months) >= 2:
        # Modo de comparação entre meses
        rondas_series = [0] * 12
        ocorrencias_series = [0] * 12
        
        for month in selected_months:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Filtros temporários para o mês
            temp_filters = filters.copy()
            temp_filters['data_inicio_str'] = start_date.strftime('%Y-%m-%d')
            temp_filters['data_fim_str'] = end_date.strftime('%Y-%m-%d')
            
            # Busca dados para o mês
            rondas_raw = _get_monthly_aggregation_with_filters(Ronda, Ronda.data_plantao_ronda, year, temp_filters, is_ronda=True)
            ocorrencias_raw = _get_monthly_aggregation_with_filters(
                Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, temp_filters, is_ronda=False
            )
            
            # Adiciona aos dados
            for mes_str, total in rondas_raw:
                mes_num = int(mes_str.split('-')[1])
                rondas_series[mes_num - 1] = total
            
            for mes_str, total in ocorrencias_raw:
                mes_num = int(mes_str.split('-')[1])
                ocorrencias_series[mes_num - 1] = total
    else:
        # Modo padrão - todos os meses
        rondas_raw = _get_monthly_aggregation_with_filters(Ronda, Ronda.data_plantao_ronda, year, filters, is_ronda=True)
        rondas_series = _prepare_monthly_series(rondas_raw, year)

        ocorrencias_raw = _get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, filters, is_ronda=False
        )
        ocorrencias_series = _prepare_monthly_series(ocorrencias_raw, year)

    # 2. Calcula métricas comparativas
    metrics = _calculate_comparison_metrics(rondas_series, ocorrencias_series, filters)
    
    # 3. Busca breakdown detalhado
    breakdown = _get_detailed_breakdown(year, filters)

    # 4. Prepara labels para os gráficos
    month_labels = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]
    
    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    # 5. Busca dados para filtros
    condominios = Condominio.query.order_by(Condominio.nome).all()
    supervisors = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    tipos_ocorrencia = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    
    turnos = ["Diurno", "Noturno", "Diurno Par", "Diurno Impar", "Noturno Par", "Noturno Impar"]
    status_list = ["Registrada", "Em Andamento", "Concluída"]

    return {
        "selected_year": year,
        "selected_months": selected_months,
        "comparison_mode": comparison_mode,
        "month_labels": month_labels,
        "month_names": month_names,
        "rondas_data": rondas_series,
        "ocorrencias_data": ocorrencias_series,
        "metrics": metrics,
        "breakdown": breakdown,
        "filters": filters,
        "filter_options": {
            "condominios": condominios,
            "supervisors": supervisors,
            "tipos_ocorrencia": tipos_ocorrencia,
            "turnos": turnos,
            "status_list": status_list,
        }
    }
