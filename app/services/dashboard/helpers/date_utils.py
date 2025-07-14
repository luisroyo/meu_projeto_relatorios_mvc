# app/services/dashboard/helpers/date_utils.py
from datetime import date, timedelta

def generate_date_labels(start_date: date, end_date: date) -> list[str]:
    """
    Gera uma lista de labels de data no formato 'YYYY-MM-DD' dentro de um intervalo.
    """
    labels = []
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    return labels