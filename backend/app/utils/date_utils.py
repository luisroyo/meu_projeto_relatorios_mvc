# utils/date_utils.py (ou onde preferir)
from datetime import datetime, timedelta, timezone
import pytz
from flask import flash, current_app


def get_local_tz():
    tz_name = (current_app.config.get("DEFAULT_TIMEZONE") if current_app else "America/Sao_Paulo")
    return pytz.timezone(tz_name)


def now_utc():
    return datetime.now(timezone.utc)


def now_local():
    return now_utc().astimezone(get_local_tz())


def parse_date_range(data_inicio_str, data_fim_str):
    today = now_local().date()
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
