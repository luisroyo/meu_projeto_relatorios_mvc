import logging
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple
from app import db
from app.models.ronda_esporadica import RondaEsporadica
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.models.user import User
from app.services.ronda_esporadica_service import RondaEsporadicaService
from app.services.patrimonial_report_service import PatrimonialReportService

logger = logging.getLogger(__name__)

class RondaEsporadicaConsolidacaoService:
    """Serviço para consolidar rondas esporádicas e integrar com sistema principal."""

    @staticmethod
    def consolidar_e_enviar_whatsapp(condominio_id: int, data_plantao: datetime.date) -> Dict[str, Any]:
        """
        Consolida todas as rondas esporádicas de um turno e envia via WhatsApp.
        """
        try:
            # 1. Consolidar dados do turno
            resultado_consolidacao = RondaEsporadicaService.consolidar_turno(condominio_id, data_plantao)
            
            if not resultado_consolidacao["sucesso"]:
                return {
                    "sucesso": False,
                    "message": "Nenhuma ronda encontrada para consolidação",
                    "whatsapp_enviado": False
                }

            # 2. Buscar dados do condomínio
            condominio = Condominio.query.get(condominio_id)
            if not condominio:
                return {
                    "sucesso": False,
                    "message": "Condomínio não encontrado",
                    "whatsapp_enviado": False
                }

            # 3. Gerar relatório formatado
            relatorio_formatado = RondaEsporadicaConsolidacaoService._formatar_relatorio_whatsapp(
                resultado_consolidacao, condominio, data_plantao
            )

            # 4. Enviar via WhatsApp (usando serviço existente)
            whatsapp_enviado = RondaEsporadicaConsolidacaoService._enviar_via_whatsapp(
                relatorio_formatado, condominio
            )

            # 5. Salvar no banco principal (se WhatsApp foi enviado com sucesso)
            ronda_principal_id = None
            if whatsapp_enviado:
                ronda_principal_id = RondaEsporadicaConsolidacaoService._salvar_no_banco_principal(
                    condominio_id, data_plantao, resultado_consolidacao
                )

            return {
                "sucesso": True,
                "message": "Consolidação realizada com sucesso",
                "whatsapp_enviado": whatsapp_enviado,
                "ronda_principal_id": ronda_principal_id,
                "total_rondas": resultado_consolidacao["total_rondas"],
                "duracao_total_minutos": resultado_consolidacao["duracao_total_minutos"],
                "relatorio": relatorio_formatado
            }

        except Exception as e:
            logger.error(f"Erro na consolidação: {str(e)}")
            return {
                "sucesso": False,
                "message": f"Erro na consolidação: {str(e)}",
                "whatsapp_enviado": False
            }

    @staticmethod
    def _formatar_relatorio_whatsapp(resultado_consolidacao: Dict[str, Any], 
                                    condominio: Condominio, 
                                    data_plantao: datetime.date) -> str:
        """Formata o relatório para envio via WhatsApp."""
        
        data_formatada = data_plantao.strftime("%d/%m/%Y")
        duracao_total_horas = resultado_consolidacao["duracao_total_minutos"] // 60
        duracao_total_minutos = resultado_consolidacao["duracao_total_minutos"] % 60
        
        relatorio = f"""🔄 *RELATÓRIO DE RONDAS ESPORÁDICAS*

🏢 *Condomínio:* {condominio.nome}
📅 *Data:* {data_formatada}
⏰ *Total de Rondas:* {resultado_consolidacao["total_rondas"]}
⏱️ *Duração Total:* {duracao_total_horas}h {duracao_total_minutos}min
✅ *Rondas Finalizadas:* {resultado_consolidacao["rondas_finalizadas"]}

📋 *Detalhes das Rondas:*
"""
        
        # Adicionar detalhes de cada ronda
        for i, ronda in enumerate(resultado_consolidacao["rondas"], 1):
            relatorio += f"""
🔸 *Ronda {i}:*
   ⏰ Entrada: {ronda['hora_entrada']}
   ⏰ Saída: {ronda['hora_saida']}
   ⏱️ Duração: {ronda['duracao_formatada']}
   📝 Status: {ronda['status']}
   📋 Obs: {ronda['observacoes'] or 'Nenhuma'}
"""
        
        relatorio += f"""
📊 *Resumo:*
• Total de rondas realizadas: {resultado_consolidacao["total_rondas"]}
• Tempo total de serviço: {duracao_total_horas}h {duracao_total_minutos}min
• Eficiência: {resultado_consolidacao["rondas_finalizadas"]}/{resultado_consolidacao["total_rondas"]} rondas finalizadas

🔄 *Relatório gerado automaticamente pelo sistema*
"""
        
        return relatorio

    @staticmethod
    def _enviar_via_whatsapp(relatorio: str, condominio: Condominio) -> bool:
        """Envia relatório via WhatsApp usando serviço existente."""
        try:
            # Usar o serviço de patrimonial report existente
            patrimonial_service = PatrimonialReportService()
            
            # Preparar dados para o serviço existente
            dados_relatorio = {
                "condominio": condominio.nome,
                "data": datetime.now().strftime("%d/%m/%Y"),
                "relatorio": relatorio,
                "tipo": "rondas_esporadicas"
            }
            
            # Enviar via WhatsApp (usando método existente)
            resultado = patrimonial_service.enviar_relatorio_whatsapp(dados_relatorio)
            
            logger.info(f"WhatsApp enviado para {condominio.nome}: {resultado}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return False

    @staticmethod
    def _salvar_no_banco_principal(condominio_id: int, 
                                  data_plantao: datetime.date, 
                                  resultado_consolidacao: Dict[str, Any]) -> Optional[int]:
        """Salva dados consolidados na tabela principal de rondas."""
        try:
            # Buscar condomínio
            condominio = Condominio.query.get(condominio_id)
            if not condominio:
                logger.error(f"Condomínio {condominio_id} não encontrado")
                return None

            # Calcular horário de início e fim baseado nas rondas
            rondas = resultado_consolidacao["rondas"]
            if not rondas:
                logger.error("Nenhuma ronda para salvar no banco principal")
                return None

            # Buscar objetos RondaEsporadica originais para obter dados completos
            from app.models.ronda_esporadica import RondaEsporadica
            rondas_objetos = RondaEsporadica.query.filter_by(
                condominio_id=condominio_id,
                data_plantao=data_plantao
            ).all()
            
            if not rondas_objetos:
                logger.error("Nenhuma ronda esporádica encontrada no banco")
                return None

            # Primeira ronda (início do turno)
            primeira_ronda = min(rondas_objetos, key=lambda x: x.hora_entrada)
            # Última ronda (fim do turno)
            ultima_ronda = max(rondas_objetos, key=lambda x: x.hora_saida if x.hora_saida else time(0, 0))

            # Criar registro na tabela principal
            ronda_principal = Ronda(
                condominio_id=condominio_id,
                data_plantao_ronda=data_plantao,
                data_hora_inicio=datetime.combine(data_plantao, primeira_ronda.hora_entrada),
                data_hora_fim=datetime.combine(data_plantao, ultima_ronda.hora_saida) if ultima_ronda.hora_saida else None,
                duracao_total_rondas_minutos=resultado_consolidacao["duracao_total_minutos"],
                total_rondas_no_log=resultado_consolidacao["total_rondas"],
                log_ronda_bruto=f"Rondas esporádicas consolidadas - {resultado_consolidacao['total_rondas']} rondas realizadas",
                relatorio_processado=resultado_consolidacao["relatorio"],
                tipo="esporadica",  # Novo campo para identificar origem
                user_id=primeira_ronda.user_id,  # Usar ID do primeiro usuário
                supervisor_id=primeira_ronda.supervisor_id,
                turno_ronda=primeira_ronda.turno,
                escala_plantao=primeira_ronda.escala_plantao
            )

            # Adicionar log consolidado
            log_consolidado = RondaEsporadicaConsolidacaoService._gerar_log_consolidado(rondas_objetos)
            ronda_principal.log_bruto = log_consolidado
            ronda_principal.relatorio_processado = resultado_consolidacao["relatorio"]

            # Salvar no banco
            db.session.add(ronda_principal)
            db.session.commit()

            logger.info(f"Ronda principal criada com ID: {ronda_principal.id}")
            return ronda_principal.id

        except Exception as e:
            logger.error(f"Erro ao salvar no banco principal: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def _gerar_log_consolidado(rondas: List[RondaEsporadica]) -> str:
        """Gera log consolidado das rondas esporádicas."""
        log = "=== LOG CONSOLIDADO DE RONDAS ESPORÁDICAS ===\n\n"
        
        for i, ronda in enumerate(rondas, 1):
            log += f"RONDA {i}:\n"
            log += f"  Entrada: {ronda.hora_entrada_formatada}\n"
            log += f"  Saída: {ronda.hora_saida_formatada}\n"
            log += f"  Duração: {ronda.duracao_formatada}\n"
            log += f"  Status: {ronda.status}\n"
            log += f"  Observações: {ronda.observacoes or 'Nenhuma'}\n"
            log += f"  Usuário: {ronda.user.username if ronda.user else 'N/A'}\n"
            if ronda.supervisor:
                log += f"  Supervisor: {ronda.supervisor.username}\n"
            log += "\n"
        
        return log

    @staticmethod
    def marcar_rondas_como_processadas(condominio_id: int, data_plantao: datetime.date) -> bool:
        """Marca todas as rondas esporádicas como processadas após consolidação."""
        try:
            # Buscar todas as rondas esporádicas do dia
            rondas = RondaEsporadica.query.filter_by(
                condominio_id=condominio_id,
                data_plantao=data_plantao
            ).all()

            # Marcar como processadas
            for ronda in rondas:
                ronda.status = "processada"
                ronda.observacoes = (ronda.observacoes or "") + " [CONSOLIDADA]"

            db.session.commit()
            logger.info(f"Marcadas {len(rondas)} rondas como processadas")
            return True

        except Exception as e:
            logger.error(f"Erro ao marcar rondas como processadas: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def obter_estatisticas_consolidacao(condominio_id: int, data_inicio: datetime.date, data_fim: datetime.date) -> Dict[str, Any]:
        """Obtém estatísticas de consolidação para um período."""
        try:
            # Buscar rondas esporádicas no período
            rondas = RondaEsporadica.query.filter(
                RondaEsporadica.condominio_id == condominio_id,
                RondaEsporadica.data_plantao >= data_inicio,
                RondaEsporadica.data_plantao <= data_fim
            ).all()

            # Calcular estatísticas
            total_rondas = len(rondas)
            rondas_finalizadas = len([r for r in rondas if r.status == "finalizada"])
            rondas_processadas = len([r for r in rondas if r.status == "processada"])
            duracao_total = sum(r.duracao_minutos or 0 for r in rondas)

            # Buscar rondas principais criadas
            rondas_principais = Ronda.query.filter(
                Ronda.condominio_id == condominio_id,
                Ronda.data >= data_inicio,
                Ronda.data <= data_fim,
                Ronda.tipo == "esporadica"
            ).all()

            return {
                "sucesso": True,
                "periodo": {
                    "inicio": data_inicio.isoformat(),
                    "fim": data_fim.isoformat()
                },
                "estatisticas": {
                    "total_rondas_esporadicas": total_rondas,
                    "rondas_finalizadas": rondas_finalizadas,
                    "rondas_processadas": rondas_processadas,
                    "duracao_total_minutos": duracao_total,
                    "duracao_total_horas": duracao_total // 60,
                    "rondas_principais_criadas": len(rondas_principais)
                },
                "rondas_principais": [
                    {
                        "id": rp.id,
                        "data": rp.data.isoformat(),
                        "duracao_minutos": rp.duracao_minutos,
                        "total_rondas": rp.total_rondas
                    } for rp in rondas_principais
                ]
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                "sucesso": False,
                "message": f"Erro ao obter estatísticas: {str(e)}"
            } 