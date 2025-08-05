# app/services/dashboard/helpers/kpis.py
import logging
from datetime import timedelta, datetime

from sqlalchemy import func, tuple_, text

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
    from app.models import VWRondasDetalhadas
    
    total_rondas = base_kpi_query.with_entities(
        func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
    ).scalar()
    soma_duracao = base_kpi_query.with_entities(
        func.coalesce(func.sum(VWRondasDetalhadas.duracao_total_rondas_minutos), 0)
    ).scalar()

    duracao_media_geral = (
        round(soma_duracao / total_rondas, 2) if total_rondas > 0 else 0
    )
    supervisor_mais_ativo = supervisor_labels[0] if supervisor_labels else "N/A"

    return total_rondas, duracao_media_geral, supervisor_mais_ativo


def calculate_average_rondas_per_day(
    total_rondas: int, filters: dict, date_start_range, date_end_range, base_kpi_query=None
) -> float:
    """
    Calcula o número médio de rondas por dia, considerando a escala do supervisor ou o tipo de turno.
    MELHORIA: Agora considera a última data registrada no sistema, não o total de dias do mês.
    """
    supervisor_id_filter = filters.get("supervisor_id")
    turno_filter = filters.get("turno")
    num_dias_divisor = 0

    # [NOVO] Busca a última data registrada no sistema dentro do período
    from app.models import VWRondasDetalhadas
    
    if base_kpi_query:
        ultima_data_registrada = base_kpi_query.with_entities(
            func.max(VWRondasDetalhadas.data_plantao_ronda)
        ).scalar()
    else:
        # Fallback: busca diretamente na tabela Ronda
        ultima_data_registrada = db.session.query(
            func.max(Ronda.data_plantao_ronda)
        ).filter(
            Ronda.data_plantao_ronda >= date_start_range,
            Ronda.data_plantao_ronda <= date_end_range
        ).scalar()
    
    if not ultima_data_registrada:
        # Se não há dados, retorna 0
        return 0
    
    # [NOVO] Ajusta o date_end_range para a última data registrada
    date_end_range_real = min(date_end_range, ultima_data_registrada)

    if supervisor_id_filter:
        meses_anos = set()
        current_date_for_months = date_start_range
        while current_date_for_months <= date_end_range_real:
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
            while current_day <= date_end_range_real:
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
        while current_day <= date_end_range_real:
            paridade = "Par" if current_day.day % 2 == 0 else "Impar"
            if paridade in turno_filter:
                num_dias_divisor += 1
            current_day += timedelta(days=1)

    else:
        # [MELHORADO] Usa a data real até onde há registros
        num_dias_divisor = (date_end_range_real - date_start_range).days + 1

    return round(total_rondas / num_dias_divisor, 1) if num_dias_divisor > 0 else 0


def find_top_ocorrencia_supervisor(filters: dict) -> str:
    """
    Encontra o nome do supervisor com mais ocorrências com base nos filtros aplicados.
    """
    try:
        from app.models import VWOcorrenciasDetalhadas
        from app.utils.date_utils import parse_date_range
        
        # Preparar filtros de data
        data_inicio_str = filters.get("data_inicio_str")
        data_fim_str = filters.get("data_fim_str")
        date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)
        
        # Query usando a view diretamente
        query = db.session.query(
            VWOcorrenciasDetalhadas.supervisor,
            func.count(VWOcorrenciasDetalhadas.id).label("ocorrencia_count")
        ).filter(
            VWOcorrenciasDetalhadas.supervisor.isnot(None),
            VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
            VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range
        )
        
        # Aplicar filtros adicionais
        if filters.get("condominio_id"):
            # Buscar o nome do condomínio pelo ID
            from app.models import Condominio
            condominio = Condominio.query.get(filters["condominio_id"])
            if condominio:
                query = query.filter(VWOcorrenciasDetalhadas.condominio == condominio.nome)
        
        if filters.get("turno"):
            query = query.filter(VWOcorrenciasDetalhadas.turno == filters["turno"])
            
        if filters.get("status"):
            query = query.filter(VWOcorrenciasDetalhadas.status == filters["status"])

        top_supervisor_data = (
            query.group_by(VWOcorrenciasDetalhadas.supervisor)
            .order_by(func.count(VWOcorrenciasDetalhadas.id).desc())
            .first()
        )

        if top_supervisor_data and top_supervisor_data.supervisor:
            return top_supervisor_data.supervisor

        return "N/A"

    except Exception as e:
        logger.error(
            f"Erro ao calcular o supervisor com mais ocorrências: {e}", exc_info=True
        )
        return "Erro ao calcular"


def get_ronda_period_info(base_kpi_query, date_start_range, date_end_range) -> dict:
    """
    Calcula informações adicionais sobre o período de rondas para melhorar os KPIs.
    Retorna informações sobre a última data registrada e período real de dados.
    """
    try:
        from app.models import VWRondasDetalhadas
        # Busca a primeira e última data registrada no período
        primeira_data = base_kpi_query.with_entities(
            func.min(VWRondasDetalhadas.data_plantao_ronda)
        ).scalar()
        
        ultima_data = base_kpi_query.with_entities(
            func.max(VWRondasDetalhadas.data_plantao_ronda)
        ).scalar()
        
        # Calcula o período real de dados
        periodo_real_dias = 0
        if primeira_data and ultima_data:
            periodo_real_dias = (ultima_data - primeira_data).days + 1
        
        # Calcula quantos dias do período solicitado têm dados
        dias_com_dados = base_kpi_query.with_entities(
            func.count(func.distinct(VWRondasDetalhadas.data_plantao_ronda))
        ).scalar() or 0
        
        return {
            "primeira_data_registrada": primeira_data,
            "ultima_data_registrada": ultima_data,
            "periodo_real_dias": periodo_real_dias,
            "dias_com_dados": dias_com_dados,
            "periodo_solicitado_dias": (date_end_range - date_start_range).days + 1,
            "cobertura_periodo": round((dias_com_dados / ((date_end_range - date_start_range).days + 1)) * 100, 1) if (date_end_range - date_start_range).days > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular informações do período: {e}", exc_info=True)
        return {
            "primeira_data_registrada": None,
            "ultima_data_registrada": None,
            "periodo_real_dias": 0,
            "dias_com_dados": 0,
            "periodo_solicitado_dias": (date_end_range - date_start_range).days + 1,
            "cobertura_periodo": 0
        }


def get_ocorrencia_period_info(base_kpi_query, date_start_range, date_end_range) -> dict:
    """
    Calcula informações adicionais sobre o período de ocorrências para melhorar os KPIs.
    Retorna informações sobre a última data registrada e período real de dados.
    Garante que as datas nunca extrapolem o range filtrado.
    """
    try:
        from app.models import VWOcorrenciasDetalhadas
        # Busca a primeira e última data registrada no período (com fallback para o range filtrado)
        primeira_data = base_kpi_query.with_entities(
            func.min(VWOcorrenciasDetalhadas.data_hora_ocorrencia)
        ).scalar()
        ultima_data = base_kpi_query.with_entities(
            func.max(VWOcorrenciasDetalhadas.data_hora_ocorrencia)
        ).scalar()

        # Converter para date se for datetime
        if primeira_data and hasattr(primeira_data, 'date'):
            primeira_data_date = primeira_data.date()
        else:
            primeira_data_date = primeira_data
        if ultima_data and hasattr(ultima_data, 'date'):
            ultima_data_date = ultima_data.date()
        else:
            ultima_data_date = ultima_data

        # Limita as datas ao range filtrado
        if primeira_data_date:
            if primeira_data_date < date_start_range:
                primeira_data_date = date_start_range
            elif primeira_data_date > date_end_range:
                primeira_data_date = date_end_range
        else:
            primeira_data_date = date_start_range

        if ultima_data_date:
            if ultima_data_date > date_end_range:
                ultima_data_date = date_end_range
            elif ultima_data_date < date_start_range:
                ultima_data_date = date_start_range
        else:
            ultima_data_date = date_end_range

        # Calcula o período real de dados
        periodo_real_dias = 0
        if primeira_data_date and ultima_data_date:
            periodo_real_dias = (ultima_data_date - primeira_data_date).days + 1

        # Corrigir: contar dias distintos com ocorrências dentro do período filtrado, considerando o timezone America/Sao_Paulo
        dias_com_dados = (
            base_kpi_query.session.query(
                func.count(
                    func.distinct(
                        func.date(
                            VWOcorrenciasDetalhadas.data_hora_ocorrencia.op('AT TIME ZONE')('UTC').op('AT TIME ZONE')('America/Sao_Paulo')
                        )
                    )
                )
            )
            .filter(
                VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
                VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range
            )
            .scalar()
        ) or 0

        return {
            "primeira_data_registrada": primeira_data_date,
            "ultima_data_registrada": ultima_data_date,
            "periodo_real_dias": periodo_real_dias,
            "dias_com_dados": dias_com_dados,
            "periodo_solicitado_dias": (date_end_range - date_start_range).days + 1,
            "cobertura_periodo": round((dias_com_dados / ((date_end_range - date_start_range).days + 1)) * 100, 1) if (date_end_range - date_start_range).days > 0 else 0
        }

    except Exception as e:
        logger.error(f"Erro ao calcular informações do período de ocorrências: {e}", exc_info=True)
        return {
            "primeira_data_registrada": date_start_range,
            "ultima_data_registrada": date_end_range,
            "periodo_real_dias": 0,
            "dias_com_dados": 0,
            "periodo_solicitado_dias": (date_end_range - date_start_range).days + 1,
            "cobertura_periodo": 0
        }


def calculate_period_comparison(base_kpi_query, date_start_range, date_end_range) -> dict:
    """
    Calcula comparações com o período anterior para mostrar tendências nos KPIs.
    """
    try:
        from app.models import VWRondasDetalhadas
        # Calcula o período anterior (mesmo tamanho)
        periodo_dias = (date_end_range - date_start_range).days + 1
        anterior_start = date_start_range - timedelta(days=periodo_dias)
        anterior_end = date_start_range - timedelta(days=1)
        
        # Query para o período atual
        total_atual = base_kpi_query.with_entities(
            func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
        ).scalar()
        
        # Query para o período anterior
        total_anterior = db.session.query(
            func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
        ).filter(
            VWRondasDetalhadas.data_plantao_ronda >= anterior_start,
            VWRondasDetalhadas.data_plantao_ronda <= anterior_end
        ).scalar()
        
        # Calcula variação percentual
        if total_anterior > 0:
            variacao_percentual = round(((total_atual - total_anterior) / total_anterior) * 100, 1)
        else:
            variacao_percentual = 0 if total_atual == 0 else 100
        
        # Determina status baseado na variação
        if variacao_percentual > 10:
            status = "success"
            status_text = "Crescimento"
        elif variacao_percentual > -10:
            status = "warning"
            status_text = "Estável"
        else:
            status = "danger"
            status_text = "Queda"
        
        # Verifica se os dados estão atualizados (última data não é muito antiga)
        ultima_data = base_kpi_query.with_entities(
            func.max(VWRondasDetalhadas.data_plantao_ronda)
        ).scalar()
        
        dados_atualizados = True
        if ultima_data:
            dias_desde_ultima = (datetime.now().date() - ultima_data).days
            dados_atualizados = dias_desde_ultima <= 3  # Considera atualizado se não passou de 3 dias
        
        return {
            "total_atual": total_atual,
            "total_anterior": total_anterior,
            "variacao_percentual": variacao_percentual,
            "status": status,
            "status_text": status_text,
            "dados_atualizados": dados_atualizados,
            "ultima_atualizacao": ultima_data,
            "dias_desde_ultima": (datetime.now().date() - ultima_data).days if ultima_data else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular comparação de períodos: {e}", exc_info=True)
        return {
            "total_atual": 0,
            "total_anterior": 0,
            "variacao_percentual": 0,
            "status": "secondary",
            "status_text": "N/A",
            "dados_atualizados": False,
            "ultima_atualizacao": None,
            "dias_desde_ultima": None
        }

def calculate_ocorrencia_period_comparison(base_kpi_query, date_start_range, date_end_range) -> dict:
    """
    Calcula comparações com o período anterior para mostrar tendências nos KPIs de ocorrências.
    """
    try:
        from datetime import timedelta
        from app.models import VWOcorrenciasDetalhadas
        
        # Calcula o período anterior (mesmo tamanho)
        periodo_dias = (date_end_range - date_start_range).days + 1
        anterior_start = date_start_range - timedelta(days=periodo_dias)
        anterior_end = date_start_range - timedelta(days=1)
        
        # Query para o período atual
        total_atual = base_kpi_query.count()
        
        # Query para o período anterior
        total_anterior = db.session.query(VWOcorrenciasDetalhadas).filter(
            VWOcorrenciasDetalhadas.data_hora_ocorrencia >= anterior_start,
            VWOcorrenciasDetalhadas.data_hora_ocorrencia <= anterior_end
        ).count()
        
        # Calcula variação percentual
        if total_anterior > 0:
            variacao_percentual = round(((total_atual - total_anterior) / total_anterior) * 100, 1)
        else:
            variacao_percentual = 0 if total_atual == 0 else 100
        
        # Determina status baseado na variação (para ocorrências, menos é melhor)
        if variacao_percentual < -10:
            status = "success"
            status_text = "Redução"
        elif variacao_percentual < 10:
            status = "warning"
            status_text = "Estável"
        else:
            status = "danger"
            status_text = "Aumento"
        
        # Verifica se os dados estão atualizados (última data não é muito antiga)
        ultima_data = base_kpi_query.with_entities(
            func.max(VWOcorrenciasDetalhadas.data_hora_ocorrencia)
        ).scalar()
        
        dados_atualizados = True
        if ultima_data:
            dias_desde_ultima = (datetime.now().date() - ultima_data.date()).days
            dados_atualizados = dias_desde_ultima <= 3  # Considera atualizado se não passou de 3 dias
        
        return {
            "total_atual": total_atual,
            "total_anterior": total_anterior,
            "variacao_percentual": variacao_percentual,
            "status": status,
            "status_text": status_text,
            "dados_atualizados": dados_atualizados,
            "ultima_atualizacao": ultima_data,
            "dias_desde_ultima": (datetime.now().date() - ultima_data.date()).days if ultima_data else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular comparação de períodos de ocorrências: {e}", exc_info=True)
        return {
            "total_atual": 0,
            "total_anterior": 0,
            "variacao_percentual": 0,
            "status": "secondary",
            "status_text": "N/A",
            "dados_atualizados": False,
            "ultima_atualizacao": None,
            "dias_desde_ultima": None
        }
