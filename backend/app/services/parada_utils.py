import logging
from datetime import datetime, time, date
from typing import Tuple, Optional
from app.models.parada import Parada
from app.models.condominio import Condominio
from app.models.user import User

logger = logging.getLogger(__name__)


def identificar_plantao(hora_entrada: time) -> str:
    """
    Identifica o plantão baseado na hora de entrada.
    """
    if hora_entrada >= time(18, 0) or hora_entrada < time(6, 0):
        return "18h às 06h"
    else:
        return "06h às 18h"


def inferir_turno(escala_plantao: str) -> str:
    """
    Infere o turno baseado na escala de plantão.
    """
    if "06h" in escala_plantao and "18h" in escala_plantao:
        return "Diurno"
    elif "18h" in escala_plantao and "06h" in escala_plantao:
        return "Noturno"
    else:
        hora_atual = datetime.now().hour
        return "Diurno" if 6 <= hora_atual < 18 else "Noturno"


def verificar_parada_em_andamento(condominio_id: int, data_plantao: date, user_id: Optional[int] = None) -> Optional[Parada]:
    """
    Verifica se existe uma parada em andamento para o condomínio na data.
    """
    from sqlalchemy import func
    
    query = Parada.query.filter(
        Parada.condominio_id == condominio_id,
        func.date(Parada.data_plantao_parada) == data_plantao,
        Parada.status == "Em Andamento"
    )
    
    if user_id:
        query = query.filter(Parada.user_id == user_id)
    
    return query.first()


def calcular_duracao_minutos(hora_entrada: time, hora_saida: time) -> int:
    """
    Calcula a duração em minutos entre entrada e saída.
    """
    entrada_minutos = hora_entrada.hour * 60 + hora_entrada.minute
    saida_minutos = hora_saida.hour * 60 + hora_saida.minute
    
    if saida_minutos < entrada_minutos:
        saida_minutos += 24 * 60
    
    return saida_minutos - entrada_minutos


def formatar_duracao(minutos: int) -> str:
    if minutos < 60:
        return f"{minutos}min"
    else:
        horas = minutos // 60
        mins = minutos % 60
        if mins == 0:
            return f"{horas}h"
        else:
            return f"{horas}h {mins}min"


def validar_horario_entrada(hora_informada: time, tolerancia_minutos: int = 120) -> Tuple[bool, str]:
    logger.warning("validar_horario_entrada foi chamada mas está desabilitada")
    return True, "Horário válido (validação desabilitada)"


def obter_condominio_por_id(condominio_id: int) -> Optional[Condominio]:
    try:
        return Condominio.query.get(condominio_id)
    except Exception as e:
        logger.error(f"Erro ao buscar condomínio {condominio_id}: {e}")
        return None


def obter_parada_por_id(parada_id: int) -> Optional[Parada]:
    try:
        return Parada.query.get(parada_id)
    except Exception as e:
        logger.error(f"Erro ao buscar parada {parada_id}: {e}")
        return None


def formatar_data_plantao(data: date) -> str:
    return data.strftime('%d/%m/%Y')


def formatar_hora(hora: time) -> str:
    return hora.strftime('%H:%M')


def get_system_user() -> Optional[User]:
    try:
        system_user = User.query.filter_by(is_admin=True).first()
        if system_user:
            logger.info(f"Usuário do sistema: {system_user.username}")
            return system_user
        else:
            logger.warning("Nenhum usuário administrador encontrado para operações do sistema")
            return None
    except Exception as e:
        logger.error(f"Erro ao obter usuário do sistema: {e}")
        return None


def infer_condominio_from_filename(filename: str) -> Optional[Condominio]:
    try:
        nome_arquivo = filename.upper().replace('.TXT', '')
        condominios = Condominio.query.all()
        for condominio in condominios:
            if condominio.nome.upper() in nome_arquivo:
                logger.info(f"Condomínio identificado: {condominio.nome} (arquivo: {filename})")
                return condominio
        logger.warning(f"Não foi possível identificar condomínio no arquivo: {filename}")
        return None
    except Exception as e:
        logger.error(f"Erro ao inferir condomínio do arquivo {filename}: {e}")
        return None
