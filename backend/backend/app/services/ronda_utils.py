"""
Utilitários centralizados para o sistema de rondas.
Este módulo contém funções comuns usadas por diferentes serviços de ronda.
"""

import logging
from datetime import datetime, time, date
from typing import Tuple, Optional
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.models.user import User

logger = logging.getLogger(__name__)


def identificar_plantao(hora_entrada: time) -> str:
    """
    Identifica o plantão baseado na hora de entrada.
    
    Args:
        hora_entrada: Hora de entrada da ronda
        
    Returns:
        str: "06h às 18h" ou "18h às 06h"
    """
    if hora_entrada >= time(18, 0) or hora_entrada < time(6, 0):
        return "18h às 06h"
    else:
        return "06h às 18h"


def inferir_turno(escala_plantao: str) -> str:
    """
    Infere o turno baseado na escala de plantão.
    
    Args:
        escala_plantao: String da escala (ex: "06h às 18h")
        
    Returns:
        str: "Diurno" ou "Noturno"
    """
    if "06h" in escala_plantao and "18h" in escala_plantao:
        return "Diurno"
    elif "18h" in escala_plantao and "06h" in escala_plantao:
        return "Noturno"
    else:
        # Fallback baseado na hora atual
        hora_atual = datetime.now().hour
        return "Diurno" if 6 <= hora_atual < 18 else "Noturno"


def verificar_ronda_em_andamento(condominio_id: int, data_plantao: date, user_id: Optional[int] = None) -> Optional[Ronda]:
    """
    Verifica se existe uma ronda em andamento para o condomínio na data.
    
    Args:
        condominio_id: ID do condomínio
        data_plantao: Data do plantão
        user_id: ID do usuário (opcional, para filtrar por usuário)
        
    Returns:
        Ronda ou None
    """
    from sqlalchemy import func
    
    query = Ronda.query.filter(
        Ronda.condominio_id == condominio_id,
        func.date(Ronda.data_plantao_ronda) == data_plantao,
        Ronda.status == "Em Andamento"
    )
    
    if user_id:
        query = query.filter(Ronda.user_id == user_id)
    
    return query.first()


def calcular_duracao_minutos(hora_entrada: time, hora_saida: time) -> int:
    """
    Calcula a duração em minutos entre entrada e saída.
    
    Args:
        hora_entrada: Hora de entrada
        hora_saida: Hora de saída
        
    Returns:
        int: Duração em minutos
    """
    entrada_minutos = hora_entrada.hour * 60 + hora_entrada.minute
    saida_minutos = hora_saida.hour * 60 + hora_saida.minute
    
    # Se a saída é no dia seguinte (plantão noturno)
    if saida_minutos < entrada_minutos:
        saida_minutos += 24 * 60  # Adiciona 24 horas em minutos
    
    return saida_minutos - entrada_minutos


def formatar_duracao(minutos: int) -> str:
    """
    Formata duração em minutos para string legível.
    
    Args:
        minutos: Duração em minutos
        
    Returns:
        str: String formatada (ex: "1h 30min" ou "45min")
    """
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
    """
    Valida se o horário informado está próximo do horário atual.
    ATENÇÃO: Esta função está desabilitada e sempre retorna True.
    
    Args:
        hora_informada: Horário informado pelo usuário
        tolerancia_minutos: Tolerância em minutos (não usado mais)
        
    Returns:
        Tuple[bool, str]: (é_válido, mensagem) - Sempre (True, "Horário válido")
    """
    # VALIDAÇÃO DESABILITADA - Sempre retorna True
    logger.warning("validar_horario_entrada foi chamada mas está desabilitada")
    return True, "Horário válido (validação desabilitada)"


def obter_condominio_por_id(condominio_id: int) -> Optional[Condominio]:
    """
    Obtém um condomínio por ID com tratamento de erro.
    
    Args:
        condominio_id: ID do condomínio
        
    Returns:
        Condominio ou None se não encontrado
    """
    try:
        return Condominio.query.get(condominio_id)
    except Exception as e:
        logger.error(f"Erro ao buscar condomínio {condominio_id}: {e}")
        return None


def obter_ronda_por_id(ronda_id: int) -> Optional[Ronda]:
    """
    Obtém uma ronda por ID com tratamento de erro.
    
    Args:
        ronda_id: ID da ronda
        
    Returns:
        Ronda ou None se não encontrada
    """
    try:
        return Ronda.query.get(ronda_id)
    except Exception as e:
        logger.error(f"Erro ao buscar ronda {ronda_id}: {e}")
        return None


def formatar_data_plantao(data: date) -> str:
    """
    Formata data do plantão para exibição.
    
    Args:
        data: Data do plantão
        
    Returns:
        str: Data formatada (ex: "31/07/2025")
    """
    return data.strftime('%d/%m/%Y')


def formatar_hora(hora: time) -> str:
    """
    Formata hora para exibição.
    
    Args:
        hora: Hora a ser formatada
        
    Returns:
        str: Hora formatada (ex: "18:30")
    """
    return hora.strftime('%H:%M')


def get_system_user() -> Optional[User]:
    """
    Obtém o usuário do sistema para operações automatizadas.
    Retorna o primeiro usuário administrador encontrado.

    Returns:
        User ou None se nenhum admin encontrado
    """
    try:
        # Busca o primeiro usuário administrador
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
    """
    Infere o condomínio baseado no nome do arquivo.
    Tenta encontrar um condomínio cujo nome esteja contido no nome do arquivo.

    Args:
        filename: Nome do arquivo (ex: "ZERMATT_20250130.txt")

    Returns:
        Condominio ou None se não encontrado
    """
    try:
        # Remove extensão e converte para maiúsculas
        nome_arquivo = filename.upper().replace('.TXT', '').replace('.TXT', '')
        
        # Busca todos os condomínios
        condominios = Condominio.query.all()
        
        # Procura por condomínio cujo nome esteja contido no nome do arquivo
        for condominio in condominios:
            if condominio.nome.upper() in nome_arquivo:
                logger.info(f"Condomínio identificado: {condominio.nome} (arquivo: {filename})")
                return condominio
        
        logger.warning(f"Não foi possível identificar condomínio no arquivo: {filename}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao inferir condomínio do arquivo {filename}: {e}")
        return None

