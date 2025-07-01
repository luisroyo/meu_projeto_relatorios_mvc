# app/services/dashboard_service.py
from flask import flash
from sqlalchemy import func, and_, cast, Float
from datetime import datetime, timedelta, timezone

from app import db
from app.models import User, Ronda, Condominio, LoginHistory, ProcessingHistory

def get_main_dashboard_data():
    """Busca e processa os dados para o dashboard principal de métricas."""
    # (código original sem alterações)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    total_users = db.session.query(User).count()
    total_approved_users = db.session.query(User).filter_by(is_approved=True).count()
    total_pending_users = total_users - total_approved_users
    successful_logins = db.session.query(LoginHistory).filter(LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == True).count()
    failed_logins = db.session.query(LoginHistory).filter(LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == False).count()
    successful_reports = db.session.query(ProcessingHistory).filter(ProcessingHistory.timestamp >= thirty_days_ago, ProcessingHistory.success == True).count()
    failed_reports = db.session.query(ProcessingHistory).filter(ProcessingHistory.timestamp >= thirty_days_ago, ProcessingHistory.success == False).count()
    processing_by_type = db.session.query(ProcessingHistory.processing_type, func.count(ProcessingHistory.id)).filter(ProcessingHistory.timestamp >= thirty_days_ago).group_by(ProcessingHistory.processing_type).all()
    processing_types_data = {item[0]: item[1] for item in processing_by_type}
    logins_per_day = db.session.query(func.date(LoginHistory.timestamp), func.count(LoginHistory.id)).filter(LoginHistory.timestamp >= thirty_days_ago).group_by(func.date(LoginHistory.timestamp)).order_by(func.date(LoginHistory.timestamp)).all()
    processing_per_day = db.session.query(func.date(ProcessingHistory.timestamp), func.count(ProcessingHistory.id)).filter(ProcessingHistory.timestamp >= thirty_days_ago).group_by(func.date(ProcessingHistory.timestamp)).order_by(func.date(ProcessingHistory.timestamp)).all()
    date_labels = []
    current_date = thirty_days_ago.date()
    end_date = datetime.now(timezone.utc).date()
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
    'filters' é um dicionário contendo os filtros da requisição.
    """
    turno_filter = filters.get('turno')
    supervisor_id_filter = filters.get('supervisor_id')
    condominio_id_filter = filters.get('condominio_id')
    data_inicio_str = filters.get('data_inicio_str')
    data_fim_str = filters.get('data_fim_str')

    data_inicio, data_fim = None, None
    try:
        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Formato de data inválido. Use AAAA-MM-DD.", "danger")

    def apply_filters(query):
        if turno_filter:
            query = query.filter(Ronda.turno_ronda == turno_filter)
        if supervisor_id_filter:
            query = query.filter(Ronda.supervisor_id == supervisor_id_filter)
        if condominio_id_filter:
            query = query.filter(Ronda.condominio_id == condominio_id_filter)
        if data_inicio:
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio)
        if data_fim:
            query = query.filter(Ronda.data_plantao_ronda <= data_fim)
        return query

    # CORREÇÃO 1: Trocado .outerjoin() por .join() para mostrar apenas condomínios com rondas.
    rondas_por_condominio_q = db.session.query(
        Condominio.nome, 
        func.sum(Ronda.total_rondas_no_log)
    ).join(Ronda, Condominio.id == Ronda.condominio_id) # <-- CORRIGIDO
    
    rondas_por_condominio_q = apply_filters(rondas_por_condominio_q)
    rondas_por_condominio = rondas_por_condominio_q.group_by(Condominio.nome).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()
    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] if item[1] is not None else 0 for item in rondas_por_condominio]

    media_expression = cast(func.coalesce(func.sum(Ronda.duracao_total_rondas_minutos), 0), Float) / cast(func.coalesce(func.sum(Ronda.total_rondas_no_log), 1), Float)
    
    # CORREÇÃO 2: Trocado .outerjoin() por .join() aqui também.
    duracao_media_q = db.session.query(
        Condominio.nome, 
        media_expression
    ).join(Ronda, Ronda.condominio_id == Condominio.id) # <-- CORRIGIDO

    duracao_media_q = apply_filters(duracao_media_q)
    duracao_media_por_condominio_raw = duracao_media_q.group_by(Condominio.nome).order_by(media_expression.desc()).all()
    duracao_condominio_labels = [item[0] for item in duracao_media_por_condominio_raw]
    duracao_media_data = [round(item[1], 2) if item[1] is not None else 0 for item in duracao_media_por_condominio_raw]

    rondas_por_turno_q = db.session.query(Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log))
    rondas_por_turno_q = apply_filters(rondas_por_turno_q)
    rondas_por_turno = rondas_por_turno_q.filter(Ronda.turno_ronda.isnot(None), Ronda.total_rondas_no_log.isnot(None)).group_by(Ronda.turno_ronda).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()
    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] if item[1] is not None else 0 for item in rondas_por_turno]
    
    # Esta consulta já estava correta, pois o .outerjoin() é da perspectiva do User, o que é desejado.
    rondas_por_supervisor_q = db.session.query(User.username, func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).outerjoin(Ronda, User.id == Ronda.supervisor_id).filter(User.is_supervisor == True)
    rondas_por_supervisor_q = apply_filters(rondas_por_supervisor_q)
    rondas_por_supervisor = rondas_por_supervisor_q.group_by(User.username).order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc()).all()
    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] for item in rondas_por_supervisor]

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    rondas_por_dia_q = db.session.query(func.date(Ronda.data_plantao_ronda), func.sum(Ronda.total_rondas_no_log))
    rondas_por_dia_q = apply_filters(rondas_por_dia_q).filter(Ronda.total_rondas_no_log.isnot(None))
    rondas_por_dia = rondas_por_dia_q.group_by(func.date(Ronda.data_plantao_ronda)).order_by(func.date(Ronda.data_plantao_ronda)).all()
    
    date_start_range = data_inicio if data_inicio else thirty_days_ago.date()
    date_end_range = data_fim if data_fim else datetime.now(timezone.utc).date()
    ronda_date_labels, ronda_activity_data, rondas_by_date_map = [], [], {}
    current_date = date_start_range
    rondas_by_date_map = {str(date): count if count is not None else 0 for date, count in rondas_por_dia}
    if (date_end_range - current_date).days < 366:
        while current_date <= date_end_range:
            date_str = current_date.strftime('%Y-%m-%d')
            ronda_date_labels.append(date_str)
            ronda_activity_data.append(rondas_by_date_map.get(date_str, 0))
            current_date += timedelta(days=1)

    data_especifica_str = filters.get('data_especifica')
    dados_dia_detalhado = {'labels': [], 'data': []}
    dados_tabela_dia = []

    if data_especifica_str:
        try:
            data_selecionada = datetime.strptime(data_especifica_str, '%Y-%m-%d').date()
            
            rondas_por_turno_dia = db.session.query(
                Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)
            ).filter(
                Ronda.data_plantao_ronda == data_selecionada,
                Ronda.turno_ronda.isnot(None)
            ).group_by(Ronda.turno_ronda).order_by(Ronda.turno_ronda).all()
            
            dados_dia_detalhado['labels'] = [item[0] for item in rondas_por_turno_dia]
            dados_dia_detalhado['data'] = [item[1] or 0 for item in rondas_por_turno_dia]

            dados_tabela_dia = db.session.query(
                User.username,
                Ronda.turno_ronda,
                func.sum(Ronda.total_rondas_no_log)
            ).join(User, User.id == Ronda.supervisor_id).filter(
                Ronda.data_plantao_ronda == data_selecionada
            ).group_by(User.username, Ronda.turno_ronda).order_by(User.username).all()

        except (ValueError, TypeError):
            flash('Data para análise detalhada em formato inválido.', 'warning')

    return {
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
    }