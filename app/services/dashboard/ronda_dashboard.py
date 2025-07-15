# app/services/dashboard/ronda_dashboard.py
import logging
from datetime import datetime

from flask import flash
from sqlalchemy import func

from app import db
from app.models import Condominio, Ronda, User
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
    # Rondas por Condomínio
    rondas_por_condominio_q = db.session.query(
        Condominio.nome, func.sum(Ronda.total_rondas_no_log)
    ).join(Ronda, Condominio.id == Ronda.condominio_id)
    rondas_por_condominio_q = filters_helper.apply_ronda_filters(
        rondas_por_condominio_q, filters, date_start_range, date_end_range
    )
    rondas_por_condominio = (
        rondas_por_condominio_q.group_by(Condominio.nome)
        .order_by(func.sum(Ronda.total_rondas_no_log).desc())
        .all()
    )
    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] or 0 for item in rondas_por_condominio]

    # Duração média por Condomínio
    duracao_somas_q = db.session.query(
        Condominio.nome,
        func.sum(Ronda.duracao_total_rondas_minutos),
        func.sum(Ronda.total_rondas_no_log),
    ).join(Ronda, Condominio.id == Ronda.condominio_id)
    duracao_somas_q = filters_helper.apply_ronda_filters(
        duracao_somas_q, filters, date_start_range, date_end_range
    )
    duracao_somas_raw = duracao_somas_q.group_by(Condominio.nome).all()

    # [ALTERADO] Lógica de cálculo movida para o helper de KPIs
    dados_ordenados = kpis_helper.calculate_average_duration_by_condominio(
        duracao_somas_raw
    )
    duracao_condominio_labels = [item["condominio"] for item in dados_ordenados]
    duracao_media_data = [item["media"] for item in dados_ordenados]

    # Rondas por Turno
    rondas_por_turno_q = db.session.query(
        Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)
    ).filter(Ronda.turno_ronda.isnot(None), Ronda.total_rondas_no_log.isnot(None))
    rondas_por_turno_q = filters_helper.apply_ronda_filters(
        rondas_por_turno_q, filters, date_start_range, date_end_range
    )
    rondas_por_turno = (
        rondas_por_turno_q.group_by(Ronda.turno_ronda)
        .order_by(func.sum(Ronda.total_rondas_no_log).desc())
        .all()
    )
    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] or 0 for item in rondas_por_turno]

    # Rondas por Supervisor
    rondas_por_supervisor_q = (
        db.session.query(
            User.username, func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)
        )
        .outerjoin(Ronda, User.id == Ronda.supervisor_id)
        .filter(User.is_supervisor == True)
    )
    rondas_por_supervisor_q = filters_helper.apply_ronda_filters(
        rondas_por_supervisor_q, filters, date_start_range, date_end_range
    )
    rondas_por_supervisor = (
        rondas_por_supervisor_q.group_by(User.username)
        .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
        .all()
    )
    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] for item in rondas_por_supervisor]

    # Atividade de Rondas por Dia (Evolução)
    rondas_por_dia_q = db.session.query(
        func.date(Ronda.data_plantao_ronda), func.sum(Ronda.total_rondas_no_log)
    ).filter(Ronda.total_rondas_no_log.isnot(None))
    rondas_por_dia_q = filters_helper.apply_ronda_filters(
        rondas_por_dia_q, filters, date_start_range, date_end_range
    )
    rondas_por_dia = (
        rondas_por_dia_q.group_by(func.date(Ronda.data_plantao_ronda))
        .order_by(func.date(Ronda.data_plantao_ronda))
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
                db.session.query(Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log))
                .filter(
                    Ronda.data_plantao_ronda == data_selecionada,
                    Ronda.turno_ronda.isnot(None),
                )
                .group_by(Ronda.turno_ronda)
                .order_by(Ronda.turno_ronda)
                .all()
            )
            dados_dia_detalhado["labels"] = [item[0] for item in rondas_por_turno_dia]
            dados_dia_detalhado["data"] = [
                item[1] or 0 for item in rondas_por_turno_dia
            ]
            dados_tabela_dia = (
                db.session.query(
                    User.username,
                    Ronda.turno_ronda,
                    func.sum(Ronda.total_rondas_no_log),
                )
                .join(User, User.id == Ronda.supervisor_id)
                .filter(Ronda.data_plantao_ronda == data_selecionada)
                .group_by(User.username, Ronda.turno_ronda)
                .order_by(User.username)
                .all()
            )
        except (ValueError, TypeError):
            flash("Data para análise detalhada em formato inválido.", "warning")

    # 3. Cálculo dos KPIs principais
    base_kpi_query = filters_helper.apply_ronda_filters(
        db.session.query(Ronda), filters, date_start_range, date_end_range
    )

    # [ALTERADO] Lógica de cálculo movida para o helper de KPIs
    total_rondas, duracao_media_geral, supervisor_mais_ativo = (
        kpis_helper.calculate_main_ronda_kpis(base_kpi_query, supervisor_labels)
    )
    media_rondas_dia = kpis_helper.calculate_average_rondas_per_day(
        total_rondas, filters, date_start_range, date_end_range
    )

    # [REMOVIDO] Blocos de código para calcular KPIs foram extraídos para helpers/kpis.py

    # 4. Retorno dos dados consolidados
    return {
        "total_rondas": total_rondas,
        "duracao_media_geral": duracao_media_geral,
        "supervisor_mais_ativo": supervisor_mais_ativo,
        "media_rondas_dia": media_rondas_dia,
        "condominio_labels": condominio_labels,
        "rondas_por_condominio_data": rondas_por_condominio_data,
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
    }
