"""Schema inicial para banco de dados de desenvolvimento

Revision ID: 735fd4b237dc
Revises: 
Create Date: 2025-06-05 10:57:53.604836

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '735fd4b237dc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('colaborador',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome_completo', sa.String(length=150), nullable=False),
    sa.Column('cargo', sa.String(length=100), nullable=False),
    sa.Column('matricula', sa.String(length=50), nullable=True),
    sa.Column('data_admissao', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('data_criacao', sa.DateTime(), nullable=True),
    sa.Column('data_modificacao', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('colaborador', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_colaborador_cargo'), ['cargo'], unique=False)
        batch_op.create_index(batch_op.f('ix_colaborador_matricula'), ['matricula'], unique=True)
        batch_op.create_index(batch_op.f('ix_colaborador_nome_completo'), ['nome_completo'], unique=False)

    op.create_table('condominio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=150), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('condominio', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_condominio_nome'), ['nome'], unique=True)

    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('is_approved', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('date_registered', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('login_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('attempted_username', sa.String(length=120), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=256), nullable=True),
    sa.Column('failure_reason', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('login_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_login_history_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_login_history_user_id'), ['user_id'], unique=False)

    op.create_table('ronda',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data_hora_inicio', sa.DateTime(), nullable=False),
    sa.Column('data_hora_fim', sa.DateTime(), nullable=True),
    sa.Column('log_ronda_bruto', sa.Text(), nullable=False),
    sa.Column('relatorio_processado', sa.Text(), nullable=True),
    sa.Column('condominio', sa.String(length=150), nullable=True),
    sa.Column('escala_plantao', sa.String(length=100), nullable=True),
    sa.Column('data_plantao_ronda', sa.Date(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ronda')
    with op.batch_alter_table('login_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_login_history_user_id'))
        batch_op.drop_index(batch_op.f('ix_login_history_timestamp'))

    op.drop_table('login_history')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    with op.batch_alter_table('condominio', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_condominio_nome'))

    op.drop_table('condominio')
    with op.batch_alter_table('colaborador', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_colaborador_nome_completo'))
        batch_op.drop_index(batch_op.f('ix_colaborador_matricula'))
        batch_op.drop_index(batch_op.f('ix_colaborador_cargo'))

    op.drop_table('colaborador')
    # ### end Alembic commands ###
