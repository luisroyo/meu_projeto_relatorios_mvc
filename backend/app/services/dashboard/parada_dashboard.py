# app/services/dashboard/parada_dashboard.py
import logging
from datetime import datetime

from sqlalchemy import func

from app import db
from app.models import Condominio, Parada, User
from app.utils.date_utils import parse_date_range

from .helpers import chart_data, date_utils

logger = logging.getLogger(__name__)


def get_parada_dashboard_data(filters):
    """
    Busca e processa todos os dados necessários para o dashboard de paradas.
    """
    # 1. Preparação de Filtros
    data_inicio_str = filters.get("data_inicio_str")
    data_fim_str = filters.get("data_fim_str")
    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)

    # 2. Busca de KPIs Principais
    total_paradas_q = db.session.query(func.coalesce(func.sum(Parada.total_paradas_no_log), 0)).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )
    total_duracao_q = db.session.query(func.coalesce(func.sum(Parada.duracao_total_paradas_minutos), 0)).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )
    dias_com_dados_q = db.session.query(func.count(func.distinct(Parada.data_plantao_parada))).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )
    supervisor_mais_ativo_q = db.session.query(
        User.username, func.sum(Parada.total_paradas_no_log)
    ).join(
        User, Parada.supervisor_id == User.id
    ).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Aplicar filtros
    if filters.get("supervisor_id"):
        total_paradas_q = total_paradas_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        total_duracao_q = total_duracao_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        dias_com_dados_q = dias_com_dados_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        supervisor_mais_ativo_q = supervisor_mais_ativo_q.filter(Parada.supervisor_id == filters["supervisor_id"])

    if filters.get("condominio_id"):
        total_paradas_q = total_paradas_q.filter(Parada.condominio_id == filters["condominio_id"])
        total_duracao_q = total_duracao_q.filter(Parada.condominio_id == filters["condominio_id"])
        dias_com_dados_q = dias_com_dados_q.filter(Parada.condominio_id == filters["condominio_id"])
        supervisor_mais_ativo_q = supervisor_mais_ativo_q.filter(Parada.condominio_id == filters["condominio_id"])

    if filters.get("turno"):
        total_paradas_q = total_paradas_q.filter(Parada.turno_parada == filters["turno"])
        total_duracao_q = total_duracao_q.filter(Parada.turno_parada == filters["turno"])
        dias_com_dados_q = dias_com_dados_q.filter(Parada.turno_parada == filters["turno"])
        supervisor_mais_ativo_q = supervisor_mais_ativo_q.filter(Parada.turno_parada == filters["turno"])

    total_paradas = total_paradas_q.scalar() or 0
    total_duracao = total_duracao_q.scalar() or 0
    dias_com_dados = dias_com_dados_q.scalar() or 0

    duracao_media_geral = round(total_duracao / total_paradas, 1) if total_paradas > 0 else 0
    media_paradas_dia = round(total_paradas / dias_com_dados, 1) if dias_com_dados > 0 else 0

    supervisor_mais_ativo = (
        supervisor_mais_ativo_q.group_by(User.username)
        .order_by(func.sum(Parada.total_paradas_no_log).desc())
        .first()
    )
    supervisor_mais_ativo_nome = supervisor_mais_ativo[0] if supervisor_mais_ativo else "N/A"

    # 3. Gráficos Data

    # Paradas por Condomínio
    paradas_por_condominio_q = db.session.query(
        Condominio.nome, func.sum(Parada.total_paradas_no_log)
    ).join(
        Condominio, Parada.condominio_id == Condominio.id
    ).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Duração média por Condomínio
    duracao_por_condominio_q = db.session.query(
        Condominio.nome,
        func.sum(Parada.duracao_total_paradas_minutos),
        func.sum(Parada.total_paradas_no_log)
    ).join(
        Condominio, Parada.condominio_id == Condominio.id
    ).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Paradas por Turno
    paradas_por_turno_q = db.session.query(
        Parada.turno_parada, func.sum(Parada.total_paradas_no_log)
    ).filter(
        Parada.turno_parada.isnot(None),
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Paradas por Supervisor
    paradas_por_supervisor_q = db.session.query(
        User.username, func.sum(Parada.total_paradas_no_log)
    ).join(
        User, Parada.supervisor_id == User.id
    ).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Evolução
    paradas_por_dia_q = db.session.query(
        Parada.data_plantao_parada, func.sum(Parada.total_paradas_no_log)
    ).filter(
        Parada.data_plantao_parada >= date_start_range,
        Parada.data_plantao_parada <= date_end_range
    )

    # Aplicar filtros nos sub-gráficos
    if filters.get("supervisor_id"):
        paradas_por_condominio_q = paradas_por_condominio_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        duracao_por_condominio_q = duracao_por_condominio_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        paradas_por_turno_q = paradas_por_turno_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        paradas_por_supervisor_q = paradas_por_supervisor_q.filter(Parada.supervisor_id == filters["supervisor_id"])
        paradas_por_dia_q = paradas_por_dia_q.filter(Parada.supervisor_id == filters["supervisor_id"])

    if filters.get("condominio_id"):
        paradas_por_condominio_q = paradas_por_condominio_q.filter(Parada.condominio_id == filters["condominio_id"])
        duracao_por_condominio_q = duracao_por_condominio_q.filter(Parada.condominio_id == filters["condominio_id"])
        paradas_por_turno_q = paradas_por_turno_q.filter(Parada.condominio_id == filters["condominio_id"])
        paradas_por_supervisor_q = paradas_por_supervisor_q.filter(Parada.condominio_id == filters["condominio_id"])
        paradas_por_dia_q = paradas_por_dia_q.filter(Parada.condominio_id == filters["condominio_id"])

    if filters.get("turno"):
        paradas_por_condominio_q = paradas_por_condominio_q.filter(Parada.turno_parada == filters["turno"])
        duracao_por_condominio_q = duracao_por_condominio_q.filter(Parada.turno_parada == filters["turno"])
        paradas_por_turno_q = paradas_por_turno_q.filter(Parada.turno_parada == filters["turno"])
        paradas_por_supervisor_q = paradas_por_supervisor_q.filter(Parada.turno_parada == filters["turno"])
        paradas_por_dia_q = paradas_por_dia_q.filter(Parada.turno_parada == filters["turno"])

    # Consolidação dos resultados dos gráficos
    paradas_por_condominio = (
        paradas_por_condominio_q.group_by(Condominio.nome)
        .order_by(func.sum(Parada.total_paradas_no_log).desc())
        .all()
    )
    condominio_labels = [item[0] for item in paradas_por_condominio]
    condominio_data = [item[1] or 0 for item in paradas_por_condominio]

    duracao_por_condominio = duracao_por_condominio_q.group_by(Condominio.nome).all()
    duracao_condominio_labels = []
    duracao_media_data = []
    for name, total_min, total_qty in duracao_por_condominio:
        duracao_condominio_labels.append(name)
        media = round(total_min / total_qty, 1) if (total_qty and total_qty > 0) else 0
        duracao_media_data.append(media)

    paradas_por_turno = (
        paradas_por_turno_q.group_by(Parada.turno_parada)
        .order_by(func.sum(Parada.total_paradas_no_log).desc())
        .all()
    )
    turno_labels = [item[0] for item in paradas_por_turno]
    paradas_por_turno_data = [item[1] or 0 for item in paradas_por_turno]

    paradas_por_supervisor = (
        paradas_por_supervisor_q.group_by(User.username)
        .order_by(func.sum(Parada.total_paradas_no_log).desc())
        .all()
    )
    supervisor_labels = [item[0] for item in paradas_por_supervisor]
    paradas_por_supervisor_data = [item[1] or 0 for item in paradas_por_supervisor]

    paradas_por_dia = (
        paradas_por_dia_q.group_by(Parada.data_plantao_parada)
        .order_by(Parada.data_plantao_parada)
        .all()
    )

    parada_date_labels = []
    parada_activity_data = []
    if (date_end_range - date_start_range).days < 366:
        parada_date_labels = date_utils.generate_date_labels(date_start_range, date_end_range)
        parada_activity_data = chart_data.fill_series_with_zeros(paradas_por_dia, parada_date_labels)

    # 4. Retorno dos dados consolidados
    return {
        "total_paradas": total_paradas,
        "total_duracao": total_duracao,
        "duracao_media_geral": duracao_media_geral,
        "supervisor_mais_ativo": supervisor_mais_ativo_nome,
        "media_paradas_dia": media_paradas_dia,
        "condominio_labels": condominio_labels,
        "condominio_data": condominio_data,
        "duracao_condominio_labels": duracao_condominio_labels,
        "duracao_media_data": duracao_media_data,
        "turno_labels": turno_labels,
        "paradas_por_turno_data": paradas_por_turno_data,
        "supervisor_labels": supervisor_labels,
        "paradas_por_supervisor_data": paradas_por_supervisor_data,
        "parada_date_labels": parada_date_labels,
        "parada_activity_data": parada_activity_data,
        "selected_data_inicio_str": date_start_range.strftime("%Y-%m-%d"),
        "selected_data_fim_str": date_end_range.strftime("%Y-%m-%d"),
    }
