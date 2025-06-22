# app/services/dashboard_service.py
from flask import flash
from sqlalchemy import func, and_, or_, cast, Float, case # Importar 'or_' para combinar condições
from datetime import datetime, timedelta, timezone

from app import db
from app.models import User, Ronda, Condominio, LoginHistory, ProcessingHistory

def get_main_dashboard_data():
    """Busca e processa os dados para o dashboard principal de métricas."""
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
        'total_users': total_users,
        'total_approved_users': total_approved_users,
        'total_pending_users': total_pending_users,
        'successful_logins': successful_logins,
        'failed_logins': failed_logins,
        'successful_reports': successful_reports,
        'failed_reports': failed_reports,
        'processing_types_data': processing_types_data,
        'date_labels': date_labels,
        'logins_chart_data': logins_chart_data,
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

    # ... (consultas existentes para os gráficos principais) ...
    rondas_por_condominio_q = db.session.query(Condominio.nome, func.sum(Ronda.total_rondas_no_log)).outerjoin(Ronda, Condominio.id == Ronda.condominio_id) #
    rondas_por_condominio_q = apply_filters(rondas_por_condominio_q)
    rondas_por_condominio = rondas_por_condominio_q.group_by(Condominio.nome).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()
    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] if item[1] is not None else 0 for item in rondas_por_condominio]

    media_expression = cast(func.coalesce(func.sum(Ronda.duracao_total_rondas_minutos), 0), Float) / cast(func.coalesce(func.sum(Ronda.total_rondas_no_log), 1), Float) #
    duracao_media_q = db.session.query(Condominio.nome, media_expression).outerjoin(Ronda, Ronda.condominio_id == Condominio.id)
    duracao_media_q = apply_filters(duracao_media_q)
    duracao_media_por_condominio_raw = duracao_media_q.group_by(Condominio.nome).order_by(media_expression.desc()).all()
    duracao_condominio_labels = [item[0] for item in duracao_media_por_condominio_raw]
    duracao_media_data = [round(item[1], 2) if item[1] is not None else 0 for item in duracao_media_por_condominio_raw]

    rondas_por_turno_q = db.session.query(Ronda.turno_ronda, func.sum(Ronda.total_rondas_no_log)) #
    rondas_por_turno_q = apply_filters(rondas_por_turno_q)
    rondas_por_turno = rondas_por_turno_q.filter(Ronda.turno_ronda.isnot(None), Ronda.total_rondas_no_log.isnot(None)).group_by(Ronda.turno_ronda).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all() #
    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] if item[1] is not None else 0 for item in rondas_por_turno]

    rondas_por_supervisor_q = db.session.query(User.username, func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).outerjoin(Ronda, User.id == Ronda.supervisor_id).filter(User.is_supervisor == True) #
    rondas_por_supervisor_q = apply_filters(rondas_por_supervisor_q)
    rondas_por_supervisor = rondas_por_supervisor_q.group_by(User.username).order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc()).all() #
    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] for item in rondas_por_supervisor]

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    rondas_por_dia_q = db.session.query(func.date(Ronda.data_plantao_ronda), func.sum(Ronda.total_rondas_no_log)) #
    rondas_por_dia_q = apply_filters(rondas_por_dia_q).filter(Ronda.total_rondas_no_log.isnot(None)) #
    rondas_por_dia = rondas_por_dia_q.group_by(func.date(Ronda.data_plantao_ronda)).order_by(func.date(Ronda.data_plantao_ronda)).all() #
    
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


    # ---- INÍCIO DO NOVO CÓDIGO PARA ANÁLISE DETALHADA ----
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
    # ---- FIM DO NOVO CÓDIGO ----

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

def get_supervisor_ronda_quality_ranking(filters=None):
    """
    Calcula e retorna um ranking de supervisores com base na qualidade das rondas supervisionadas.
    A "qualidade" é medida pelo percentual de rondas incompletas ou com duração anômala.
    """
    if filters is None:
        filters = {}

    # Define a função interna para aplicar filtros à query
    def apply_quality_filters(query):
        turno_filter = filters.get('turno')
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
            flash("Formato de data inválido para filtros de qualidade. Use AAAA-MM-DD.", "danger")
        
        if turno_filter:
            query = query.filter(Ronda.turno_ronda == turno_filter)
        if condominio_id_filter:
            query = query.filter(Ronda.condominio_id == condominio_id_filter)
        if data_inicio:
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio)
        if data_fim:
            query = query.filter(Ronda.data_plantao_ronda <= data_fim)
        
        return query

    # Subconsulta para contar rondas problemáticas (incompletas OU anômalas)
    problematic_rondas_subquery = db.session.query(
        Ronda.supervisor_id,
        func.count(Ronda.id).label('total_rondas'),
        func.sum(case((Ronda.is_incomplete == True, 1), else_=0)).label('incompletas_count'),
        func.sum(case((Ronda.is_duration_anomalous == True, 1), else_=0)).label('anomalas_duracao_count')
    ).filter(Ronda.supervisor_id.isnot(None)) # Apenas rondas com supervisor atribuído
    
    # Aplica os mesmos filtros que o dashboard geral se fornecidos
    problematic_rondas_subquery = apply_quality_filters(problematic_rondas_subquery)
    
    problematic_rondas_subquery = problematic_rondas_subquery.group_by(Ronda.supervisor_id).subquery()

    # Consulta principal para unir com os dados do supervisor e calcular o ranking
    ranking_query = db.session.query(
        User.username,
        problematic_rondas_subquery.c.total_rondas,
        problematic_rondas_subquery.c.incompletas_count,
        problematic_rondas_subquery.c.anomalas_duracao_count,
        # Calcula o total de rondas problematicas para o ranking (qualquer uma das flags)
        (problematic_rondas_subquery.c.incompletas_count + problematic_rondas_subquery.c.anomalas_duracao_count).label('total_problematicas'),
        # Calcula o percentual de rondas problematicas, evitando divisão por zero
        case(
            (problematic_rondas_subquery.c.total_rondas > 0, 
             cast((problematic_rondas_subquery.c.incompletas_count + problematic_rondas_subquery.c.anomalas_duracao_count), Float) / 
             cast(problematic_rondas_subquery.c.total_rondas, Float) * 100
            ),
            else_=0
        ).label('percentual_problematicas')
    ).join(User, User.id == problematic_rondas_subquery.c.supervisor_id).filter(User.is_supervisor == True)

    # Ordena pelo percentual de problematicas (menor é melhor), depois pelo total de rondas (mais rondas é melhor em caso de empate)
    ranking_query = ranking_query.order_by(
        'percentual_problematicas',
        problematic_rondas_subquery.c.total_rondas.desc()
    )

    ranking_data_raw = ranking_query.all()

    # Formata os resultados
    ranking_final = []
    for rank in ranking_data_raw:
        ranking_final.append({
            'supervisor_nome': rank.username,
            'total_rondas': rank.total_rondas,
            'rondas_incompletas': rank.incompletas_count,
            'rondas_anomalas_duracao': rank.anomalas_duracao_count,
            'total_rondas_problematicas': rank.total_problematicas,
            'percentual_problematicas': round(rank.percentual_problematicas, 2)
        })

    return ranking_final

def get_ronda_anomalies_report(filters=None):
    """
    Busca rondas que apresentam anomalias: não encerradas, incompletas ou com duração anômala.
    """
    if filters is None:
        filters = {}

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
        # Flash message handled by the caller if this is part of a web request
        pass # Or logger.warning("Invalid date format for anomaly report filters.")

    query = Ronda.query.options(db.joinedload(Ronda.condominio_obj), db.joinedload(Ronda.criador), db.joinedload(Ronda.supervisor))

    # Aplica os filtros gerais
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

    # Filtra por anomalias:
    # 1. Rondas iniciadas e não encerradas (data_hora_fim é nula)
    # 2. Rondas marcadas como incompletas
    # 3. Rondas marcadas com duração anômala
    query = query.filter(
        or_(
            Ronda.data_hora_fim.is_(None),
            Ronda.is_incomplete == True,
            Ronda.is_duration_anomalous == True
        )
    )

    # Ordena para melhor visualização no relatório
    query = query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.data_hora_inicio.desc())

    # Retorna os objetos Ronda encontrados
    return query.all()