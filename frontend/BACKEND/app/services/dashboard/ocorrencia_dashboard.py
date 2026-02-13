# app/services/dashboard/ocorrencia_dashboard.py
import logging
from datetime import datetime

from flask import current_app
from sqlalchemy import func

from app import db
from app.models import (Colaborador, Condominio, Ocorrencia, OcorrenciaTipo,
                        User, VWOcorrenciasDetalhadas, ocorrencia_colaboradores)
from app.services import ocorrencia_service
from app.utils.date_utils import parse_date_range

from .helpers import chart_data, date_utils
from .helpers import kpis as kpis_helper

logger = logging.getLogger(__name__)


def get_ocorrencia_dashboard_data(filters):
    """
    Busca e processa todos os dados necessários para o dashboard de ocorrências.
    """
    # 1. Preparação de Filtros
    data_inicio_str = filters.get("data_inicio_str")
    data_fim_str = filters.get("data_fim_str")
    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)

    # Sempre garantir o filtro de datas em todas as queries
    def add_date_filter(query):
        from datetime import time, timezone, datetime
        date_start_range_dt = datetime.combine(date_start_range, time.min, tzinfo=timezone.utc)
        date_end_range_dt = datetime.combine(date_end_range, time.max, tzinfo=timezone.utc)
        return query.filter(
            VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range_dt,
            VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range_dt
        )

    # 2. Query base para KPIs (com filtro de datas) - usando a view
    base_kpi_query = db.session.query(VWOcorrenciasDetalhadas)
    base_kpi_query = ocorrencia_service.apply_ocorrencia_filters(
        base_kpi_query, filters
    )
    base_kpi_query = add_date_filter(base_kpi_query)

    total_ocorrencias = base_kpi_query.count()
    logger.info(f"Total de ocorrências encontradas: {total_ocorrencias}")

    status_abertos = [
        'Registrada',
        'Em Andamento',
    ]
    ocorrencias_abertas = base_kpi_query.filter(
        VWOcorrenciasDetalhadas.status.in_(status_abertos)
    ).count()

    ocorrencias_por_tipo_q = db.session.query(
        VWOcorrenciasDetalhadas.tipo, func.count(VWOcorrenciasDetalhadas.id)
    ).filter(
        VWOcorrenciasDetalhadas.tipo.isnot(None),
        VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
        VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range
    )
    ocorrencias_por_tipo = (
        ocorrencias_por_tipo_q.group_by(VWOcorrenciasDetalhadas.tipo)
        .order_by(func.count(VWOcorrenciasDetalhadas.id).desc())
        .all()
    )
    tipo_labels = [item[0] for item in ocorrencias_por_tipo]
    ocorrencias_por_tipo_data = [item[1] for item in ocorrencias_por_tipo]
    tipo_mais_comum = tipo_labels[0] if tipo_labels else "N/A"

    ocorrencias_por_condominio_q = db.session.query(
        VWOcorrenciasDetalhadas.condominio, func.count(VWOcorrenciasDetalhadas.id)
    ).filter(
        VWOcorrenciasDetalhadas.condominio.isnot(None),
        VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
        VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range
    )
    ocorrencias_por_condominio = (
        ocorrencias_por_condominio_q.group_by(VWOcorrenciasDetalhadas.condominio)
        .order_by(func.count(VWOcorrenciasDetalhadas.id).desc())
        .all()
    )
    condominio_labels = [item[0] for item in ocorrencias_por_condominio]
    ocorrencias_por_condominio_data = [item[1] for item in ocorrencias_por_condominio]

    # --- DEBUG: Logs para evolução diária ---
    logger.info(f"Filtros aplicados: {filters}")

    # [NOVO] Evolução por turno diário (diurno e noturno) - Plantão 12x36
    from datetime import datetime, time
    import pytz
    
    # Obtém o timezone local da configuração
    local_tz_str = current_app.config.get("DEFAULT_TIMEZONE", "America/Sao_Paulo")
    local_tz = pytz.timezone(local_tz_str)
    
    # Query para ocorrências por turno e data
    ocorrencias_por_turno_dia_q = db.session.query(
        func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia),
        VWOcorrenciasDetalhadas.turno,
        func.count(VWOcorrenciasDetalhadas.id)
    ).filter(
        VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
        VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range,
        VWOcorrenciasDetalhadas.turno.isnot(None)
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        supervisor = User.query.get(filters["supervisor_id"])
        if supervisor:
            ocorrencias_por_turno_dia_q = ocorrencias_por_turno_dia_q.filter(
                VWOcorrenciasDetalhadas.supervisor == supervisor.username
            )
    if filters.get("condominio_id"):
        condominio = Condominio.query.get(filters["condominio_id"])
        if condominio:
            ocorrencias_por_turno_dia_q = ocorrencias_por_turno_dia_q.filter(
                VWOcorrenciasDetalhadas.condominio == condominio.nome
            )
    
    ocorrencias_por_turno_dia = (
        ocorrencias_por_turno_dia_q.group_by(
            func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia),
            VWOcorrenciasDetalhadas.turno
        )
        .order_by(func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia))
        .all()
    )

    logger.info(f"Dados de ocorrências por turno e dia: {ocorrencias_por_turno_dia}")

    # Processar dados para gráfico de barras empilhadas
    evolucao_date_labels, evolucao_diurno_data, evolucao_noturno_data = [], [], []
    
    if (date_end_range - date_start_range).days < 366:
        # Gerar labels de data
        evolucao_date_labels = date_utils.generate_date_labels(
            date_start_range, date_end_range
        )
        
        # Criar dicionário para organizar dados por data e turno
        dados_por_data = {}
        for data_str in evolucao_date_labels:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            dados_por_data[data_obj] = {"diurno": 0, "noturno": 0}
        
        # Preencher dados das ocorrências
        for data_ocorrencia, turno, count in ocorrencias_por_turno_dia:
            if data_ocorrencia in dados_por_data:
                # Normalizar nomes dos turnos
                turno_normalizado = turno.lower().strip()
                if "diurno" in turno_normalizado or "dia" in turno_normalizado:
                    dados_por_data[data_ocorrencia]["diurno"] += count
                elif "noturno" in turno_normalizado or "noite" in turno_normalizado:
                    dados_por_data[data_ocorrencia]["noturno"] += count
        
        # Preparar dados para o gráfico
        evolucao_total_data = []
        for data_str in evolucao_date_labels:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            total_dia = dados_por_data[data_obj]["diurno"] + dados_por_data[data_obj]["noturno"]
            evolucao_total_data.append(total_dia)
            evolucao_diurno_data.append(dados_por_data[data_obj]["diurno"])
            evolucao_noturno_data.append(dados_por_data[data_obj]["noturno"])

        logger.info(f"Labels de data gerados: {len(evolucao_date_labels)}")
        logger.info(f"Dados diurno: {evolucao_diurno_data[:5]}")
        logger.info(f"Dados noturno: {evolucao_noturno_data[:5]}")

    ultimas_ocorrencias_q = db.session.query(VWOcorrenciasDetalhadas).filter(
        VWOcorrenciasDetalhadas.data_hora_ocorrencia >= date_start_range,
        VWOcorrenciasDetalhadas.data_hora_ocorrencia <= date_end_range
    )
    
    # Aplicar filtros adicionais
    if filters.get("supervisor_id"):
        # Buscar o nome do supervisor pelo ID
        supervisor = User.query.get(filters["supervisor_id"])
        if supervisor:
            ultimas_ocorrencias_q = ultimas_ocorrencias_q.filter(
                VWOcorrenciasDetalhadas.supervisor == supervisor.username
            )
    if filters.get("condominio_id"):
        # Buscar o nome do condomínio pelo ID
        condominio = Condominio.query.get(filters["condominio_id"])
        if condominio:
            ultimas_ocorrencias_q = ultimas_ocorrencias_q.filter(
                VWOcorrenciasDetalhadas.condominio == condominio.nome
            )
    if filters.get("turno"):
        ultimas_ocorrencias_q = ultimas_ocorrencias_q.filter(
            VWOcorrenciasDetalhadas.turno == filters["turno"]
        )
    ultimas_ocorrencias = (
        ultimas_ocorrencias_q.order_by(VWOcorrenciasDetalhadas.data_hora_ocorrencia.desc())
        .limit(10)
        .all()
    )

    # Query para top colaboradores que ATENDERAM ocorrências (não quem registrou)
    top_colaboradores_q = db.session.query(
        Colaborador.nome_completo, 
        func.count(Ocorrencia.id).label("total_ocorrencias")
    ).join(
        ocorrencia_colaboradores, 
        Colaborador.id == ocorrencia_colaboradores.c.colaborador_id
    ).join(
        Ocorrencia, 
        ocorrencia_colaboradores.c.ocorrencia_id == Ocorrencia.id
    ).filter(
        Colaborador.nome_completo.isnot(None),
        Ocorrencia.data_hora_ocorrencia >= date_start_range,
        Ocorrencia.data_hora_ocorrencia <= date_end_range
    )
    
    # Aplicar filtros adicionais se necessário
    if filters.get("supervisor_id"):
        supervisor = User.query.get(filters["supervisor_id"])
        if supervisor:
            top_colaboradores_q = top_colaboradores_q.filter(
                Ocorrencia.supervisor_id == supervisor.id
            )
    if filters.get("condominio_id"):
        top_colaboradores_q = top_colaboradores_q.filter(
            Ocorrencia.condominio_id == filters["condominio_id"]
        )
    
    top_colaboradores_raw = (
        top_colaboradores_q.group_by(Colaborador.nome_completo)
        .order_by(func.count(Ocorrencia.id).desc())
        .limit(5)
        .all()
    )
    top_colaboradores_labels = [item[0] for item in top_colaboradores_raw]
    top_colaboradores_data = [item[1] for item in top_colaboradores_raw]

    # [ALTERADO] Lógica de busca do supervisor movida para o helper de KPIs
    supervisor_id_filter = filters.get("supervisor_id")
    if supervisor_id_filter:
        kpi_supervisor_label = "Supervisor Selecionado"
        supervisor = User.query.get(supervisor_id_filter)
        kpi_supervisor_name = supervisor.username if supervisor else "N/A"
    else:
        kpi_supervisor_label = "Supervisor com Mais Ocorrências"
        kpi_supervisor_name = kpis_helper.find_top_ocorrencia_supervisor(filters)

    # [NOVO] Informações adicionais sobre o período
    periodo_info = kpis_helper.get_ocorrencia_period_info(
        base_kpi_query, date_start_range, date_end_range
    )

    # [NOVO] Comparação com período anterior
    comparacao_periodo = kpis_helper.calculate_ocorrencia_period_comparison(
        base_kpi_query, date_start_range, date_end_range
    )

    # [NOVO] Tempo médio de resolução das ocorrências concluídas
    # Detecta se estamos usando a view ou a tabela
    is_view = hasattr(base_kpi_query.column_descriptions[0]['type'], '__tablename__') and \
              base_kpi_query.column_descriptions[0]['type'].__tablename__ == 'vw_ocorrencias_detalhadas'
    
    if is_view:
        # A view não tem data_modificacao, então não podemos calcular o tempo de resolução
        tempo_medio_resolucao_minutos = None
    else:
        # Usando a tabela original, podemos calcular o tempo de resolução
        ocorrencias_concluidas_q = base_kpi_query.filter(Ocorrencia.status == 'Concluída', Ocorrencia.data_modificacao.isnot(None))
        tempos_resolucao = [
            (o.data_modificacao - o.data_hora_ocorrencia).total_seconds() / 60.0
            for o in ocorrencias_concluidas_q.all()
            if o.data_modificacao and o.data_hora_ocorrencia and o.data_modificacao > o.data_hora_ocorrencia
        ]
        tempo_medio_resolucao_minutos = round(sum(tempos_resolucao) / len(tempos_resolucao), 1) if tempos_resolucao else None

    # [NOVO] Média diária de ocorrências
    dias_com_dados = periodo_info["dias_com_dados"] if periodo_info and "dias_com_dados" in periodo_info else 0
    if dias_com_dados > 0:
        media_diaria_ocorrencias = round(total_ocorrencias / dias_com_dados, 2)
    else:
        media_diaria_ocorrencias = None

    return {
        "total_ocorrencias": total_ocorrencias,
        "ocorrencias_abertas": ocorrencias_abertas,
        "tipo_mais_comum": tipo_mais_comum,
        "kpi_supervisor_label": kpi_supervisor_label,
        "kpi_supervisor_name": kpi_supervisor_name,
        "tipo_labels": tipo_labels,
        "ocorrencias_por_tipo_data": ocorrencias_por_tipo_data,
        "condominio_labels": condominio_labels,
        "ocorrencias_por_condominio_data": ocorrencias_por_condominio_data,
        "evolucao_date_labels": evolucao_date_labels,
        "evolucao_ocorrencia_data": evolucao_total_data,
        "ultimas_ocorrencias": ultimas_ocorrencias,
        "top_colaboradores_labels": top_colaboradores_labels,
        "top_colaboradores_data": top_colaboradores_data,
        "selected_data_inicio_str": date_start_range.strftime("%Y-%m-%d"),
        "selected_data_fim_str": date_end_range.strftime("%Y-%m-%d"),
        # [NOVO] Informações detalhadas sobre o período
        "periodo_info": periodo_info,
        "comparacao_periodo": comparacao_periodo,
        # [NOVO] Tempo médio de resolução
        "tempo_medio_resolucao_minutos": tempo_medio_resolucao_minutos,
        # [NOVO] Média diária de ocorrências
        "media_diaria_ocorrencias": media_diaria_ocorrencias,
    }
