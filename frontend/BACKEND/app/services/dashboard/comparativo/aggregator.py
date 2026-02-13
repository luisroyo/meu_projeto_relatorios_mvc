# app/services/dashboard/comparativo/aggregator.py
from typing import Dict, List, Tuple
from sqlalchemy import func
from app import db
from app.models import Ronda, Ocorrencia
from .filters import FilterApplier


class DataAggregator:
    """Classe para agregar dados dos modelos."""
    
    @staticmethod
    def get_monthly_aggregation_with_filters(
        model, date_column, year: int, filters: Dict, is_ronda: bool = True
    ) -> List[Tuple]:
        """
        Função genérica para agregar dados de um modelo por mês com filtros.
        """
        if is_ronda:
            # Para rondas, usa total_rondas_no_log (soma das rondas individuais)
            query = db.session.query(
                func.to_char(date_column, "YYYY-MM"),
                func.coalesce(func.sum(Ronda.total_rondas_no_log), 0),
            )
        else:
            # Para ocorrências, conta registros
            query = db.session.query(
                func.to_char(date_column, "YYYY-MM"), func.count(model.id)
            )

        # Aplica filtros específicos
        if is_ronda:
            query = FilterApplier.apply_ronda_filters(query, filters)
        else:
            query = FilterApplier.apply_ocorrencia_filters(query, filters)

        # Filtro de ano
        query = query.filter(func.to_char(date_column, "YYYY") == str(year))

        return (
            query.group_by(func.to_char(date_column, "YYYY-MM"))
            .order_by(func.to_char(date_column, "YYYY-MM"))
            .all()
        )

    @staticmethod
    def prepare_monthly_series(query_result: List[Tuple], year: int) -> List[int]:
        """Prepara uma série de 12 meses, preenchendo com zeros onde não há dados."""
        monthly_map = {f"{year}-{month:02d}": 0 for month in range(1, 13)}

        for month_str, count in query_result:
            if month_str in monthly_map:
                monthly_map[month_str] = count

        return list(monthly_map.values()) 