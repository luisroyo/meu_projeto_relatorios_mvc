"""Merge das migrations 06008147b031 e otimizacoes_views_indices

Revision ID: dc0697d2a16b
Revises: 06008147b031, otimizacoes_views_indices
Create Date: 2025-07-12 15:11:42.373710

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc0697d2a16b'
down_revision = ('06008147b031', 'otimizacoes_views_indices')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
