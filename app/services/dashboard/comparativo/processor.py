from datetime import date, timedelta
from typing import Dict, List, Tuple
from app.models import Ronda, Ocorrencia
from .aggregator import DataAggregator


class DataProcessor:
    """Classe para processar dados de diferentes modos de comparação."""
    
    @staticmethod
    def process_single_month_mode(year: int, month: int, filters: Dict) -> Tuple[List[int], List[int]]:
        """Processa dados para modo de mês único."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Aplica filtros de data para o mês específico
        temp_filters = filters.copy()
        temp_filters["data_inicio_str"] = start_date.strftime("%Y-%m-%d")
        temp_filters["data_fim_str"] = end_date.strftime("%Y-%m-%d")

        # Busca dados apenas para o mês selecionado
        rondas_raw = DataAggregator.get_monthly_aggregation_with_filters(
            Ronda, Ronda.data_plantao_ronda, year, temp_filters, is_ronda=True
        )
        ocorrencias_raw = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, temp_filters, is_ronda=False
        )

        # Prepara série apenas para o mês selecionado
        rondas_series = [0] * 12
        ocorrencias_series = [0] * 12

        for mes_str, total in rondas_raw:
            mes_num = int(mes_str.split("-")[1])
            rondas_series[mes_num - 1] = total

        for mes_str, total in ocorrencias_raw:
            mes_num = int(mes_str.split("-")[1])
            ocorrencias_series[mes_num - 1] = total

        return rondas_series, ocorrencias_series

    @staticmethod
    def process_comparison_mode(year: int, selected_months: List[int], filters: Dict) -> Tuple[List[int], List[int]]:
        """Processa dados para modo de comparação entre meses."""
        rondas_series = [0] * 12
        ocorrencias_series = [0] * 12

        for month in selected_months:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            # Filtros temporários para o mês
            temp_filters = filters.copy()
            temp_filters["data_inicio_str"] = start_date.strftime("%Y-%m-%d")
            temp_filters["data_fim_str"] = end_date.strftime("%Y-%m-%d")

            # Busca dados para o mês
            rondas_raw = DataAggregator.get_monthly_aggregation_with_filters(
                Ronda, Ronda.data_plantao_ronda, year, temp_filters, is_ronda=True
            )
            ocorrencias_raw = DataAggregator.get_monthly_aggregation_with_filters(
                Ocorrencia,
                Ocorrencia.data_hora_ocorrencia,
                year,
                temp_filters,
                is_ronda=False,
            )

            # Adiciona aos dados
            for mes_str, total in rondas_raw:
                mes_num = int(mes_str.split("-")[1])
                rondas_series[mes_num - 1] = total

            for mes_str, total in ocorrencias_raw:
                mes_num = int(mes_str.split("-")[1])
                ocorrencias_series[mes_num - 1] = total

        return rondas_series, ocorrencias_series

    @staticmethod
    def process_all_months_mode(year: int, filters: Dict) -> Tuple[List[int], List[int]]:
        """Processa dados para modo padrão - todos os meses."""
        rondas_raw = DataAggregator.get_monthly_aggregation_with_filters(
            Ronda, Ronda.data_plantao_ronda, year, filters, is_ronda=True
        )
        rondas_series = DataAggregator.prepare_monthly_series(rondas_raw, year)

        ocorrencias_raw = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, filters, is_ronda=False
        )
        ocorrencias_series = DataAggregator.prepare_monthly_series(ocorrencias_raw, year)

        return rondas_series, ocorrencias_series 