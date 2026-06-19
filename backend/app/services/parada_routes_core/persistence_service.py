from app import db
from app.models.parada import Parada
from app.models.condominio import Condominio
from app.models.user import User
from sqlalchemy.orm import joinedload
from sqlalchemy import func

def get_parada_by_id(parada_id):
    return Parada.query.options(joinedload(Parada.condominio), joinedload(Parada.supervisor)).get_or_404(parada_id)

def delete_parada(parada):
    db.session.delete(parada)
    db.session.commit()

def save_parada(parada):
    db.session.add(parada)
    db.session.commit()

def update_parada():
    db.session.commit()

def list_paradas(query, page=1, per_page=10):
    return query.order_by(Parada.data_plantao_parada.desc(), Parada.id.desc()).paginate(page=page, per_page=per_page)

def build_parada_query(filters):
    query = Parada.query.options(joinedload(Parada.condominio), joinedload(Parada.supervisor))
    if filters.get("condominio"):
        query = query.join(Parada.condominio).filter(Condominio.nome == filters["condominio"])
    if filters.get("supervisor"):
        query = query.filter(Parada.supervisor_id == filters["supervisor"])
    if filters.get("turno"):
        query = query.filter(Parada.turno_parada == filters["turno"])
    if filters.get("data_inicio"):
        from datetime import date
        try:
            data_inicio_obj = date.fromisoformat(filters["data_inicio"])
            query = query.filter(Parada.data_plantao_parada >= data_inicio_obj)
        except (ValueError, TypeError):
            pass
    if filters.get("data_fim"):
        from datetime import date
        try:
            data_fim_obj = date.fromisoformat(filters["data_fim"])
            query = query.filter(Parada.data_plantao_parada <= data_fim_obj)
        except (ValueError, TypeError):
            pass
    return query

def get_parada_stats(query):
    total_paradas = query.with_entities(func.sum(Parada.total_paradas_no_log)).scalar() or 0
    soma_duracao = query.with_entities(func.sum(Parada.duracao_total_paradas_minutos)).scalar() or 0
    return total_paradas, soma_duracao

def get_top_supervisor(query):
    # Precisamos do join com User para pegar o username do supervisor
    top_supervisor_q = (
        db.session.query(User.username, func.sum(Parada.total_paradas_no_log))
        .join(Parada, Parada.supervisor_id == User.id)
        .filter(Parada.id.in_(query.with_entities(Parada.id)))
        .group_by(User.username)
        .order_by(func.sum(Parada.total_paradas_no_log).desc())
        .first()
    )
    return top_supervisor_q[0] if top_supervisor_q else "N/A"
