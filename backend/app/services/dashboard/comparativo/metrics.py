from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from app import db
from app.models import Ronda
from app.utils.locale_config import LocaleConfig


class MetricsCalculator:
    """Classe para calcular métricas e indicadores."""
    
    @staticmethod
    def calculate_supervisor_specific_metrics(total_rondas: int, filters: Dict, year: int) -> Tuple[float, int]:
        """
        Calcula métricas específicas para um supervisor quando há filtro de supervisor.
        """
        if filters.get("supervisor_id"):
            # Se há filtro de supervisor, calcula baseado apenas nos dias que ele trabalhou
            dias_trabalhados = (
                db.session.query(func.count(func.distinct(Ronda.data_plantao_ronda)))
                .filter(
                    func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year),
                    Ronda.supervisor_id == filters["supervisor_id"],
                )
                .scalar()
            )

            media_rondas_dia_trabalhado = (
                round(total_rondas / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
            )
            return media_rondas_dia_trabalhado, dias_trabalhados
        else:
            # Se não há filtro de supervisor, usa o cálculo geral
            dias_trabalhados = (
                db.session.query(func.count(func.distinct(Ronda.data_plantao_ronda)))
                .filter(
                    func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(year),
                    Ronda.supervisor_id.isnot(None),
                )
                .scalar()
            )

            media_rondas_dia_trabalhado = (
                round(total_rondas / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
            )
            return media_rondas_dia_trabalhado, dias_trabalhados

    @staticmethod
    def calculate_trend(data_series: List[int]) -> str:
        """Calcula a tendência baseada nos últimos 3 meses vs primeiros 3 meses."""
        if len(data_series) < 6:
            return "Insuficiente"

        primeiros_3 = sum(data_series[:3])
        ultimos_3 = sum(data_series[-3:])

        if ultimos_3 > primeiros_3 * 1.1:
            return "Crescimento"
        elif ultimos_3 < primeiros_3 * 0.9:
            return "Queda"
        else:
            return "Estável"

    @staticmethod
    def calculate_comparison_metrics(
        rondas_series: List[int], 
        ocorrencias_series: List[int], 
        paradas_series: Optional[List[int]] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Calcula métricas comparativas entre rondas, ocorrências e paradas."""
        if paradas_series is None:
            paradas_series = [0] * 12

        total_rondas = sum(rondas_series)
        total_ocorrencias = sum(ocorrencias_series)
        total_paradas = sum(paradas_series)

        # Calcula médias mensais
        meses_com_dados = len([x for x in rondas_series if x > 0])
        media_rondas_mensal = (
            round(total_rondas / meses_com_dados, 1) if meses_com_dados > 0 else 0
        )

        meses_com_paradas = len([x for x in paradas_series if x > 0])
        media_paradas_mensal = (
            round(total_paradas / meses_com_paradas, 1) if meses_com_paradas > 0 else 0
        )

        meses_com_ocorrencias = len([x for x in ocorrencias_series if x > 0])
        media_ocorrencias_mensal = (
            round(total_ocorrencias / meses_com_ocorrencias, 1)
            if meses_com_ocorrencias > 0
            else 0
        )

        # Calcula média por dia real trabalhado
        current_year = datetime.now().year
        media_rondas_dia_trabalhado, dias_trabalhados = (
            MetricsCalculator.calculate_supervisor_specific_metrics(
                total_rondas, filters or {}, current_year
            )
        )

        # Encontra meses com mais atividade
        mes_mais_rondas = MetricsCalculator._find_most_active_month(rondas_series, "rondas")
        mes_mais_ocorrencias = MetricsCalculator._find_most_active_month(ocorrencias_series, "ocorrencias")
        mes_mais_paradas = MetricsCalculator._find_most_active_month(paradas_series, "paradas")

        # Calcula tendências
        tendencia_rondas = MetricsCalculator.calculate_trend(rondas_series)
        tendencia_ocorrencias = MetricsCalculator.calculate_trend(ocorrencias_series)
        tendencia_paradas = MetricsCalculator.calculate_trend(paradas_series)

        # Calcula proporção
        proporcao_ocorrencias_por_ronda = (
            round((total_ocorrencias / total_rondas) * 100, 1) if total_rondas > 0 else 0
        )
        proporcao_paradas_por_ronda = (
            round((total_paradas / total_rondas) * 100, 1) if total_rondas > 0 else 0
        )

        return {
            "total_rondas": total_rondas,
            "total_ocorrencias": total_ocorrencias,
            "total_paradas": total_paradas,
            "media_rondas_mensal": media_rondas_mensal,
            "media_paradas_mensal": media_paradas_mensal,
            "media_ocorrencias_mensal": media_ocorrencias_mensal,
            "media_rondas_dia_trabalhado": media_rondas_dia_trabalhado,
            "dias_trabalhados_periodo": dias_trabalhados,
            "mes_mais_rondas": mes_mais_rondas,
            "mes_mais_ocorrencias": mes_mais_ocorrencias,
            "mes_mais_paradas": mes_mais_paradas,
            "tendencia_rondas": tendencia_rondas,
            "tendencia_ocorrencias": tendencia_ocorrencias,
            "tendencia_paradas": tendencia_paradas,
            "proporcao_ocorrencias_por_ronda": proporcao_ocorrencias_por_ronda,
            "proporcao_paradas_por_ronda": proporcao_paradas_por_ronda,
        }

    @staticmethod
    def _find_most_active_month(data_series: List[int], data_type: str) -> str:
        """Encontra o mês com mais atividade."""
        if not data_series:
            return "N/A"
            
        max_value = max(data_series)
        if max_value <= 0:
            return "N/A"
            
        mes_index = data_series.index(max_value)
        month_names = LocaleConfig.get_all_month_names('pt_BR')
        return f"{month_names[mes_index]} ({max_value})" 