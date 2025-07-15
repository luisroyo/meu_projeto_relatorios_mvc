# app/services/user_service.py
from app import db
from app.models import LoginHistory, ProcessingHistory, Ronda, User


def delete_user_and_dependencies(user_id):
    """
    Deleta um usuário e todos os seus registros dependentes.
    Retorna (True, 'Mensagem de sucesso') ou (False, 'Mensagem de erro').
    """
    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        return False, f"Usuário com ID {user_id} não encontrado."

    try:
        # Deleta os registros dependentes
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete()
        Ronda.query.filter_by(user_id=user_to_delete.id).delete()
        ProcessingHistory.query.filter_by(user_id=user_to_delete.id).delete()

        # Deleta o usuário
        db.session.delete(user_to_delete)

        db.session.commit()
        return (
            True,
            f"Usuário {user_to_delete.username} e seus dados foram deletados com sucesso.",
        )

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao deletar usuário: {str(e)}"
