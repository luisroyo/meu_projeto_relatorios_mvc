"""add_composite_indexes_and_views

Revision ID: 26266299674d
Revises: e4d785006823
Create Date: 2026-02-27 05:06:57.209723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
"""add_composite_indexes_and_views

Revision ID: 26266299674d
Revises: e4d785006823
Create Date: 2026-02-27 05:06:57.209723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26266299674d'
down_revision = 'e4d785006823'
branch_labels = None
depends_on = None


def upgrade():
    # Composite index for Whatsapp filtering
    op.create_index(
        'ix_whatsapp_condo_time',
        'whatsapp_message',
        ['condominio_id', 'timestamp'],
        unique=False
    )
    # Composite index for Ronda filtering
    op.create_index(
        'ix_ronda_condo_data',
        'ronda',
        ['condominio_id', 'data_plantao_ronda'],
        unique=False
    )

def downgrade():
    op.drop_index('ix_ronda_condo_data', table_name='ronda')
    op.drop_index('ix_whatsapp_condo_time', table_name='whatsapp_message')
