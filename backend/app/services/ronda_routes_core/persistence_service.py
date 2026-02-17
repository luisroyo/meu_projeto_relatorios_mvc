from app import db
from app.models import Ronda, Condominio, User
from app.models.vw_rondas_detalhadas import VWRondasDetalhadas
from sqlalchemy.orm import joinedload
from sqlalchemy import func

def get_ronda_by_id(ronda_id):
    # Para detalhes, ainda usamos a tabela original pois precisamos das relações
    return Ronda.query.options(joinedload(Ronda.condominio), joinedload(Ronda.supervisor)).get_or_404(ronda_id)

def delete_ronda(ronda):
    db.session.delete(ronda)
    db.session.commit()

def save_ronda(ronda):
    db.session.add(ronda)
    db.session.commit()

def update_ronda():
    db.session.commit()

def list_rondas(query, page=1, per_page=10):
    return query.order_by(VWRondasDetalhadas.data_plantao_ronda.desc(), VWRondasDetalhadas.id.desc()).paginate(page=page, per_page=per_page)

def build_ronda_query(filters):
    query = VWRondasDetalhadas.query
    if filters.get("condominio"):
        query = query.filter(VWRondasDetalhadas.condominio_nome == filters["condominio"])
    if filters.get("supervisor"):
        query = query.filter(VWRondasDetalhadas.supervisor_id == filters["supervisor"])
    if filters.get("turno"):
        query = query.filter(VWRondasDetalhadas.turno_ronda == filters["turno"])
    if filters.get("data_inicio"):
        from datetime import date
        try:
            data_inicio_obj = date.fromisoformat(filters["data_inicio"])
            query = query.filter(VWRondasDetalhadas.data_plantao_ronda >= data_inicio_obj)
        except (ValueError, TypeError):
            pass
    if filters.get("data_fim"):
        from datetime import date
        try:
            data_fim_obj = date.fromisoformat(filters["data_fim"])
            query = query.filter(VWRondasDetalhadas.data_plantao_ronda <= data_fim_obj)
        except (ValueError, TypeError):
            pass
    return query

def get_ronda_stats(query):
    total_rondas = query.with_entities(func.sum(VWRondasDetalhadas.total_rondas_no_log)).scalar() or 0
    soma_duracao = query.with_entities(func.sum(VWRondasDetalhadas.duracao_total_rondas_minutos)).scalar() or 0
    return total_rondas, soma_duracao

def get_top_supervisor(query):
    top_supervisor_q = (
        query.group_by(VWRondasDetalhadas.supervisor_username)
        .with_entities(VWRondasDetalhadas.supervisor_username, func.sum(VWRondasDetalhadas.total_rondas_no_log))
        .order_by(func.sum(VWRondasDetalhadas.total_rondas_no_log).desc())
        .first()
    )
    return top_supervisor_q[0] if top_supervisor_q else "N/A" 