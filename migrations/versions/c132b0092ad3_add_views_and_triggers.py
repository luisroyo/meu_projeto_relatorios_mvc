"""add_views_and_triggers

Revision ID: c132b0092ad3
Revises: c69d0ffcff85
Create Date: 2025-07-03 16:42:24.658521
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c132b0092ad3'
down_revision = 'c69d0ffcff85'
branch_labels = None
depends_on = None

def upgrade():
    # VIEW: vw_ocorrencias_detalhadas
    op.execute("""
    CREATE OR REPLACE VIEW vw_ocorrencias_detalhadas AS
    SELECT 
        o.id,
        o.data_hora_ocorrencia,
        o.status,
        o.turno,
        o.endereco_especifico,
        t.nome AS tipo,
        c.nome AS condominio,
        u.username AS registrado_por,
        s.username AS supervisor
    FROM 
        ocorrencia o
    LEFT JOIN ocorrencia_tipo t ON o.ocorrencia_tipo_id = t.id
    LEFT JOIN condominio c ON o.condominio_id = c.id
    LEFT JOIN "user" u ON o.registrado_por_user_id = u.id
    LEFT JOIN "user" s ON o.supervisor_id = s.id;
    """)

    # FUNÇÃO para atualizar data_modificacao automaticamente
    op.execute("""
    CREATE OR REPLACE FUNCTION atualizar_data_modificacao()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.data_modificacao = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # TRIGGER para data_modificacao na tabela ocorrencia
    op.execute("""
    CREATE TRIGGER trg_update_ocorrencia
    BEFORE UPDATE ON ocorrencia
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_data_modificacao();
    """)

    # MATERIALIZED VIEW: mv_ocorrencias_por_condominio
    op.execute("""
    CREATE MATERIALIZED VIEW mv_ocorrencias_por_condominio AS
    SELECT 
        condominio_id,
        COUNT(*) AS total_ocorrencias,
        MAX(data_hora_ocorrencia) AS ultima_ocorrencia
    FROM ocorrencia
    GROUP BY condominio_id;
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ocorrencias_por_condominio;")
    op.execute("DROP TRIGGER IF EXISTS trg_update_ocorrencia ON ocorrencia;")
    op.execute("DROP FUNCTION IF EXISTS atualizar_data_modificacao;")
    op.execute("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;")
