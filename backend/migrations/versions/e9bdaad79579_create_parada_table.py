"""create_parada_table

Revision ID: e9bdaad79579
Revises: 26266299674d
Create Date: 2026-07-03 02:22:48.661848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9bdaad79579'
down_revision = '26266299674d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'parada' not in inspector.get_table_names():
        op.create_table('parada',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('data_hora_inicio', sa.DateTime(timezone=True), nullable=False),
            sa.Column('data_hora_fim', sa.DateTime(timezone=True), nullable=True),
            sa.Column('log_parada_bruto', sa.Text(), nullable=False),
            sa.Column('relatorio_processado', sa.Text(), nullable=True),
            sa.Column('condominio_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('supervisor_id', sa.Integer(), nullable=True),
            sa.Column('turno_parada', sa.String(length=50), nullable=True),
            sa.Column('escala_plantao', sa.String(length=100), nullable=True),
            sa.Column('data_plantao_parada', sa.Date(), nullable=True),
            sa.Column('total_paradas_no_log', sa.Integer(), nullable=True),
            sa.Column('primeiro_evento_log_dt', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ultimo_evento_log_dt', sa.DateTime(timezone=True), nullable=True),
            sa.Column('duracao_total_paradas_minutos', sa.Integer(), nullable=True),
            sa.Column('tipo', sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(['condominio_id'], ['condominio.id'], ),
            sa.ForeignKeyConstraint(['supervisor_id'], ['user.id'], name='fk_parada_supervisor_id'),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_parada_criador_id'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('parada', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_parada_condominio_id'), ['condominio_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_parada_data_plantao_parada'), ['data_plantao_parada'], unique=False)
            batch_op.create_index(batch_op.f('ix_parada_supervisor_id'), ['supervisor_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_parada_turno_parada'), ['turno_parada'], unique=False)
            batch_op.create_index(batch_op.f('ix_parada_user_id'), ['user_id'], unique=False)


def downgrade():
    pass
