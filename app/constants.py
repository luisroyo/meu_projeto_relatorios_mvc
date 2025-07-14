# app/constants.py
## [MELHORIA] Novo arquivo para centralizar constantes e Enums, eliminando "magic strings".
from enum import Enum

class ColaboradorStatus(Enum):
    """Define os status possíveis para um Colaborador."""
    ATIVO = 'Ativo'
    INATIVO = 'Inativo'

class OcorrenciaStatus(Enum):
    """Define os status possíveis para uma Ocorrência."""
    REGISTRADA = 'Registrada'
    EM_ANDAMENTO = 'Em Andamento'
    CONCLUIDA = 'Concluída'
    CANCELADA = 'Cancelada'

class JustificativaTipo(Enum):
    """Define os tipos de justificativas que podem ser geradas."""
    ATESTADO = 'atestado'
    TROCA_PLANTAO = 'troca_plantao'

class Turnos(Enum):
    """Define os nomes dos turnos de trabalho."""
    DIURNO_PAR = 'Diurno Par'
    NOTURNO_PAR = 'Noturno Par'
    DIURNO_IMPAR = 'Diurno Impar'
    NOTURNO_IMPAR = 'Noturno Impar'