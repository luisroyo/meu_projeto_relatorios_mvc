"""Merge heads

Revision ID: 2efe6c34fc62
Revises: 01eaf0d6f0fd, add_tipo_field_to_ronda
Create Date: 2025-08-01 02:19:08.789514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2efe6c34fc62'
down_revision = ('01eaf0d6f0fd', 'add_tipo_field_to_ronda')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
