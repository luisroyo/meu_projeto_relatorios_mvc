"""add remaining production columns

Revision ID: e4d785006823
Revises: 6fd01c939d2f
Create Date: 2026-02-21 20:32:32.897393

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4d785006823'
down_revision = '6fd01c939d2f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('is_supervisor', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user', sa.Column('date_registered', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('user', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))

    op.add_column('ronda', sa.Column('data_hora', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ronda', sa.Column('km_entrada', sa.String(length=50), nullable=True))
    op.add_column('ronda', sa.Column('km_saida', sa.String(length=50), nullable=True))
    op.add_column('ronda', sa.Column('km_total_percorrido', sa.String(length=50), nullable=True))
    op.add_column('ronda', sa.Column('data_hora_entrada', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ronda', sa.Column('data_hora_saida', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ronda', sa.Column('observacoes', sa.Text(), nullable=True))
    op.add_column('ronda', sa.Column('localizacao_gps', sa.String(length=100), nullable=True))

    op.add_column('ocorrencia', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('ocorrencia', sa.Column('data_hora', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ocorrencia', sa.Column('tipo', sa.String(length=50), nullable=True))
    op.add_column('ocorrencia', sa.Column('descricao', sa.Text(), nullable=True))
    op.add_column('ocorrencia', sa.Column('gravidade', sa.String(length=20), server_default='Baixa', nullable=True))
    op.add_column('ocorrencia', sa.Column('acoes_tomadas', sa.Text(), nullable=True))
    op.add_column('ocorrencia', sa.Column('anexos_urls', sa.Text(), nullable=True))
    op.add_column('ocorrencia', sa.Column('resolvido_em', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ocorrencia', sa.Column('resolvido_por', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('ocorrencia', 'resolvido_por')
    op.drop_column('ocorrencia', 'resolvido_em')
    op.drop_column('ocorrencia', 'anexos_urls')
    op.drop_column('ocorrencia', 'acoes_tomadas')
    op.drop_column('ocorrencia', 'gravidade')
    op.drop_column('ocorrencia', 'descricao')
    op.drop_column('ocorrencia', 'tipo')
    op.drop_column('ocorrencia', 'data_hora')
    op.drop_column('ocorrencia', 'user_id')

    op.drop_column('ronda', 'localizacao_gps')
    op.drop_column('ronda', 'observacoes')
    op.drop_column('ronda', 'data_hora_saida')
    op.drop_column('ronda', 'data_hora_entrada')
    op.drop_column('ronda', 'km_total_percorrido')
    op.drop_column('ronda', 'km_saida')
    op.drop_column('ronda', 'km_entrada')
    op.drop_column('ronda', 'data_hora')

    op.drop_column('user', 'last_login')
    op.drop_column('user', 'date_registered')
    op.drop_column('user', 'is_admin')
    op.drop_column('user', 'is_supervisor')
