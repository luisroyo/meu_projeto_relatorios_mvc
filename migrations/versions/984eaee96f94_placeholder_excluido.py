"""Placeholder para a migração 984eaee96f94 que foi intencionalmente excluída."""
from alembic import op
import sqlalchemy as sa

# !!! IMPORTANTE: ESCOLHA A OPÇÃO CORRETA ABAIXO !!!

# OPÇÃO 1: Se 984eaee96f94 foi a PRIMEIRA migração:
# down_revision = None

# OPÇÃO 2: Se havia uma migração ANTES (substitua 'ID_REAL_DA_MIGRACAO_ANTERIOR' pelo ID correto):
# Exemplo: down_revision = 'abcdef12345'
down_revision = None # <--- SUBSTITUA AQUI PELA OPÇÃO CORRETA: None ou 'ID_REAL_DA_MIGRACAO_ANTERIOR'

revision = '984eaee96f94' # Mantém o ID da migração excluída
branch_labels = None
depends_on = None

def upgrade():
    # Esta função fica vazia.
    # As alterações da migração original ou já estão no banco (se foi aplicada)
    # ou não são mais desejadas e foram/serão revertidas de outra forma.
    print(f"INFO: Pulando a migração {revision} (placeholder para arquivo excluído).")
    pass

def downgrade():
    # Esta função também pode ficar vazia, ou se você souber como reverter
    # as alterações da 984eaee96f94 e quiser manter essa lógica, coloque aqui.
    # Principalmente para manter a cadeia de downgrade consistente.
    print(f"INFO: Pulando downgrade da migração {revision} (placeholder para arquivo excluído).")
    pass