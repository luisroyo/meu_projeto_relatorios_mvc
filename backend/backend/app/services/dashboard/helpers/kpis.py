
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


def get_ronda_period_info(base_kpi_query, date_start_range, date_end_range, supervisor_id=None) -> dict:
    """
    Calcula informações adicionais sobre o período de rondas para melhorar os KPIs.
    Retorna informações sobre a última data registrada e período real de dados.
    
    Se supervisor_id for fornecido, calcula apenas os dias trabalhados pelo supervisor
    considerando sua jornada 12x36 baseada na escala mensal.
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
        
        # [NOVO] Se supervisor_id for fornecido, calcula apenas os dias trabalhados
        if supervisor_id:
            dias_com_dados = _calculate_supervisor_working_days(
                supervisor_id, date_start_range, date_end_range
            )
        else:
            # Calcula quantos dias do período solicitado têm dados
            dias_com_dados = base_kpi_query.with_entities(
                func.count(func.distinct(VWRondasDetalhadas.data_plantao_ronda))
            ).scalar() or 0

        # [CORRIGIDO] Se supervisor_id for fornecido, ajusta o período solicitado para os dias trabalhados
        if supervisor_id:
            periodo_solicitado_dias = dias_com_dados
            cobertura_periodo = 100.0 if dias_com_dados > 0 else 0.0
        else:
            periodo_solicitado_dias = (date_end_range - date_start_range).days + 1
            cobertura_periodo = round((dias_com_dados / ((date_end_range - date_start_range).days + 1)) * 100, 1) if (date_end_range - date_start_range).days > 0 else 0
        
        return {
            "primeira_data_registrada": primeira_data,
            "ultima_data_registrada": ultima_data,
            "periodo_real_dias": periodo_real_dias,
            "dias_com_dados": dias_com_dados,
            "periodo_solicitado_dias": periodo_solicitado_dias,
            "cobertura_periodo": cobertura_periodo
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


def get_ocorrencia_period_info(base_kpi_query, date_start_range, date_end_range, supervisor_id=None) -> dict:
    """
    Calcula informações adicionais sobre o período de ocorrências para melhorar os KPIs.
    Retorna informações sobre a última data registrada e período real de dados.
    Garante que as datas nunca extrapolem o range filtrado.
    
    Se supervisor_id for fornecido, calcula apenas os dias trabalhados pelo supervisor
    considerando sua jornada 12x36 baseada na escala mensal.
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

        # [NOVO] Se supervisor_id for fornecido, calcula apenas os dias trabalhados
        if supervisor_id:
            dias_com_dados = _calculate_supervisor_working_days(
                supervisor_id, date_start_range, date_end_range
            )
        else:
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

        # [CORRIGIDO] Se supervisor_id for fornecido, ajusta o período solicitado para os dias trabalhados
        if supervisor_id:
            periodo_solicitado_dias = dias_com_dados
            cobertura_periodo = 100.0 if dias_com_dados > 0 else 0.0
        else:
            periodo_solicitado_dias = (date_end_range - date_start_range).days + 1
            cobertura_periodo = round((dias_com_dados / ((date_end_range - date_start_range).days + 1)) * 100, 1) if (date_end_range - date_start_range).days > 0 else 0

        return {
            "primeira_data_registrada": primeira_data_date,
            "ultima_data_registrada": ultima_data_date,
            "periodo_real_dias": periodo_real_dias,
            "dias_com_dados": dias_com_dados,
            "periodo_solicitado_dias": periodo_solicitado_dias,
            "cobertura_periodo": cobertura_periodo
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


def _calculate_supervisor_working_days(supervisor_id: int, date_start: datetime.date, date_end: datetime.date) -> int:
    """
    Calcula quantos dias um supervisor trabalhou em um período específico,
    considerando sua jornada 12x36 baseada na escala mensal.
    
    A jornada 12x36 significa:
    - Trabalha 12 horas por dia
    - Trabalha em dias alternados (par ou ímpar)
    - Trabalha em turnos alternados (diurno ou noturno)
    
    Args:
        supervisor_id: ID do supervisor
        date_start: Data de início do período
        date_end: Data de fim do período
    
    Returns:
        Número de dias trabalhados pelo supervisor no período
    """
    try:
        from app.models import EscalaMensal
        
        # [CORRIGIDO] Busca escalas do supervisor para todos os meses do período
        meses_anos = set()
        current_date = date_start
        while current_date <= date_end:
            meses_anos.add((current_date.year, current_date.month))
            # Avança para o próximo mês
            next_month_year = current_date.year + (
                current_date.month // 12
            )
            next_month = current_date.month % 12 + 1
            current_date = current_date.replace(
                year=next_month_year, month=next_month, day=1
            )
            if current_date > date_end:
                break
        
        escalas = EscalaMensal.query.filter(
            EscalaMensal.supervisor_id == supervisor_id,
            tuple_(EscalaMensal.ano, EscalaMensal.mes).in_(meses_anos)
        ).all()
        
        if not escalas:
            logger.warning(f"Supervisor {supervisor_id} não tem escala definida no período {date_start} a {date_end}")
            return 0
        
        # Mapeia os turnos para determinar quais dias da semana o supervisor trabalha
        turnos_supervisor = {escala.nome_turno for escala in escalas}
        
        # Calcula os dias trabalhados
        dias_trabalhados = 0
        current_date = date_start
        
        logger.info(f"Turnos do supervisor: {turnos_supervisor}")
        logger.info(f"Período analisado: {date_start} a {date_end}")
        
        while current_date <= date_end:
            # Verifica se o supervisor trabalha neste dia baseado na escala
            trabalha = _is_supervisor_working_day(current_date, turnos_supervisor)
            if trabalha:
                dias_trabalhados += 1
                logger.info(f"  {current_date.strftime('%d/%m/%Y')} (dia {'par' if current_date.day % 2 == 0 else 'ímpar'}): ✅ Trabalha")
            else:
                logger.info(f"  {current_date.strftime('%d/%m/%Y')} (dia {'par' if current_date.day % 2 == 0 else 'ímpar'}): ❌ Folga")
            
            current_date += timedelta(days=1)
        
        logger.info(f"Supervisor {supervisor_id} trabalhou {dias_trabalhados} dias no período {date_start} a {date_end}")
        return dias_trabalhados
        
    except Exception as e:
        logger.error(f"Erro ao calcular dias trabalhados do supervisor {supervisor_id}: {e}", exc_info=True)
        return 0


def _is_supervisor_working_day(date: datetime.date, turnos_supervisor: set) -> bool:
    """
    Determina se um supervisor trabalha em uma data específica baseado nos turnos da escala.
    
    A jornada 12x36 funciona da seguinte forma:
    - "Diurno Par": trabalha nos dias pares durante o dia (6h às 18h)
    - "Diurno Impar": trabalha nos dias ímpares durante o dia (6h às 18h)
    - "Noturno Par": trabalha nos dias pares durante a noite (18h às 6h)
    - "Noturno Impar": trabalha nos dias ímpares durante a noite (18h às 6h)
    
    Args:
        date: Data a verificar
        turnos_supervisor: Conjunto de turnos atribuídos ao supervisor
    
    Returns:
        True se o supervisor trabalha na data, False caso contrário
    """
    # Determina se o dia é par ou ímpar
    is_par = date.day % 2 == 0
    
    # Verifica se o supervisor tem escala para este tipo de dia
    # IMPORTANTE: O supervisor só trabalha se tiver escala EXATA para o tipo de dia
    if is_par:
        # Dia par - verifica se tem escala para dias pares (Diurno Par OU Noturno Par)
        return any("Par" in turno for turno in turnos_supervisor)
    else:
        # Dia ímpar - verifica se tem escala para dias ímpares (Diurno Impar OU Noturno Impar)
        return any("Impar" in turno for turno in turnos_supervisor)


def calculate_period_comparison(base_kpi_query, date_start_range, date_end_range, supervisor_id=None, filters=None) -> dict:
    """
    Calcula comparações com o período anterior para mostrar tendências nos KPIs.
    Se supervisor_id for fornecido, compara apenas as rondas desse supervisor.
    
    A comparação é feita com o período correspondente do mês anterior:
    - Se o período atual é 01/08 a 15/08, compara com 01/07 a 15/07
    - Se o período atual é 01/08 a 31/08, compara com 01/07 a 31/07
    - Se o período atual é 29/08 a 05/09, compara com 29/07 a 05/08
    """
    try:
        from app.models import VWRondasDetalhadas
        from datetime import timedelta
        
        # Calcula o período anterior correspondente (mesmo dia do mês anterior)
        # Exemplo: 01/08 a 15/08 -> 01/07 a 15/07
        # Exemplo: 29/08 a 05/09 -> 29/07 a 05/08
        
        # Calcula a diferença em dias entre start e end
        dias_diferenca = (date_end_range - date_start_range).days
        
        # Calcula o período anterior mantendo a mesma diferença de dias
        if date_start_range.month == 1:
            # Se estamos em janeiro, vai para dezembro do ano anterior
            anterior_start = date_start_range.replace(year=date_start_range.year - 1, month=12)
        else:
            anterior_start = date_start_range.replace(month=date_start_range.month - 1)
        
        # Calcula o final do período anterior mantendo a mesma diferença de dias
        anterior_end = anterior_start + timedelta(days=dias_diferenca)
        
        # Query para o período atual
        total_atual = base_kpi_query.with_entities(
            func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
        ).scalar()
        
        # Query para o período anterior - aplica os mesmos filtros do período atual
        anterior_query = db.session.query(
            func.coalesce(func.sum(VWRondasDetalhadas.total_rondas_no_log), 0)
        ).filter(
            VWRondasDetalhadas.data_plantao_ronda >= anterior_start,
            VWRondasDetalhadas.data_plantao_ronda <= anterior_end
        )
        
        # Aplica os mesmos filtros do período atual no período anterior
        if supervisor_id:
            anterior_query = anterior_query.filter(
                VWRondasDetalhadas.supervisor_id == supervisor_id
            )
        
        # Aplica filtros adicionais se fornecidos
        if filters:
            if filters.get("condominio_id"):
                anterior_query = anterior_query.filter(
                    VWRondasDetalhadas.condominio_id == filters["condominio_id"]
                )
            if filters.get("turno"):
                anterior_query = anterior_query.filter(
                    VWRondasDetalhadas.turno_ronda == filters["turno"]
                )
        
        total_anterior = anterior_query.scalar()
        
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

def calculate_ocorrencia_period_comparison(base_kpi_query, date_start_range, date_end_range, supervisor_id=None) -> dict:
    """
    Calcula comparações com o período anterior para mostrar tendências nos KPIs de ocorrências.
    Se supervisor_id for fornecido, compara apenas as ocorrências desse supervisor.
    
    A comparação é feita com o período correspondente do mês anterior:
    - Se o período atual é 01/08 a 15/08, compara com 01/07 a 15/07
    - Se o período atual é 01/08 a 31/08, compara com 01/07 a 31/07
    - Se o período atual é 29/08 a 05/09, compara com 29/07 a 05/08
    """
    try:
        from datetime import timedelta
        from app.models import VWOcorrenciasDetalhadas
        
        # Calcula o período anterior correspondente (mesmo dia do mês anterior)
        # Exemplo: 01/08 a 15/08 -> 01/07 a 15/07
        # Exemplo: 29/08 a 05/09 -> 29/07 a 05/08
        
        # Calcula a diferença em dias entre start e end
        dias_diferenca = (date_end_range - date_start_range).days
        
        # Calcula o período anterior mantendo a mesma diferença de dias
        if date_start_range.month == 1:
            # Se estamos em janeiro, vai para dezembro do ano anterior
            anterior_start = date_start_range.replace(year=date_start_range.year - 1, month=12)
        else:
            anterior_start = date_start_range.replace(month=date_start_range.month - 1)
        
        # Calcula o final do período anterior mantendo a mesma diferença de dias
        anterior_end = anterior_start + timedelta(days=dias_diferenca)
        
        # Query para o período atual
        total_atual = base_kpi_query.count()
        
        # Query para o período anterior - aplica os mesmos filtros do período atual
        anterior_query = db.session.query(VWOcorrenciasDetalhadas).filter(
            VWOcorrenciasDetalhadas.data_hora_ocorrencia >= anterior_start,
            VWOcorrenciasDetalhadas.data_hora_ocorrencia <= anterior_end
        )
        
        # Se um supervisor foi filtrado, aplica o mesmo filtro no período anterior
        if supervisor_id:
            # Busca o nome do supervisor para filtrar na view
            from app.models import User
            supervisor = User.query.get(supervisor_id)
            if supervisor:
                anterior_query = anterior_query.filter(
                    VWOcorrenciasDetalhadas.supervisor == supervisor.username
                )
        
        total_anterior = anterior_query.count()
        
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
