# app/services/dashboard/ronda_dashboard.py
import logging
from datetime import datetime

from flask import flash
from sqlalchemy import func

from app import db
from app.models import Condominio, Ronda, User, VWRondasDetalhadas
from app.utils.date_utils import parse_date_range

# [NOVO] Importa o helper de KPIs
from .helpers import chart_data, date_utils
from .helpers import filters as filters_helper
from .helpers import kpis as kpis_helper

logger = logging.getLogger(__name__)


def get_ronda_dashboard_data(filters):
    """
    Busca e processa todos os dados necessários para o dashboard de rondas.
    """
    # 1. Preparação de Filtros
    data_inicio_str = filters.get("data_inicio_str")
    data_fim_str = filters.get("data_fim_str")
    data_especifica_str = filters.get("data_especifica", "")
    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)

    # 2. Busca de Dados para Gráficos
    # Rondas por Condomínio - usando a view
    rondas_por_condominio_q = db.session.query(
        VWRondasDetalhadas.condominio_nome, func.sum(VWRondasDetalhadas.total_rondas_no_log)
    ).filter(
        VWRondasDetalhadas.condominio_nome.isnot(None),
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        rondas_por_condominio_q = rondas_por_condominio_q.filter(
            VWRondasDetalhadas.supervisor_id == filters["supervisor_id"]
        )
    if filters.get("condominio_id"):
        rondas_por_condominio_q = rondas_por_condominio_q.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    if filters.get("turno"):
        rondas_por_condominio_q = rondas_por_condominio_q.filter(
            VWRondasDetalhadas.turno_ronda == filters["turno"]
        )
    rondas_por_condominio = (
        rondas_por_condominio_q.group_by(VWRondasDetalhadas.condominio_nome)
        .order_by(func.sum(VWRondasDetalhadas.total_rondas_no_log).desc())
        .all()
    )
    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] or 0 for item in rondas_por_condominio]

    # Duração média por Condomínio - usando a view
    duracao_somas_q = db.session.query(
        VWRondasDetalhadas.condominio_nome,
        func.sum(VWRondasDetalhadas.duracao_total_rondas_minutos),
        func.sum(VWRondasDetalhadas.total_rondas_no_log),
    ).filter(
        VWRondasDetalhadas.condominio_nome.isnot(None),
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        duracao_somas_q = duracao_somas_q.filter(
            VWRondasDetalhadas.supervisor_id == filters["supervisor_id"]
        )
    if filters.get("condominio_id"):
        duracao_somas_q = duracao_somas_q.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    if filters.get("turno"):
        duracao_somas_q = duracao_somas_q.filter(
            VWRondasDetalhadas.turno_ronda == filters["turno"]
        )
    duracao_somas_raw = duracao_somas_q.group_by(VWRondasDetalhadas.condominio_nome).all()

    # [ALTERADO] Lógica de cálculo movida para o helper de KPIs
    dados_ordenados = kpis_helper.calculate_average_duration_by_condominio(
        duracao_somas_raw
    )
    duracao_condominio_labels = [item["condominio"] for item in dados_ordenados]
    duracao_media_data = [item["media"] for item in dados_ordenados]

    # Rondas por Turno - usando a view
    rondas_por_turno_q = db.session.query(
        VWRondasDetalhadas.turno_ronda, func.sum(VWRondasDetalhadas.total_rondas_no_log)
    ).filter(
        VWRondasDetalhadas.turno_ronda.isnot(None), 
        VWRondasDetalhadas.total_rondas_no_log.isnot(None),
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        rondas_por_turno_q = rondas_por_turno_q.filter(
            VWRondasDetalhadas.supervisor_id == filters["supervisor_id"]
        )
    if filters.get("condominio_id"):
        rondas_por_turno_q = rondas_por_turno_q.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    rondas_por_turno = (
        rondas_por_turno_q.group_by(VWRondasDetalhadas.turno_ronda)
        .order_by(func.sum(VWRondasDetalhadas.total_rondas_no_log).desc())
        .all()
    )
    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] or 0 for item in rondas_por_turno]

    # Rondas por Supervisor - usando a view
    rondas_por_supervisor_q = db.session.query(
        VWRondasDetalhadas.supervisor_username, func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
    ).filter(
        VWRondasDetalhadas.supervisor_username.isnot(None),
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("condominio_id"):
        rondas_por_supervisor_q = rondas_por_supervisor_q.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    if filters.get("turno"):
        rondas_por_supervisor_q = rondas_por_supervisor_q.filter(
            VWRondasDetalhadas.turno_ronda == filters["turno"]
        )
    rondas_por_supervisor = (
        rondas_por_supervisor_q.group_by(VWRondasDetalhadas.supervisor_username)
        .order_by(func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0).desc())
        .all()
    )
    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] for item in rondas_por_supervisor]

    # Atividade de Rondas por Dia (Evolução) - usando a view
    rondas_por_dia_q = db.session.query(
        func.date(VWRondasDetalhadas.data_plantao_ronda), func.sum(VWRondasDetalhadas.total_rondas_no_log)
    ).filter(
        VWRondasDetalhadas.total_rondas_no_log.isnot(None),
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        rondas_por_dia_q = rondas_por_dia_q.filter(
            VWRondasDetalhadas.supervisor_id == filters["supervisor_id"]
        )
    if filters.get("condominio_id"):
        rondas_por_dia_q = rondas_por_dia_q.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    if filters.get("turno"):
        rondas_por_dia_q = rondas_por_dia_q.filter(
            VWRondasDetalhadas.turno_ronda == filters["turno"]
        )
    rondas_por_dia = (
        rondas_por_dia_q.group_by(func.date(VWRondasDetalhadas.data_plantao_ronda))
        .order_by(func.date(VWRondasDetalhadas.data_plantao_ronda))
        .all()
    )

    ronda_date_labels, ronda_activity_data = [], []
    if (date_end_range - date_start_range).days < 366:
        ronda_date_labels = date_utils.generate_date_labels(
            date_start_range, date_end_range
        )
        ronda_activity_data = chart_data.fill_series_with_zeros(
            rondas_por_dia, ronda_date_labels
        )

    # Detalhes para um dia específico
    dados_dia_detalhado = {"labels": [], "data": []}
    dados_tabela_dia = []
    if data_especifica_str:
        try:
            data_selecionada = datetime.strptime(data_especifica_str, "%Y-%m-%d").date()
            rondas_por_turno_dia = (
                db.session.query(VWRondasDetalhadas.turno_ronda, func.sum(VWRondasDetalhadas.total_rondas_no_log))
                .filter(
                    VWRondasDetalhadas.data_plantao_ronda == data_selecionada,
                    VWRondasDetalhadas.turno_ronda.isnot(None),
                )
                .group_by(VWRondasDetalhadas.turno_ronda)
                .order_by(VWRondasDetalhadas.turno_ronda)
                .all()
            )
            dados_dia_detalhado["labels"] = [item[0] for item in rondas_por_turno_dia]
            dados_dia_detalhado["data"] = [
                item[1] or 0 for item in rondas_por_turno_dia
            ]
            dados_tabela_dia = (
                db.session.query(
                    VWRondasDetalhadas.supervisor_username,
                    VWRondasDetalhadas.turno_ronda,
                    func.sum(VWRondasDetalhadas.total_rondas_no_log),
                )
                .filter(VWRondasDetalhadas.data_plantao_ronda == data_selecionada)
                .group_by(VWRondasDetalhadas.supervisor_username, VWRondasDetalhadas.turno_ronda)
                .order_by(VWRondasDetalhadas.supervisor_username)
                .all()
            )
        except (ValueError, TypeError):
            flash("Data para análise detalhada em formato inválido.", "warning")

    # 3. Cálculo dos KPIs principais - usando a view
    base_kpi_query = db.session.query(VWRondasDetalhadas).filter(
        VWRondasDetalhadas.data_plantao_ronda >= date_start_range,
        VWRondasDetalhadas.data_plantao_ronda <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        base_kpi_query = base_kpi_query.filter(
            VWRondasDetalhadas.supervisor_id == filters["supervisor_id"]
        )
    if filters.get("condominio_id"):
        base_kpi_query = base_kpi_query.filter(
            VWRondasDetalhadas.condominio_id == filters["condominio_id"]
        )
    if filters.get("turno"):
        base_kpi_query = base_kpi_query.filter(
            VWRondasDetalhadas.turno_ronda == filters["turno"]
        )

    # [ALTERADO] Lógica de cálculo movida para o helper de KPIs
    total_rondas, duracao_media_geral, supervisor_mais_ativo = (
        kpis_helper.calculate_main_ronda_kpis(base_kpi_query, supervisor_labels)
    )
    media_rondas_dia = kpis_helper.calculate_average_rondas_per_day(
        total_rondas, filters, date_start_range, date_end_range, base_kpi_query
    )
    
    # [NOVO] Informações adicionais sobre o período
    periodo_info = kpis_helper.get_ronda_period_info(
        base_kpi_query, date_start_range, date_end_range, 
        supervisor_id=filters.get("supervisor_id")
    )
    
    # [NOVO] Comparação com período anterior
    comparacao_periodo = kpis_helper.calculate_period_comparison(
        base_kpi_query, date_start_range, date_end_range, 
        supervisor_id=filters.get("supervisor_id"),
        filters=filters
    )

    # [REMOVIDO] Blocos de código para calcular KPIs foram extraídos para helpers/kpis.py

    # 4. Retorno dos dados consolidados
    return {
        "total_rondas": total_rondas,
        "duracao_media_geral": duracao_media_geral,
        "supervisor_mais_ativo": supervisor_mais_ativo,
        "media_rondas_dia": media_rondas_dia,
        "condominio_labels": condominio_labels,
        "condominio_data": rondas_por_condominio_data,
        "duracao_condominio_labels": duracao_condominio_labels,
        "duracao_media_data": duracao_media_data,
        "turno_labels": turno_labels,
        "rondas_por_turno_data": rondas_por_turno_data,
        "supervisor_labels": supervisor_labels,
        "rondas_por_supervisor_data": rondas_por_supervisor_data,
        "ronda_date_labels": ronda_date_labels,
        "ronda_activity_data": ronda_activity_data,
        "dados_dia_detalhado": dados_dia_detalhado,
        "dados_tabela_dia": dados_tabela_dia,
        "selected_data_inicio_str": date_start_range.strftime("%Y-%m-%d"),
        "selected_data_fim_str": date_end_range.strftime("%Y-%m-%d"),
        # [NOVO] Informações detalhadas sobre o período
        "periodo_info": periodo_info,
        "comparacao_periodo": comparacao_periodo,
    }
