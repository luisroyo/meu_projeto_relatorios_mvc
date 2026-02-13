"""update_view_relatorio_final

Revision ID: update_view_relatorio_final
Revises: c132b0092ad3
Create Date: 2025-01-27 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_view_relatorio_final'
down_revision = 'c132b0092ad3'
branch_labels = None
depends_on = None

def upgrade():
    # Abordagem mais segura: dropar e recriar a view
    # Primeiro, dropar a view existente
    op.execute("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;")
    
    # Agora criar a nova view com a estrutura correta
    op.execute("""
    CREATE VIEW vw_ocorrencias_detalhadas AS
    SELECT 
        o.id,
        o.data_hora_ocorrencia,
        o.status,
        o.turno,
        o.endereco_especifico,
        t.nome AS tipo,
        c.nome AS condominio,
        u.username AS registrado_por,
        s.username AS supervisor,
        o.relatorio_final
    FROM 
        ocorrencia o
    LEFT JOIN ocorrencia_tipo t ON o.ocorrencia_tipo_id = t.id
    LEFT JOIN condominio c ON o.condominio_id = c.id
    LEFT JOIN "user" u ON o.registrado_por_user_id = u.id
    LEFT JOIN "user" s ON o.supervisor_id = s.id;
    """)

def downgrade():
    # Reverter para a view original sem relatorio_final
    op.execute("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;")
    
    op.execute("""
    CREATE VIEW vw_ocorrencias_detalhadas AS
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
