# Serviço para consolidar e exportar relatório de rondas no formato do prompt
# ATUALIZADO: Usando modelo Ronda unificado
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.services.ronda_format_utils import (
    agrupar_rondas_por_condominio_e_plantao,
    gerar_relatorio_formatado,
)
from app import db


def consolidar_relatorio_rondas(user_id=None, data_inicio=None, data_fim=None):
    """
    Consolida e gera relatório formatado de todas as rondas do período, agrupando por condomínio e plantão.
    Filtros opcionais: user_id, data_inicio, data_fim
    Retorna: lista de strings (um relatório por grupo)
    """
    from sqlalchemy import func
    
    query = Ronda.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if data_inicio:
        query = query.filter(func.date(Ronda.data_plantao_ronda) >= data_inicio)
    if data_fim:
        query = query.filter(func.date(Ronda.data_plantao_ronda) <= data_fim)
    rondas = query.order_by(
        Ronda.condominio_id,
        Ronda.data_plantao_ronda,
        Ronda.data_criacao,
    ).all()
    grupos = agrupar_rondas_por_condominio_e_plantao(rondas)
    relatorios = []
    for (condominio_id, data_plantao, plantao), grupo in grupos.items():
        cond = Condominio.query.get(condominio_id)
        nome_cond = cond.nome if cond else f"ID {condominio_id}"
        relatorio = gerar_relatorio_formatado(grupo, nome_cond, data_plantao, plantao)
        relatorios.append(relatorio)
    return relatorios
