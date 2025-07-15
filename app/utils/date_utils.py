# utils/date_utils.py (ou onde preferir)
from datetime import datetime, timedelta, timezone

from flask import flash


def parse_date_range(data_inicio_str, data_fim_str):
    today = datetime.now(timezone.utc).date()
    first_day = today.replace(day=1)
    last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(
        days=1
    )

    try:
        data_inicio = (
            datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            if data_inicio_str
            else first_day
        )
        data_fim = (
            datetime.strptime(data_fim_str, "%Y-%m-%d").date()
            if data_fim_str
            else last_day
        )
    except ValueError:
        flash("Formato de data inválido. Use AAAA-MM-DD.", "danger")
        return first_day, last_day
    return data_inicio, data_fim
