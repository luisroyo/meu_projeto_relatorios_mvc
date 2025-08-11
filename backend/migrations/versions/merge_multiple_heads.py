"""merge multiple heads

Revision ID: merge_multiple_heads
Revises: update_view_relatorio_final, 7eac948b9e42
Create Date: 2025-08-11 01:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_multiple_heads'
down_revision = ('update_view_relatorio_final', '7eac948b9e42')
branch_labels = None
depends_on = None

def upgrade():
    # Esta é uma migração de merge, não faz alterações no banco
    # Apenas consolida as duas branches de migração
    pass

def downgrade():
    # Não é possível fazer downgrade de uma migração de merge
    pass
