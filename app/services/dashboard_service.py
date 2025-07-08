# app/services/dashboard_service.py
from flask import flash
from sqlalchemy import func, cast, Float, tuple_
from datetime import datetime, timedelta, timezone

from app import db
from app.models import User, Ronda, Condominio, LoginHistory, ProcessingHistory, Ocorrencia, OcorrenciaTipo, EscalaMensal, Colaborador
from app.utils.date_utils import parse_date_range

def get_main_dashboard_data():
    """Busca e processa os dados para o dashboard principal de métricas."""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc).date()

    total_users = db.session.query(func.count(User.id)).scalar()
    total_approved_users = db.session.query(func.count(User.id)).filter_by(is_approved=True).scalar()
    total_pending_users = total_users - total_approved_users

    successful_logins = db.session.query(func.count(LoginHistory.id)).filter(LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == True).scalar()
    failed_logins = db.session.query(func.count(LoginHistory.id)).filter(LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == False).scalar()

    successful_reports = db.session.query(func.count(ProcessingHistory.id)).filter(ProcessingHistory.timestamp >= thirty_days_ago, ProcessingHistory.success == True).scalar()
    failed_reports = db.session.query(func.count(ProcessingHistory.id)).filter(ProcessingHistory.timestamp >= thirty_days_ago, ProcessingHistory.success == False).scalar()
    
    processing_by_type = db.session.query(
        ProcessingHistory.processing_type, 
        func.count(ProcessingHistory.id)
    ).filter(ProcessingHistory.timestamp >= thirty_days_ago).group_by(ProcessingHistory.processing_type).all()
    processing_types_data = {item[0]: item[1] for item in processing_by_type}

    logins_per_day = db.session.query(func.date(LoginHistory.timestamp), func.count(LoginHistory.id)).filter(LoginHistory.timestamp >= thirty_days_ago).group_by(func.date(LoginHistory.timestamp)).order_by(func.date(LoginHistory.timestamp)).all()
    processing_per_day = db.session.query(func.date(ProcessingHistory.timestamp), func.count(ProcessingHistory.id)).filter(ProcessingHistory.timestamp >= thirty_days_ago).group_by(func.date(ProcessingHistory.timestamp)).order_by(func.date(ProcessingHistory.timestamp)).all()

    date_labels = []
    current_date = thirty_days_ago.date()
    while current_date <= end_date:
        date_labels.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    logins_data_map = {str(date): count for date, count in logins_per_day}
    processing_data_map = {str(date): count for date, count in processing_per_day}
    logins_chart_data = [logins_data_map.get(label, 0) for label in date_labels]
    processing_chart_data = [processing_data_map.get(label, 0) for label in date_labels]
    
    return {
        'total_users': total_users, 'total_approved_users': total_approved_users,
        'total_pending_users': total_pending_users, 'successful_logins': successful_logins,
        'failed_logins': failed_logins, 'successful_reports': successful_reports,
        'failed_reports': failed_reports, 'processing_types_data': processing_types_data,
        'date_labels': date_labels, 'logins_chart_data': logins_chart_data,
        'processing_chart_data': processing_chart_data
    }


def get_ronda_dashboard_data(filters):
    """
    Busca e processa todos os dados necessários para o dashboard de rondas.
    """
    turno_filter = filters.get('turno')
    supervisor_id_filter = filters.get('supervisor_id')
    condominio_id_filter = filters.get('condominio_id')
    data_inicio_str = filters.get('data_inicio_str')
    data_fim_str = filters.get('data_fim_str')
    data_especifica_str = filters.get('data_especifica', '')
    
    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)

    def apply_filters(query):
        query = query.filter(Ronda.data_plantao_ronda.between(date_start_range, date_end_range))
        
        if turno_filter:
            query = query.filter(Ronda.turno_ronda == turno_filter)
        if supervisor_id_filter:
            query = query.filter(Ronda.supervisor_id == supervisor_id_filter)
        if condominio_id_filter:
            query = query.filter(Ronda.condominio_id == condominio_id_filter)
        return query

    rondas_por_condominio_q = db.session.query(Condominio.nome, func.sum(Ronda.total_rondas_no_log)).join(Ronda, Condominio.id == Ronda.condominio_id)
    rondas_por_condominio_q = apply_filters(rondas_por_condominio_q)
    rondas_por_condominio = rondas_por_condominio_q.group_by(Condominio.nome).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()
    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] or 0 for item in rondas_por_condominio]

    duracao_somas_q = db.session.query(
        Condominio.nome,
        func.sum(Ronda.duracao_total_rondas_minutos),
        func.sum(Ronda.total_rondas_no_log)
    ).join(Ronda, Condominio.id == Ronda.condominio_id)
    
    duracao_somas_q = apply_filters(duracao_somas_q)
    duracao_somas_raw = duracao_somas_q.group_by(Condominio.nome).all()

    dados_para_ordenar = []
    for nome, soma_duracao, soma_rondas in duracao_somas_raw:
        soma_duracao = soma_duracao or 0
        soma_rondas = soma_rondas or 0
        media = round(soma_duracao / soma_rondas, 2) if soma_rondas > 0 else 0
        dados_para_ordenar.append({'condominio': nome, 'media': media})

    dados_ordenados = sorted(dados_para_ordenar, key=lambda item: item['media'], reverse=True)
    duracao_condominio_labels = [item['condominio'] for item in dados_ordenados]
    duracao_media_data = [item['media'] for item in dados_ordenados]

    rondas_por_turno_q = db.session.query(Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)).filter(Ronda.turno_ronda.isnot(None), Ronda.total_rondas_no_log.isnot(None))
    rondas_por_turno_q = apply_filters(rondas_por_turno_q)
    rondas_por_turno = rondas_por_turno_q.group_by(Ronda.turno_ronda).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()
    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] or 0 for item in rondas_por_turno]
    
    rondas_por_supervisor_q = db.session.query(User.username, func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).outerjoin(Ronda, User.id == Ronda.supervisor_id).filter(User.is_supervisor == True)
    rondas_por_supervisor_q = apply_filters(rondas_por_supervisor_q)
    rondas_por_supervisor = rondas_por_supervisor_q.group_by(User.username).order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc()).all()
    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] for item in rondas_por_supervisor]

    rondas_por_dia_q = db.session.query(func.date(Ronda.data_plantao_ronda), func.sum(Ronda.total_rondas_no_log)).filter(Ronda.total_rondas_no_log.isnot(None))
    rondas_por_dia_q = apply_filters(rondas_por_dia_q)
    rondas_por_dia = rondas_por_dia_q.group_by(func.date(Ronda.data_plantao_ronda)).order_by(func.date(Ronda.data_plantao_ronda)).all()
    
    ronda_date_labels, ronda_activity_data = [], []
    if (date_end_range - date_start_range).days < 366:
        rondas_by_date_map = {str(date): count or 0 for date, count in rondas_por_dia}
        current_date = date_start_range
        while current_date <= date_end_range:
            date_str = current_date.strftime('%Y-%m-%d')
            ronda_date_labels.append(date_str)
            ronda_activity_data.append(rondas_by_date_map.get(date_str, 0))
            current_date += timedelta(days=1)

    dados_dia_detalhado = {'labels': [], 'data': []}
    dados_tabela_dia = []
    if data_especifica_str:
        try:
            data_selecionada = datetime.strptime(data_especifica_str, '%Y-%m-%d').date()
            rondas_por_turno_dia = db.session.query(Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)).filter(Ronda.data_plantao_ronda == data_selecionada, Ronda.turno_ronda.isnot(None)).group_by(Ronda.turno_ronda).order_by(Ronda.turno_ronda).all()
            dados_dia_detalhado['labels'] = [item[0] for item in rondas_por_turno_dia]
            dados_dia_detalhado['data'] = [item[1] or 0 for item in rondas_por_turno_dia]
            dados_tabela_dia = db.session.query(User.username, Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)).join(User, User.id == Ronda.supervisor_id).filter(Ronda.data_plantao_ronda == data_selecionada).group_by(User.username, Ronda.turno_ronda).order_by(User.username).all()
        except (ValueError, TypeError):
            flash('Data para análise detalhada em formato inválido.', 'warning')
            
    base_kpi_query = apply_filters(db.session.query(Ronda))
    total_rondas = base_kpi_query.with_entities(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).scalar()
    soma_duracao = base_kpi_query.with_entities(func.coalesce(func.sum(Ronda.duracao_total_rondas_minutos), 0)).scalar()
    duracao_media_geral = round(soma_duracao / total_rondas, 2) if total_rondas > 0 else 0
    supervisor_mais_ativo = supervisor_labels[0] if supervisor_labels else "N/A"

    # --- INÍCIO DA LÓGICA CORRIGIDA E MELHORADA PARA MÉDIA DE RONDAS/DIA ---
    num_dias_divisor = 0
    if supervisor_id_filter:
        # Lógica para contar os dias de trabalho de um supervisor específico
        meses_anos = set()
        current_date_for_months = date_start_range
        while current_date_for_months <= date_end_range:
            meses_anos.add((current_date_for_months.year, current_date_for_months.month))
            # Avança para o próximo mês
            next_month_year = current_date_for_months.year + (current_date_for_months.month // 12)
            next_month = current_date_for_months.month % 12 + 1
            current_date_for_months = current_date_for_months.replace(year=next_month_year, month=next_month, day=1)

        turnos_supervisor_db = db.session.query(EscalaMensal.nome_turno).filter(
            EscalaMensal.supervisor_id == supervisor_id_filter,
            tuple_(EscalaMensal.ano, EscalaMensal.mes).in_(meses_anos)
        ).distinct().all()
        turnos_do_supervisor = {turno[0] for turno in turnos_supervisor_db}
        
        if turnos_do_supervisor:
            current_day = date_start_range
            while current_day <= date_end_range:
                paridade = 'Par' if current_day.day % 2 == 0 else 'Impar'
                turno_diurno_do_dia = f"Diurno {paridade}"
                turno_noturno_do_dia = f"Noturno {paridade}"
                
                # Conta o dia se o supervisor trabalha em qualquer um dos turnos do dia (Diurno ou Noturno)
                if turno_diurno_do_dia in turnos_do_supervisor or turno_noturno_do_dia in turnos_do_supervisor:
                    num_dias_divisor += 1
                current_day += timedelta(days=1)
    
    elif turno_filter:
        # Lógica para contar os dias de um turno específico
        current_day = date_start_range
        while current_day <= date_end_range:
            paridade = 'Par' if current_day.day % 2 == 0 else 'Impar'
            if paridade in turno_filter:
                num_dias_divisor += 1
            current_day += timedelta(days=1)
    
    else:
        # Lógica padrão: todos os dias no período
        num_dias_divisor = (date_end_range - date_start_range).days + 1
    
    media_rondas_dia = round(total_rondas / num_dias_divisor, 1) if num_dias_divisor > 0 else 0
    # --- FIM DA LÓGICA CORRIGIDA ---


    return {
        'total_rondas': total_rondas,
        'duracao_media_geral': duracao_media_geral,
        'supervisor_mais_ativo': supervisor_mais_ativo,
        'media_rondas_dia': media_rondas_dia,
        'condominio_labels': condominio_labels, 
        'rondas_por_condominio_data': rondas_por_condominio_data,
        'duracao_condominio_labels': duracao_condominio_labels, 
        'duracao_media_data': duracao_media_data,
        'turno_labels': turno_labels, 
        'rondas_por_turno_data': rondas_por_turno_data,
        'supervisor_labels': supervisor_labels, 
        'rondas_por_supervisor_data': rondas_por_supervisor_data,
        'ronda_date_labels': ronda_date_labels, 
        'ronda_activity_data': ronda_activity_data,
        'dados_dia_detalhado': dados_dia_detalhado, 
        'dados_tabela_dia': dados_tabela_dia,
        'selected_data_inicio_str': date_start_range.strftime('%Y-%m-%d'), 
        'selected_data_fim_str': date_end_range.strftime('%Y-%m-%d') 
    }


def get_ocorrencia_dashboard_data(filters):
    """
    Busca e processa todos os dados necessários para o dashboard de ocorrências.
    """
    condominio_id_filter = filters.get('condominio_id')
    tipo_id_filter = filters.get('tipo_id')
    status_filter = filters.get('status')
    supervisor_id_filter = filters.get('supervisor_id')
    data_inicio_str = filters.get('data_inicio_str')
    data_fim_str = filters.get('data_fim_str')

    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)

    def apply_ocorrencia_filters(query):
        if condominio_id_filter:
            query = query.filter(Ocorrencia.condominio_id == condominio_id_filter)
        if tipo_id_filter:
            query = query.filter(Ocorrencia.ocorrencia_tipo_id == tipo_id_filter)
        if status_filter:
            query = query.filter(Ocorrencia.status == status_filter)
        if supervisor_id_filter: 
            query = query.filter(Ocorrencia.supervisor_id == supervisor_id_filter)
        
        query = query.filter(Ocorrencia.data_hora_ocorrencia >= date_start_range)
        query = query.filter(Ocorrencia.data_hora_ocorrencia < date_end_range + timedelta(days=1))
        return query

    base_kpi_query = db.session.query(Ocorrencia)
    total_ocorrencias = apply_ocorrencia_filters(base_kpi_query).count()
    
    abertas_kpi_query = base_kpi_query.filter(Ocorrencia.status.in_(['Registrada', 'Em Andamento']))
    ocorrencias_abertas = apply_ocorrencia_filters(abertas_kpi_query).count()

    ocorrencias_por_tipo_q = db.session.query(OcorrenciaTipo.nome, func.count(Ocorrencia.id)).join(Ocorrencia, OcorrenciaTipo.id == Ocorrencia.ocorrencia_tipo_id)
    ocorrencias_por_tipo_q = apply_ocorrencia_filters(ocorrencias_por_tipo_q)
    ocorrencias_por_tipo = ocorrencias_por_tipo_q.group_by(OcorrenciaTipo.nome).order_by(func.count(Ocorrencia.id).desc()).all()
    tipo_labels = [item[0] for item in ocorrencias_por_tipo]
    ocorrencias_por_tipo_data = [item[1] for item in ocorrencias_por_tipo]
    tipo_mais_comum = tipo_labels[0] if tipo_labels else "N/A"

    ocorrencias_por_condominio_q = db.session.query(Condominio.nome, func.count(Ocorrencia.id)).join(Ocorrencia, Condominio.id == Ocorrencia.condominio_id)
    ocorrencias_por_condominio_q = apply_ocorrencia_filters(ocorrencias_por_condominio_q)
    ocorrencias_por_condominio = ocorrencias_por_condominio_q.group_by(Condominio.nome).order_by(func.count(Ocorrencia.id).desc()).all()
    
    condominio_labels = [item[0] for item in ocorrencias_por_condominio]
    ocorrencias_por_condominio_data = [item[1] for item in ocorrencias_por_condominio]
    
    ocorrencias_por_dia_q = db.session.query(
        func.date(Ocorrencia.data_hora_ocorrencia), 
        func.count(Ocorrencia.id)
    )
    ocorrencias_por_dia_q = apply_ocorrencia_filters(ocorrencias_por_dia_q)
    ocorrencias_por_dia = ocorrencias_por_dia_q.group_by(func.date(Ocorrencia.data_hora_ocorrencia)).order_by(func.date(Ocorrencia.data_hora_ocorrencia)).all()

    evolucao_date_labels, evolucao_ocorrencia_data = [], []
    if (date_end_range - date_start_range).days < 366:
        ocorrencias_map = {str(date): count for date, count in ocorrencias_por_dia}
        current_date = date_start_range
        while current_date <= date_end_range:
            date_str = current_date.strftime('%Y-%m-%d')
            evolucao_date_labels.append(date_str)
            evolucao_ocorrencia_data.append(ocorrencias_map.get(date_str, 0))
            current_date += timedelta(days=1)
            
    ultimas_ocorrencias_q = db.session.query(Ocorrencia).join(
        Condominio, Ocorrencia.condominio_id == Condominio.id
    ).join(
        OcorrenciaTipo, Ocorrencia.ocorrencia_tipo_id == OcorrenciaTipo.id
    ).outerjoin(
        User, Ocorrencia.supervisor_id == User.id
    )
    ultimas_ocorrencias_q = apply_ocorrencia_filters(ultimas_ocorrencias_q)
    ultimas_ocorrencias = ultimas_ocorrencias_q.order_by(Ocorrencia.data_hora_ocorrencia.desc()).limit(10).all()

    top_colaboradores_q = db.session.query(
        Colaborador.nome_completo,
        func.count(Ocorrencia.id).label('total_ocorrencias')
    ).join(Ocorrencia.colaboradores_envolvidos)

    top_colaboradores_q = apply_ocorrencia_filters(top_colaboradores_q)

    top_colaboradores_raw = top_colaboradores_q.group_by(Colaborador.nome_completo).order_by(func.count(Ocorrencia.id).desc()).limit(5).all()

    top_colaboradores_labels = [item[0] for item in top_colaboradores_raw]
    top_colaboradores_data = [item[1] for item in top_colaboradores_raw]

    return {
        'total_ocorrencias': total_ocorrencias,
        'ocorrencias_abertas': ocorrencias_abertas,
        'tipo_mais_comum': tipo_mais_comum,
        'tipo_labels': tipo_labels,
        'ocorrencias_por_tipo_data': ocorrencias_por_tipo_data,
        'condominio_labels': condominio_labels,
        'ocorrencias_por_condominio_data': ocorrencias_por_condominio_data,
        'evolucao_date_labels': evolucao_date_labels,
        'evolucao_ocorrencia_data': evolucao_ocorrencia_data,
        'ultimas_ocorrencias': ultimas_ocorrencias,
        'top_colaboradores_labels': top_colaboradores_labels,
        'top_colaboradores_data': top_colaboradores_data,
        'selected_data_inicio_str': date_start_range.strftime('%Y-%m-%d'),
        'selected_data_fim_str': date_end_range.strftime('%Y-%m-%d')
    }