from flask import request, session, current_app
from flask_login import current_user
from app.models.user_online import UserOnline
import logging

logger = logging.getLogger(__name__)

def track_user_activity():
    """Middleware para rastrear atividade dos usuários."""
    try:
        # Só rastreia se o usuário estiver autenticado
        if current_user.is_authenticated:
            # Obtém informações da sessão e request
            session_id = str(session.get('_id', hash(request.remote_addr + str(current_user.id))))
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            # Log para debug (apenas em desenvolvimento)
            if current_app.debug:
                logger.debug(f"Rastreando atividade: User={current_user.username}, Session={session_id[:10]}...")
            
            # Atualiza atividade do usuário
            UserOnline.update_activity(
                user_id=current_user.id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log de sucesso para debug
            if current_app.debug:
                logger.debug(f"Atividade registrada com sucesso para {current_user.username}")
            
            # Limpa sessões antigas periodicamente (a cada 10% das requisições)
            import random
            if random.randint(1, 10) == 1:
                UserOnline.cleanup_old_sessions()
        else:
            # Log quando usuário não está autenticado
            if current_app.debug:
                logger.debug("Usuário não autenticado, pulando rastreamento")
                
    except Exception as e:
        logger.error(f"Erro ao rastrear atividade do usuário: {e}")
        # Log mais detalhado em caso de erro
        if current_user.is_authenticated:
            logger.error(f"Detalhes do erro - User ID: {current_user.id}, Session: {session.get('_id', 'N/A')}")
        else:
            logger.error("Erro ocorreu com usuário não autenticado")

def get_online_users_count():
    """Retorna o número de usuários online."""
    try:
        online_users = UserOnline.get_online_users()
        return len(online_users)
    except Exception as e:
        logger.error(f"Erro ao obter contagem de usuários online: {e}")
        return 0

def get_online_users_list():
    """Retorna lista de usuários online."""
    try:
        return UserOnline.get_online_users()
    except Exception as e:
        logger.error(f"Erro ao obter lista de usuários online: {e}")
        return [] 