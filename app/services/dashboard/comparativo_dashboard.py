# app/services/dashboard/comparativo_dashboard.py
from datetime import datetime
from typing import Dict, List, Optional
from .comparativo.filters import FilterOptionsProvider
from .comparativo.aggregator import DataAggregator
from .comparativo.metrics import MetricsCalculator
from .comparativo.breakdown import BreakdownAnalyzer
from .comparativo.processor import DataProcessor


def get_monthly_comparison_data(
    year: Optional[int] = None,
    filters: Optional[Dict] = None,
    selected_months: Optional[List[int]] = None,
    comparison_mode: Optional[str] = None
) -> Dict:
    """
    Busca e processa dados de rondas e ocorrências para comparação mensal detalhada com filtros avançados.

    Args:
        year: Ano para análise
        filters: Filtros aplicados
        selected_months: Lista de meses selecionados (1-12)
        comparison_mode: 'single' para um mês, 'comparison' para múltiplos meses
    """
    # Inicializa valores padrão
    if not year:
        year = datetime.now().year
    if not filters:
        filters = {}
    if not selected_months:
        selected_months = []
    if not comparison_mode:
        comparison_mode = "all"

    # Processa dados baseado no modo de comparação
    if comparison_mode == "single" and selected_months:
        rondas_series, ocorrencias_series = DataProcessor.process_single_month_mode(
            year, selected_months[0], filters
        )
    elif comparison_mode == "comparison" and len(selected_months) >= 2:
        rondas_series, ocorrencias_series = DataProcessor.process_comparison_mode(
            year, selected_months, filters
        )
    else:
        rondas_series, ocorrencias_series = DataProcessor.process_all_months_mode(
            year, filters
        )

    # Calcula métricas comparativas
    metrics = MetricsCalculator.calculate_comparison_metrics(
        rondas_series, ocorrencias_series, filters
    )

    # Busca breakdown detalhado
    breakdown = BreakdownAnalyzer.get_detailed_breakdown(year, filters)

    # Prepara labels para os gráficos
    month_labels = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    # Busca dados para filtros
    filter_options = FilterOptionsProvider.get_filter_options()

    return {
        "selected_year": year,
        "selected_months": selected_months,
        "comparison_mode": comparison_mode,
        "month_labels": month_labels,
        "month_names": month_names,
        "rondas_data": rondas_series,
        "ocorrencias_data": ocorrencias_series,
        "metrics": metrics,
        "breakdown": breakdown,
        "filters": filters,
        "filter_options": filter_options,
    }
