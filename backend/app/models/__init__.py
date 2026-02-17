from .user import User
from .colaborador import Colaborador
from .condominio import Condominio
from .ronda import Ronda
from .processing_history import ProcessingHistory
from .escala_mensal import EscalaMensal
from .ocorrencia_tipo import OcorrenciaTipo
from .orgao_publico import OrgaoPublico
from .logradouro import Logradouro
from .ocorrencia import Ocorrencia, ocorrencia_orgaos, ocorrencia_colaboradores
from .login_history import LoginHistory
from .vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas
from .vw_colaboradores import VWColaboradores
from .vw_logradouros import VWLogradouros
from .vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas
from .vw_rondas_detalhadas import VWRondasDetalhadas
# RondaEsporadica removida - usar apenas modelo Ronda unificado
from .user_online import UserOnline 