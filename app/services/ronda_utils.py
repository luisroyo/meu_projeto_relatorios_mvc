import logging
import os
import re
from typing import Optional

from app import db
from app.models import Condominio, User
from sqlalchemy import func

logger = logging.getLogger(__name__)

class RondaUtils:
    @staticmethod
    def get_system_user() -> User:
        """Retorna ou cria um usuário 'Sistema Automatizado' para registro de rondas."""
        system_user = User.query.filter_by(username='Sistema Automatizado').first()
        if not system_user:
            # Crie um usuário com permissões adequadas (ex: is_admin=True ou is_supervisor=True)
            # É CRUCIAL USAR UMA SENHA SEGURA OU VARIÁVEL DE AMBIENTE PARA ISSO EM PRODUÇÃO
            system_user = User(username='Sistema Automatizado', email='system_auto@yourdomain.com', is_admin=True)
            # Use os.getenv para a senha em produção
            system_user.set_password(os.getenv('SYSTEM_USER_PASSWORD', 'super_secret_auto_password_dev'))
            db.session.add(system_user)
            db.session.commit()
            logger.info("Usuário 'Sistema Automatizado' criado.")
        return system_user

    @staticmethod
    def infer_condominio_from_filename(filename: str) -> Optional[Condominio]:
        """
        Tenta inferir o condomínio a partir do nome do arquivo.
        Ex: "AROSA.TXT" -> "AROSA"
            "AROSA RELATORIO.TXT" -> "AROSA"
        """
        condominio_name_raw = os.path.splitext(filename)[0]
        condominio_name_clean = re.sub(r'(?i)\s*(RELATORIOS|RELATORIO|RONDAS|RONDA)\s*', '', condominio_name_raw).strip()
        
        if not condominio_name_clean:
            logger.warning(f"Nome do condomínio vazio após limpeza do arquivo: {filename}")
            return None

        condominio = Condominio.query.filter(
            func.lower(Condominio.nome) == func.lower(condominio_name_clean)
        ).first()

        if condominio:
            logger.info(f"Condomínio '{condominio.nome}' identificado para o arquivo '{filename}'.")
            return condominio

        aliases = {
            "arosa": "Condomínio Arosa Residence",
            "horizonte": "Horizonte Azul",
            # Adicione outros aliases conforme necessário
        }
        
        condominio_name_for_alias_check = condominio_name_clean.lower()
        if condominio_name_for_alias_check in aliases:
            condominio = Condominio.query.filter(
                func.lower(Condominio.nome) == func.lower(aliases[condominio_name_for_alias_check])
            ).first()
            if condominio:
                logger.info(f"Condomínio '{condominio.nome}' identificado via alias para o arquivo '{filename}'.")
                return condominio

        logger.warning(
            f"Não foi possível encontrar um condomínio correspondente no banco de dados para o nome '{condominio_name_clean}' do arquivo '{filename}'."
        )
        return None

