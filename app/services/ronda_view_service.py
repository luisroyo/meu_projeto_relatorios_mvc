from app import db
from app.models.vw_rondas_detalhadas import VWRondasDetalhadas
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RondaViewService:
    """Serviço para consultas usando a view de rondas detalhadas."""
    
    @staticmethod
    def get_rondas_por_periodo(data_inicio, data_fim):
        """Busca rondas por período usando a view."""
        try:
            return VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.data_plantao_ronda >= data_inicio,
                VWRondasDetalhadas.data_plantao_ronda <= data_fim
            ).order_by(desc(VWRondasDetalhadas.data_plantao_ronda)).all()
        except Exception as e:
            logger.error(f"Erro ao buscar rondas por período: {e}")
            return []
    
    @staticmethod
    def get_rondas_por_condominio(condominio_id):
        """Busca todas as rondas de um condomínio específico."""
        try:
            return VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.condominio_id == condominio_id
            ).order_by(desc(VWRondasDetalhadas.data_plantao_ronda)).all()
        except Exception as e:
            logger.error(f"Erro ao buscar rondas por condomínio: {e}")
            return []
    
    @staticmethod
    def get_rondas_por_usuario(user_id):
        """Busca todas as rondas de um usuário específico."""
        try:
            return VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.user_id == user_id
            ).order_by(desc(VWRondasDetalhadas.data_plantao_ronda)).all()
        except Exception as e:
            logger.error(f"Erro ao buscar rondas por usuário: {e}")
            return []
    
    @staticmethod
    def get_rondas_em_andamento():
        """Busca todas as rondas em andamento."""
        try:
            return VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.status_ronda == 'em_andamento'
            ).order_by(desc(VWRondasDetalhadas.data_hora_inicio)).all()
        except Exception as e:
            logger.error(f"Erro ao buscar rondas em andamento: {e}")
            return []
    
    @staticmethod
    def get_estatisticas_rondas():
        """Retorna estatísticas gerais das rondas."""
        try:
            # Total de rondas
            total_rondas = VWRondasDetalhadas.query.count()
            
            # Rondas por status
            em_andamento = VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.status_ronda == 'em_andamento'
            ).count()
            
            finalizadas = VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.status_ronda == 'finalizada'
            ).count()
            
            # Duração média
            duracao_media = db.session.query(
                func.avg(VWRondasDetalhadas.duracao_horas)
            ).filter(
                VWRondasDetalhadas.duracao_horas.isnot(None)
            ).scalar()
            
            # Total de rondas por tipo
            tradicionais = VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.tipo == 'tradicional'
            ).count()
            
            esporadicas = VWRondasDetalhadas.query.filter(
                VWRondasDetalhadas.tipo == 'esporadica'
            ).count()
            
            return {
                'total_rondas': total_rondas,
                'em_andamento': em_andamento,
                'finalizadas': finalizadas,
                'duracao_media_horas': float(duracao_media) if duracao_media else 0,
                'tradicionais': tradicionais,
                'esporadicas': esporadicas
            }
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}
    
    @staticmethod
    def get_top_condominios_rondas(limit=5):
        """Retorna os condomínios com mais rondas."""
        try:
            return db.session.query(
                VWRondasDetalhadas.condominio_nome,
                func.count(VWRondasDetalhadas.id).label('total_rondas')
            ).group_by(
                VWRondasDetalhadas.condominio_nome
            ).order_by(
                desc(func.count(VWRondasDetalhadas.id))
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Erro ao buscar top condomínios: {e}")
            return []
    
    @staticmethod
    def get_rondas_recentes(limit=10):
        """Retorna as rondas mais recentes."""
        try:
            return VWRondasDetalhadas.query.order_by(
                desc(VWRondasDetalhadas.data_hora_inicio)
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Erro ao buscar rondas recentes: {e}")
            return [] 