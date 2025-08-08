from flask import request, session, current_app
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity
from app.models.user_online import UserOnline
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def track_user_activity():
    """Middleware para rastrear atividade dos usuários."""
    try:
        user_id = None
        username = None
        
        # Verifica se usuário está autenticado via Flask-Login
        if current_user.is_authenticated:
            user_id = current_user.id
            username = current_user.username
        else:
            # Verifica se usuário está autenticado via JWT
            try:
                jwt_user_id = get_jwt_identity()
                if jwt_user_id:
                    user = User.query.get(jwt_user_id)
                    if user:
                        user_id = user.id
                        username = user.username
            except Exception as jwt_error:
                # JWT não válido ou não presente, continua normalmente
                pass
        
        # Só rastreia se o usuário estiver autenticado
        if user_id and username:
            # Obtém informações da sessão e request
            session_id = str(session.get('_id', hash(request.remote_addr + str(user_id))))
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            # Log para debug (apenas em desenvolvimento)
            if current_app.debug:
                logger.debug(f"Rastreando atividade: User={username}, Session={session_id[:10]}...")
            
            # Atualiza atividade do usuário
            UserOnline.update_activity(
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log de sucesso para debug
            if current_app.debug:
                logger.debug(f"Atividade registrada com sucesso para {username}")
            
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
        try:
            if current_user.is_authenticated:
                logger.error(f"Detalhes do erro - User ID: {current_user.id}, Session: {session.get('_id', 'N/A')}")
            else:
                logger.error("Erro ocorreu com usuário não autenticado")
        except:
            logger.error("Erro ao obter detalhes do usuário para log")

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