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
        flash("Formato de data inválido. Use dd/mm/aaaa ou aaaa-mm-dd.", "danger")
        return first_day, last_day
    return data_inicio, data_fim


def format_date_brazilian(date_obj, format_type="display"):
    """
    Formata uma data para o formato brasileiro.
    
    Args:
        date_obj: Objeto date ou datetime
        format_type: Tipo de formatação ("display", "short", "month_year")
    
    Returns:
        String formatada no padrão brasileiro
    """
    if not date_obj:
        return ""
    
    if format_type == "display":
        return date_obj.strftime("%d/%m/%Y")
    elif format_type == "short":
        return date_obj.strftime("%d/%m/%y")
    elif format_type == "month_year":
        return date_obj.strftime("%B/%Y")
    elif format_type == "datetime":
        return date_obj.strftime("%d/%m/%Y %H:%M")
    else:
        return date_obj.strftime("%d/%m/%Y")


def parse_brazilian_date(date_str):
    """
    Converte uma data do formato brasileiro (dd/mm/yyyy) para date object.
    
    Args:
        date_str: String no formato dd/mm/yyyy
    
    Returns:
        Objeto date ou None se inválido
    """
    if not date_str:
        return None
    
    try:
        # Tenta formato brasileiro primeiro
        if "/" in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        # Fallback para formato ISO
        elif "-" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return None
    except ValueError:
        return None
