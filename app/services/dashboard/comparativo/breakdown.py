from typing import Dict, List, Tuple
from sqlalchemy import func
from app import db
from app.models import Condominio, Ronda, Ocorrencia, User, OcorrenciaTipo
from .filters import FilterApplier


class BreakdownAnalyzer:
    """Classe para análise detalhada por diferentes critérios."""
    
    @staticmethod
    def get_detailed_breakdown(year: int, filters: Dict) -> Dict:
        """Busca breakdown detalhado por diferentes critérios."""
        return {
            "rondas_por_condominio": BreakdownAnalyzer._get_rondas_por_condominio(year, filters),
            "ocorrencias_por_condominio": BreakdownAnalyzer._get_ocorrencias_por_condominio(year, filters),
            "rondas_por_supervisor": BreakdownAnalyzer._get_rondas_por_supervisor(year, filters),
            "ocorrencias_por_supervisor": BreakdownAnalyzer._get_ocorrencias_por_supervisor(year, filters),
            "rondas_por_turno": BreakdownAnalyzer._get_rondas_por_turno(year, filters),
            "ocorrencias_por_tipo": BreakdownAnalyzer._get_ocorrencias_por_tipo(year, filters),
            "ocorrencias_por_status": BreakdownAnalyzer._get_ocorrencias_por_status(year, filters),
        }

    @staticmethod
    def _get_rondas_por_condominio(year: int, filters: Dict) -> List[Tuple]:
        """Busca rondas por condomínio."""
        query = (
            db.session.query(
                Condominio.nome,
                func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total"),
            )
            .join(Ronda, Condominio.id == Ronda.condominio_id)
            .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
        )
        query = FilterApplier.apply_ronda_filters(query, filters)
        return (
            query.group_by(Condominio.nome)
            .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
            .limit(10)
            .all()
        )

    @staticmethod
    def _get_ocorrencias_por_condominio(year: int, filters: Dict) -> List[Tuple]:
        """Busca ocorrências por condomínio."""
        query = (
            db.session.query(Condominio.nome, func.count(Ocorrencia.id).label("total"))
            .join(Ocorrencia, Condominio.id == Ocorrencia.condominio_id)
            .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
        )
        query = FilterApplier.apply_ocorrencia_filters(query, filters)
        return (
            query.group_by(Condominio.nome)
            .order_by(func.count(Ocorrencia.id).desc())
            .limit(10)
            .all()
        )

    @staticmethod
    def _get_rondas_por_supervisor(year: int, filters: Dict) -> List[Tuple]:
        """Busca rondas por supervisor."""
        query = (
            db.session.query(
                User.username,
                func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total"),
            )
            .join(Ronda, User.id == Ronda.supervisor_id)
            .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
        )
        query = FilterApplier.apply_ronda_filters(query, filters)
        return (
            query.group_by(User.username)
            .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
            .limit(10)
            .all()
        )

    @staticmethod
    def _get_ocorrencias_por_supervisor(year: int, filters: Dict) -> List[Tuple]:
        """Busca ocorrências por supervisor."""
        query = (
            db.session.query(User.username, func.count(Ocorrencia.id).label("total"))
            .join(Ocorrencia, User.id == Ocorrencia.supervisor_id)
            .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
        )
        query = FilterApplier.apply_ocorrencia_filters(query, filters)
        return (
            query.group_by(User.username)
            .order_by(func.count(Ocorrencia.id).desc())
            .limit(10)
            .all()
        )

    @staticmethod
    def _get_ocorrencias_por_tipo(year: int, filters: Dict) -> List[Tuple]:
        """Busca ocorrências por tipo."""
        query = (
            db.session.query(OcorrenciaTipo.nome, func.count(Ocorrencia.id).label("total"))
            .join(Ocorrencia, OcorrenciaTipo.id == Ocorrencia.ocorrencia_tipo_id)
            .filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
        )
        query = FilterApplier.apply_ocorrencia_filters(query, filters)
        return (
            query.group_by(OcorrenciaTipo.nome)
            .order_by(func.count(Ocorrencia.id).desc())
            .limit(10)
            .all()
        )

    @staticmethod
    def _get_rondas_por_turno(year: int, filters: Dict) -> List[Tuple]:
        """Busca rondas por turno."""
        query = db.session.query(
            Ronda.turno_ronda,
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total"),
        ).filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year))
        query = FilterApplier.apply_ronda_filters(query, filters)
        return (
            query.group_by(Ronda.turno_ronda)
            .order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc())
            .all()
        )

    @staticmethod
    def _get_ocorrencias_por_status(year: int, filters: Dict) -> List[Tuple]:
        """Busca ocorrências por status."""
        query = db.session.query(
            Ocorrencia.status, func.count(Ocorrencia.id).label("total")
        ).filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year))
        query = FilterApplier.apply_ocorrencia_filters(query, filters)
        return (
            query.group_by(Ocorrencia.status)
            .order_by(func.count(Ocorrencia.id).desc())
            .all()
        ) 