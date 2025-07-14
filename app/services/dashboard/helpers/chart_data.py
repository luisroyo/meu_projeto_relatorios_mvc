# app/services/dashboard/helpers/chart_data.py
def fill_series_with_zeros(data_query_result: list[tuple], labels: list[str]) -> list[int]:
    """
    Preenche uma série de dados com zeros para labels (datas) sem valores.
    
    Args:
        data_query_result: Uma lista de tuplas no formato (label, valor) vinda do banco.
        labels: A lista completa de labels que o gráfico deve ter.

    Returns:
        Uma lista de valores pronta para ser usada no gráfico.
    """
    data_map = {str(date): count for date, count in data_query_result}
    return [data_map.get(label, 0) for label in labels]