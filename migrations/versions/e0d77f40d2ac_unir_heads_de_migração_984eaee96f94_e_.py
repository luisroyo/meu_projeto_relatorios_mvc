"""Unir heads de migração 984eaee96f94 e fc78a162677a

Revision ID: e0d77f40d2ac
Revises: 984eaee96f94, fc78a162677a
Create Date: 2025-05-29 19:21:33.360875

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0d77f40d2ac'
down_revision = ('984eaee96f94', 'fc78a162677a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
