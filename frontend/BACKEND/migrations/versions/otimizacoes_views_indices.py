"""otimizacoes_views_indices

Revision ID: otimizacoes_views_indices
Revises: c69d0ffcff85
Create Date: 2025-07-12 15:20:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'otimizacoes_views_indices'
down_revision = 'c69d0ffcff85'
branch_labels = None
depends_on = None

def upgrade():
    # DROP views/triggers para recriar sem conflito
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ocorrencias_por_condominio;")
    op.execute("DROP TRIGGER IF EXISTS trg_update_ocorrencia ON ocorrencia;")
    op.execute("DROP FUNCTION IF EXISTS atualizar_data_modificacao();")
    op.execute("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;")
    op.execute("DROP VIEW IF EXISTS vw_colaboradores;")
    op.execute("DROP VIEW IF EXISTS vw_logradouros;")
    
    # Criar view detalhada de ocorrencias
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

    # Criar função para atualizar data_modificacao
    op.execute("""
    CREATE FUNCTION atualizar_data_modificacao()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.data_modificacao = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Criar trigger que usa a função para atualizar data_modificacao
    op.execute("""
    CREATE TRIGGER trg_update_ocorrencia
    BEFORE UPDATE ON ocorrencia
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_data_modificacao();
    """)

    # Criar materialized view com contagem de ocorrencias por condominio
    op.execute("""
    CREATE MATERIALIZED VIEW mv_ocorrencias_por_condominio AS
    SELECT 
        condominio_id,
        COUNT(*) AS total_ocorrencias,
        MAX(data_hora_ocorrencia) AS ultima_ocorrencia
    FROM ocorrencia
    GROUP BY condominio_id;
    """)

    # Criar view de colaboradores
    op.execute("""
    CREATE VIEW vw_colaboradores AS
    SELECT 
        id,
        nome_completo,
        cargo,
        matricula,
        data_admissao,
        status,
        data_criacao,
        data_modificacao
    FROM colaborador;
    """)
    # Criar view de logradouros
    op.execute("""
    CREATE VIEW vw_logradouros AS
    SELECT 
        id,
        nome
    FROM logradouro;
    """)

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ocorrencias_por_condominio;")
    op.execute("DROP TRIGGER IF EXISTS trg_update_ocorrencia ON ocorrencia;")
    op.execute("DROP FUNCTION IF EXISTS atualizar_data_modificacao();")
    op.execute("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas;")
    op.execute("DROP VIEW IF EXISTS vw_colaboradores;")
    op.execute("DROP VIEW IF EXISTS vw_logradouros;")
