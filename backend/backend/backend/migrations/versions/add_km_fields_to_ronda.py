"""Adicionar campos de kilometragem na tabela ronda

Revision ID: add_km_fields_to_ronda
Revises: 
Create Date: 2024-09-30 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_km_fields_to_ronda'
down_revision = None  # Ajustar conforme a última migração
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona os novos campos de kilometragem na tabela ronda
    op.add_column('ronda', sa.Column('km_entrada', sa.Float(), nullable=True, comment='Quilometragem no momento da entrada no residencial'))
    op.add_column('ronda', sa.Column('km_saida', sa.Float(), nullable=True, comment='Quilometragem no momento da saída do residencial'))
    op.add_column('ronda', sa.Column('km_total_percorrido', sa.Float(), nullable=True, comment='Total de quilômetros percorridos durante a ronda'))
    op.add_column('ronda', sa.Column('data_hora_entrada', sa.DateTime(timezone=True), nullable=True, comment='Data e hora da entrada no residencial'))
    op.add_column('ronda', sa.Column('data_hora_saida', sa.DateTime(timezone=True), nullable=True, comment='Data e hora da saída do residencial'))


def downgrade():
    # Remove os campos de kilometragem
    op.drop_column('ronda', 'data_hora_saida')
    op.drop_column('ronda', 'data_hora_entrada')
    op.drop_column('ronda', 'km_total_percorrido')
    op.drop_column('ronda', 'km_saida')
    op.drop_column('ronda', 'km_entrada')

