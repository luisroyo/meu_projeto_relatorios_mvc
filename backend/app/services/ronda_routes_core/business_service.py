from app.services.ronda_routes_core.helpers import inferir_turno
from app.services.ronda_routes_core.validation import validar_campos_essenciais, validar_condominio_existe
from app.services.ronda_routes_core.persistence_service import save_ronda, update_ronda, get_ronda_by_id
from app.models import EscalaMensal

def atribuir_supervisor(data_plantao, turno_ronda, supervisor_id_manual_str):
    supervisor_id_para_db = (
        int(supervisor_id_manual_str)
        if supervisor_id_manual_str and supervisor_id_manual_str != "0"
        else None
    )
    if not supervisor_id_para_db:
        escala = EscalaMensal.query.filter_by(
            ano=data_plantao.year, mes=data_plantao.month, nome_turno=turno_ronda
        ).first()
        if escala:
            supervisor_id_para_db = escala.supervisor_id
    return supervisor_id_para_db 