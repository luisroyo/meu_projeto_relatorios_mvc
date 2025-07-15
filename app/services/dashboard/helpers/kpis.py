# app/services/dashboard/helpers/kpis.py
import logging
from datetime import timedelta

from sqlalchemy import func, tuple_

from app import db
from app.models import EscalaMensal, Ocorrencia, Ronda, User
from app.services import ocorrencia_service

logger = logging.getLogger(__name__)


def calculate_average_duration_by_condominio(duracao_somas_raw: list) -> list:
    """
    Calcula a duração média da ronda por condomínio e ordena o resultado.
    """
    dados_para_ordenar = []
    for nome, soma_duracao, soma_rondas in duracao_somas_raw:
        soma_duracao = soma_duracao or 0
        soma_rondas = soma_rondas or 0
        media = round(soma_duracao / soma_rondas, 2) if soma_rondas > 0 else 0
        dados_para_ordenar.append({"condominio": nome, "media": media})

    return sorted(dados_para_ordenar, key=lambda item: item["media"], reverse=True)


def calculate_main_ronda_kpis(base_kpi_query, supervisor_labels: list) -> tuple:
    """
    Calcula os principais KPIs de rondas: total, duração média geral e supervisor mais ativo.
    """
    total_rondas = base_kpi_query.with_entities(
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)
    ).scalar()
    soma_duracao = base_kpi_query.with_entities(
        func.coalesce(func.sum(Ronda.duracao_total_rondas_minutos), 0)
    ).scalar()

    duracao_media_geral = (
        round(soma_duracao / total_rondas, 2) if total_rondas > 0 else 0
    )
    supervisor_mais_ativo = supervisor_labels[0] if supervisor_labels else "N/A"

    return total_rondas, duracao_media_geral, supervisor_mais_ativo


def calculate_average_rondas_per_day(
    total_rondas: int, filters: dict, date_start_range, date_end_range
) -> float:
    """
    Calcula o número médio de rondas por dia, considerando a escala do supervisor ou o tipo de turno.
    """
    supervisor_id_filter = filters.get("supervisor_id")
    turno_filter = filters.get("turno")
    num_dias_divisor = 0

    if supervisor_id_filter:
        meses_anos = set()
        current_date_for_months = date_start_range
        while current_date_for_months <= date_end_range:
            meses_anos.add(
                (current_date_for_months.year, current_date_for_months.month)
            )
            # Avança para o próximo mês
            next_month_year = current_date_for_months.year + (
                current_date_for_months.month // 12
            )
            next_month = current_date_for_months.month % 12 + 1
            current_date_for_months = current_date_for_months.replace(
                year=next_month_year, month=next_month, day=1
            )

        turnos_supervisor_db = (
            db.session.query(EscalaMensal.nome_turno)
            .filter(
                EscalaMensal.supervisor_id == supervisor_id_filter,
                tuple_(EscalaMensal.ano, EscalaMensal.mes).in_(meses_anos),
            )
            .distinct()
            .all()
        )
        turnos_do_supervisor = {turno[0] for turno in turnos_supervisor_db}

        if turnos_do_supervisor:
            current_day = date_start_range
            while current_day <= date_end_range:
                paridade = "Par" if current_day.day % 2 == 0 else "Impar"
                turno_diurno_do_dia = f"Diurno {paridade}"
                turno_noturno_do_dia = f"Noturno {paridade}"

                if (
                    turno_diurno_do_dia in turnos_do_supervisor
                    or turno_noturno_do_dia in turnos_do_supervisor
                ):
                    num_dias_divisor += 1
                current_day += timedelta(days=1)

    elif turno_filter:
        current_day = date_start_range
        while current_day <= date_end_range:
            paridade = "Par" if current_day.day % 2 == 0 else "Impar"
            if paridade in turno_filter:
                num_dias_divisor += 1
            current_day += timedelta(days=1)

    else:
        num_dias_divisor = (date_end_range - date_start_range).days + 1

    return round(total_rondas / num_dias_divisor, 1) if num_dias_divisor > 0 else 0


def find_top_ocorrencia_supervisor(filters: dict) -> str:
    """
    Encontra o nome do supervisor com mais ocorrências com base nos filtros aplicados.
    """
    try:
        query = (
            db.session.query(
                Ocorrencia.supervisor_id,
                func.count(Ocorrencia.id).label("ocorrencia_count"),
            )
            .join(User, Ocorrencia.supervisor_id == User.id)
            .filter(User.is_supervisor == True, Ocorrencia.supervisor_id.isnot(None))
        )

        # Reutiliza o serviço de filtro de ocorrências
        query = ocorrencia_service.apply_ocorrencia_filters(query, filters)

        top_supervisor_data = (
            query.group_by(Ocorrencia.supervisor_id)
            .order_by(func.count(Ocorrencia.id).desc())
            .first()
        )

        if top_supervisor_data and top_supervisor_data.supervisor_id:
            supervisor = User.query.get(top_supervisor_data.supervisor_id)
            if supervisor:
                return supervisor.username

        return "N/A"

    except Exception as e:
        logger.error(
            f"Erro ao calcular o supervisor com mais ocorrências: {e}", exc_info=True
        )
        return "Erro ao calcular"
