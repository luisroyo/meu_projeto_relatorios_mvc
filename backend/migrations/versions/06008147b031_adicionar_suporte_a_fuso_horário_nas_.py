"""Adicionar suporte a fuso horário nas colunas

Revision ID: 06008147b031
Revises: c132b0092ad3
Create Date: 2025-07-09 23:45:51.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06008147b031'
down_revision = 'c132b0092ad3' # Verifique se este é o ID da sua migração anterior
branch_labels = None
depends_on = None

# --- DEFINIÇÃO DAS VIEWS (COLE AS DEFINIÇÕES REAIS AQUI SE FOREM DIFERENTES) ---

# View 1: vw_ocorrencias_detalhadas
view_definition = """
CREATE OR REPLACE VIEW vw_ocorrencias_detalhadas AS
SELECT
    o.id,
    o.data_hora_ocorrencia,
    o.turno,
    o.status,
    o.relatorio_final,
    c.nome AS condominio_nome,
    ot.nome AS tipo_ocorrencia_nome,
    u_reg.username AS registrado_por_username,
    u_sup.username AS supervisor_username
FROM
    ocorrencia o
LEFT JOIN condominio c ON o.condominio_id = c.id
LEFT JOIN ocorrencia_tipo ot ON o.ocorrencia_tipo_id = ot.id
LEFT JOIN "user" u_reg ON o.registrado_por_user_id = u_reg.id
LEFT JOIN "user" u_sup ON o.supervisor_id = u_sup.id;
"""
drop_view_sql = "DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;"

# View 2: mv_ocorrencias_por_condominio (Materialized View)
materialized_view_definition = """
CREATE MATERIALIZED VIEW mv_ocorrencias_por_condominio AS
SELECT
    c.id AS condominio_id,
    c.nome AS condominio_nome,
    count(o.id) AS total_ocorrencias,
    max(o.data_hora_ocorrencia) AS ultima_ocorrencia
FROM condominio c
JOIN ocorrencia o ON c.id = o.condominio_id
GROUP BY c.id, c.nome;
"""
drop_materialized_view_sql = "DROP MATERIALIZED VIEW IF EXISTS mv_ocorrencias_por_condominio;"


def upgrade():
    # ### Início da correção manual ###
    op.execute(drop_view_sql)
    op.execute(drop_materialized_view_sql)
    # ### Fim da correção manual ###

    with op.batch_alter_table('colaborador', schema=None) as batch_op:
        batch_op.alter_column('data_criacao',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('data_modificacao',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)

    with op.batch_alter_table('login_history', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False)

    with op.batch_alter_table('ocorrencia', schema=None) as batch_op:
        batch_op.alter_column('data_hora_ocorrencia',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
        batch_op.alter_column('data_criacao',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('data_modificacao',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)

    with op.batch_alter_table('processing_history', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False)

    with op.batch_alter_table('ronda', schema=None) as batch_op:
        batch_op.alter_column('data_hora_inicio',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False)
        batch_op.alter_column('data_hora_fim',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('primeiro_evento_log_dt',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('ultimo_evento_log_dt',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('date_registered',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
        batch_op.alter_column('last_login',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)

    # ### Início da correção manual ###
    op.execute(view_definition)
    op.execute(materialized_view_definition)
    # ### Fim da correção manual ###


def downgrade():
    # ### Início da correção manual ###
    op.execute(drop_view_sql)
    op.execute(drop_materialized_view_sql)
    # ### Fim da correção manual ###

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('last_login',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('date_registered',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)

    with op.batch_alter_table('ronda', schema=None) as batch_op:
        batch_op.alter_column('ultimo_evento_log_dt',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('primeiro_evento_log_dt',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('data_hora_fim',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('data_hora_inicio',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               nullable=False)

    with op.batch_alter_table('processing_history', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               nullable=False)

    with op.batch_alter_table('ocorrencia', schema=None) as batch_op:
        batch_op.alter_column('data_modificacao',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('data_criacao',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('data_hora_ocorrencia',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('login_history', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               nullable=False)

    with op.batch_alter_table('colaborador', schema=None) as batch_op:
        batch_op.alter_column('data_modificacao',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('data_criacao',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.TIMESTAMP(),
               existing_nullable=True)

    # ### Início da correção manual ###
    op.execute(view_definition)
    op.execute(materialized_view_definition)
    # ### Fim da correção manual ###
