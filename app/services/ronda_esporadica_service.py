import logging
from datetime import datetime, time, timedelta, timezone
from typing import Tuple, Optional, Dict, Any
from app import db
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from app.models.user import User

logger = logging.getLogger(__name__)

class RondaEsporadicaService:
    """Serviço para gerenciar rondas esporádicas via PWA."""
    
    @staticmethod
    def validar_horario_entrada(hora_informada: time, tolerancia_minutos: int = 120) -> Tuple[bool, str]:
        """
        Valida se o horário informado está próximo do horário atual.
        
        Args:
            hora_informada: Horário informado pelo usuário
            tolerancia_minutos: Tolerância em minutos (padrão: 120 = 2 horas)
            
        Returns:
            Tuple[bool, str]: (é_válido, mensagem)
        """
        try:
            hora_atual = datetime.now().time()
            
            # Converter para minutos para facilitar comparação
            hora_informada_minutos = hora_informada.hour * 60 + hora_informada.minute
            hora_atual_minutos = hora_atual.hour * 60 + hora_atual.minute
            
            # Calcular diferença absoluta
            diferenca = abs(hora_informada_minutos - hora_atual_minutos)
            
            if diferenca <= tolerancia_minutos:
                return True, "Horário válido"
            else:
                return False, f"Horário muito diferente do atual. Diferença: {diferenca} minutos (máximo: {tolerancia_minutos} minutos)"
                
        except Exception as e:
            logger.error(f"Erro ao validar horário: {e}")
            return False, "Erro ao validar horário"
    
    @staticmethod
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
    
    @staticmethod
    def verificar_ronda_em_andamento(condominio_id: int, data_plantao: datetime.date) -> Optional[RondaEsporadica]:
        """
        Verifica se existe uma ronda em andamento para o condomínio na data.
        
        Args:
            condominio_id: ID do condomínio
            data_plantao: Data do plantão
            
        Returns:
            RondaEsporadica ou None
        """
        return RondaEsporadica.query.filter(
            RondaEsporadica.condominio_id == condominio_id,
            RondaEsporadica.data_plantao == data_plantao,
            RondaEsporadica.status == "em_andamento"
        ).first()
    
    @staticmethod
    def iniciar_ronda(
        condominio_id: int,
        user_id: int,
        data_plantao: datetime.date,
        hora_entrada: time,
        escala_plantao: str,
        supervisor_id: Optional[int] = None,
        observacoes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Inicia uma nova ronda esporádica.
        
        Args:
            condominio_id: ID do condomínio
            user_id: ID do usuário
            data_plantao: Data do plantão
            hora_entrada: Hora de entrada
            escala_plantao: Escala do plantão
            supervisor_id: ID do supervisor (opcional)
            observacoes: Observações iniciais (opcional)
            
        Returns:
            Tuple[bool, str, Optional[int]]: (sucesso, mensagem, ronda_id)
        """
        try:
            # Verificar se já existe ronda em andamento
            ronda_existente = RondaEsporadicaService.verificar_ronda_em_andamento(condominio_id, data_plantao)
            if ronda_existente:
                return False, "Já existe uma ronda em andamento para este condomínio nesta data.", None
            
            # Validar horário de entrada
            horario_valido, msg = RondaEsporadicaService.validar_horario_entrada(hora_entrada)
            if not horario_valido:
                return False, f"Horário inválido: {msg}", None
            
            # Inferir turno
            turno = RondaEsporadicaService.inferir_turno(escala_plantao)
            
            # Criar nova ronda
            nova_ronda = RondaEsporadica(
                condominio_id=condominio_id,
                user_id=user_id,
                supervisor_id=supervisor_id,
                data_plantao=data_plantao,
                escala_plantao=escala_plantao,
                turno=turno,
                hora_entrada=hora_entrada,
                observacoes=observacoes,
                status="em_andamento"
            )
            
            # Salvar no banco
            db.session.add(nova_ronda)
            db.session.commit()
            
            logger.info(f"Ronda esporádica iniciada: ID {nova_ronda.id}, Condomínio {condominio_id}")
            return True, "Ronda iniciada com sucesso!", nova_ronda.id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao iniciar ronda esporádica: {e}")
            return False, f"Erro interno: {str(e)}", None
    
    @staticmethod
    def finalizar_ronda(
        ronda_id: int,
        hora_saida: time,
        observacoes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Finaliza uma ronda esporádica.
        
        Args:
            ronda_id: ID da ronda
            hora_saida: Hora de saída
            observacoes: Observações finais (opcional)
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            ronda = RondaEsporadica.query.get(ronda_id)
            if not ronda:
                return False, "Ronda não encontrada."
            
            if ronda.status != "em_andamento":
                return False, "Apenas rondas em andamento podem ser finalizadas."
            
            # Validar horário de saída
            horario_valido, msg = RondaEsporadicaService.validar_horario_entrada(hora_saida, tolerancia_minutos=60)
            if not horario_valido:
                return False, f"Horário de saída inválido: {msg}", None
            
            # Finalizar ronda
            ronda.finalizar_ronda(hora_saida, observacoes)
            db.session.commit()
            
            logger.info(f"Ronda esporádica finalizada: ID {ronda_id}")
            return True, "Ronda finalizada com sucesso!"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao finalizar ronda esporádica: {e}")
            return False, f"Erro interno: {str(e)}"
    
    @staticmethod
    def atualizar_ronda(
        ronda_id: int,
        observacoes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Atualiza uma ronda em andamento.
        
        Args:
            ronda_id: ID da ronda
            observacoes: Novas observações
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            ronda = RondaEsporadica.query.get(ronda_id)
            if not ronda:
                return False, "Ronda não encontrada."
            
            if ronda.status != "em_andamento":
                return False, "Apenas rondas em andamento podem ser atualizadas."
            
            if observacoes:
                ronda.adicionar_observacao(observacoes)
            
            db.session.commit()
            return True, "Ronda atualizada com sucesso!"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar ronda esporádica: {e}")
            return False, f"Erro interno: {str(e)}"
    
    @staticmethod
    def listar_rondas_do_dia(condominio_id: int, data_plantao: datetime.date) -> list:
        """
        Lista todas as rondas de um condomínio em uma data específica.
        
        Args:
            condominio_id: ID do condomínio
            data_plantao: Data do plantão
            
        Returns:
            list: Lista de rondas
        """
        return RondaEsporadica.query.filter(
            RondaEsporadica.condominio_id == condominio_id,
            RondaEsporadica.data_plantao == data_plantao
        ).order_by(RondaEsporadica.hora_entrada.asc()).all()
    
    @staticmethod
    def consolidar_turno(condominio_id: int, data_plantao: datetime.date) -> Dict[str, Any]:
        """
        Consolida todas as rondas de um turno para gerar relatório.
        
        Args:
            condominio_id: ID do condomínio
            data_plantao: Data do plantão
            
        Returns:
            Dict com dados consolidados
        """
        rondas = RondaEsporadicaService.listar_rondas_do_dia(condominio_id, data_plantao)
        
        if not rondas:
            return {
                "sucesso": False,
                "mensagem": "Nenhuma ronda encontrada para esta data."
            }
        
        # Calcular totais
        total_rondas = len(rondas)
        duracao_total = sum(r.duracao_minutos for r in rondas if r.duracao_minutos)
        rondas_finalizadas = [r for r in rondas if r.status == "finalizada"]
        
        # Gerar relatório consolidado
        condominio = Condominio.query.get(condominio_id)
        relatorio = f"RELATÓRIO DE RONDAS ESPORÁDICAS - {condominio.nome if condominio else 'N/A'}\n"
        relatorio += f"Data: {data_plantao.strftime('%d/%m/%Y')}\n"
        relatorio += f"Total de Rondas: {total_rondas}\n"
        relatorio += f"Rondas Finalizadas: {len(rondas_finalizadas)}\n"
        relatorio += f"Duração Total: {duracao_total} minutos\n\n"
        
        for i, ronda in enumerate(rondas, 1):
            relatorio += f"Ronda {i}:\n"
            relatorio += f"  Entrada: {ronda.hora_entrada_formatada}\n"
            relatorio += f"  Saída: {ronda.hora_saida_formatada}\n"
            relatorio += f"  Duração: {ronda.duracao_formatada}\n"
            relatorio += f"  Status: {ronda.status}\n"
            if ronda.observacoes:
                relatorio += f"  Observações: {ronda.observacoes}\n"
            relatorio += "\n"
        
        # Converter objetos para dicionários serializáveis
        rondas_dict = []
        for ronda in rondas:
            rondas_dict.append({
                "id": ronda.id,
                "hora_entrada": ronda.hora_entrada_formatada,
                "hora_saida": ronda.hora_saida_formatada,
                "duracao_formatada": ronda.duracao_formatada,
                "status": ronda.status,
                "observacoes": ronda.observacoes,
                "user_id": ronda.user_id,
                "supervisor_id": ronda.supervisor_id,
                "turno": ronda.turno,
                "escala_plantao": ronda.escala_plantao
            })
        
        return {
            "sucesso": True,
            "total_rondas": total_rondas,
            "rondas_finalizadas": len(rondas_finalizadas),
            "duracao_total_minutos": duracao_total,
            "relatorio": relatorio,
            "rondas": rondas_dict
        } 