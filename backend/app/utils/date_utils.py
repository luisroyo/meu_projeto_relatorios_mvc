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
    
    # [CORRIGIDO] Calcular o último dia do mês de forma mais robusta
    # Avança para o próximo mês e volta um dia
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    last_day = next_month - timedelta(days=1)

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


def get_plantao_date_from_ocorrencia(ocorrencia_datetime, turno_supervisor=None):
    """
    Determina a data do plantão baseada na data/hora da ocorrência e no turno do supervisor.
    
    Regras:
    - Turnos Diurnos (6h às 18h): ocorrência pertence ao mesmo dia
    - Turnos Noturnos (18h às 6h): 
      * Se ocorrência entre 18h-23h59: pertence ao mesmo dia
      * Se ocorrência entre 0h-5h59: pertence ao dia anterior (plantão começou no dia anterior)
    
    Args:
        ocorrencia_datetime: datetime da ocorrência
        turno_supervisor: turno do supervisor ("Diurno Par", "Noturno Par", etc.)
    
    Returns:
        date: data do plantão ao qual a ocorrência pertence
    """
    if not ocorrencia_datetime:
        return None
    
    # Se não há informação do turno, usa a data da ocorrência
    if not turno_supervisor:
        return ocorrencia_datetime.date()
    
    # Converte para timezone local se necessário
    if ocorrencia_datetime.tzinfo is None:
        local_tz = get_local_tz()
        ocorrencia_datetime = local_tz.localize(ocorrencia_datetime)
    elif ocorrencia_datetime.tzinfo != get_local_tz():
        ocorrencia_datetime = ocorrencia_datetime.astimezone(get_local_tz())
    
    # Determina se é turno noturno
    is_turno_noturno = "Noturno" in turno_supervisor
    
    if is_turno_noturno:
        # Para turnos noturnos, verifica o horário
        hora = ocorrencia_datetime.hour
        
        if 0 <= hora < 6:
            # Madrugada (0h-5h59): pertence ao plantão do dia anterior
            return (ocorrencia_datetime.date() - timedelta(days=1))
        else:
            # Resto do dia: pertence ao plantão do mesmo dia
            return ocorrencia_datetime.date()
    else:
        # Turnos diurnos: sempre pertence ao mesmo dia
        return ocorrencia_datetime.date()


def get_plantao_datetime_range(plantao_date, turno_supervisor):
    """
    Retorna o range de datetime para um plantão específico.
    
    Args:
        plantao_date: data do plantão
        turno_supervisor: turno do supervisor
    
    Returns:
        tuple: (inicio_datetime, fim_datetime) em UTC
    """
    local_tz = get_local_tz()
    is_turno_noturno = "Noturno" in turno_supervisor
    
    if is_turno_noturno:
        # Turno noturno: 18h do dia anterior até 6h do dia seguinte
        inicio = local_tz.localize(datetime.combine(plantao_date, datetime.min.time().replace(hour=18)))
        fim = local_tz.localize(datetime.combine(plantao_date + timedelta(days=1), datetime.min.time().replace(hour=6)))
    else:
        # Turno diurno: 6h até 18h do mesmo dia
        inicio = local_tz.localize(datetime.combine(plantao_date, datetime.min.time().replace(hour=6)))
        fim = local_tz.localize(datetime.combine(plantao_date, datetime.min.time().replace(hour=18)))
    
    # Converte para UTC
    return inicio.astimezone(pytz.utc), fim.astimezone(pytz.utc)