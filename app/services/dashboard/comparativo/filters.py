from datetime import datetime
from typing import Dict
from app.models import Ronda, Ocorrencia


class FilterApplier:
    """Classe para aplicar filtros nas queries."""
    
    @staticmethod
    def apply_ronda_filters(query, filters: Dict):
        """Aplica filtros à query de rondas."""
        if not filters:
            return query
            
        if filters.get("condominio_id"):
            query = query.filter(Ronda.condominio_id == filters["condominio_id"])

        if filters.get("supervisor_id"):
            query = query.filter(Ronda.supervisor_id == filters["supervisor_id"])

        if filters.get("turno"):
            query = query.filter(Ronda.turno_ronda == filters["turno"])

        if filters.get("data_inicio_str"):
            try:
                start_date = datetime.strptime(filters["data_inicio_str"], "%Y-%m-%d")
                query = query.filter(Ronda.data_plantao_ronda >= start_date)
            except ValueError:
                pass

        if filters.get("data_fim_str"):
            try:
                end_date = datetime.strptime(filters["data_fim_str"], "%Y-%m-%d")
                query = query.filter(Ronda.data_plantao_ronda <= end_date)
            except ValueError:
                pass

        return query

    @staticmethod
    def apply_ocorrencia_filters(query, filters: Dict):
        """Aplica filtros à query de ocorrências."""
        if not filters:
            return query
            
        if filters.get("condominio_id"):
            query = query.filter(Ocorrencia.condominio_id == filters["condominio_id"])

        if filters.get("supervisor_id"):
            query = query.filter(Ocorrencia.supervisor_id == filters["supervisor_id"])

        if filters.get("tipo_ocorrencia_id"):
            query = query.filter(
                Ocorrencia.ocorrencia_tipo_id == filters["tipo_ocorrencia_id"]
            )

        if filters.get("status"):
            query = query.filter(Ocorrencia.status == filters["status"])

        if filters.get("turno"):
            query = query.filter(Ocorrencia.turno == filters["turno"])

        if filters.get("data_inicio_str"):
            try:
                start_date = datetime.strptime(filters["data_inicio_str"], "%Y-%m-%d")
                query = query.filter(Ocorrencia.data_hora_ocorrencia >= start_date)
            except ValueError:
                pass

        if filters.get("data_fim_str"):
            try:
                end_date = datetime.strptime(filters["data_fim_str"], "%Y-%m-%d")
                query = query.filter(Ocorrencia.data_hora_ocorrencia <= end_date)
            except ValueError:
                pass

        return query


class FilterOptionsProvider:
    """Classe para fornecer opções de filtros."""
    
    @staticmethod
    def get_filter_options() -> Dict:
        """Retorna todas as opções disponíveis para filtros."""
        from app.models import Condominio, User, OcorrenciaTipo
        
        return {
            "condominios": Condominio.query.order_by(Condominio.nome).all(),
            "supervisors": (
                User.query.filter_by(is_supervisor=True, is_approved=True)
                .order_by(User.username)
                .all()
            ),
            "tipos_ocorrencia": OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all(),
            "turnos": [
                "Diurno", "Noturno", "Diurno Par", "Diurno Impar", 
                "Noturno Par", "Noturno Impar"
            ],
            "status_list": ["Registrada", "Em Andamento", "Concluída"],
        } 