# Arquivo para comandos específicos de rondas
import logging
import os
import re
import click
from flask.cli import with_appcontext
from datetime import datetime
from app import db
from app.models import Ronda

logger = logging.getLogger(__name__)


@click.command("verificar-alertas-rondas")
@click.option("--output", "-o", default=None,
              help="Caminho do arquivo de saída para salvar relatório (opcional)")
@click.option("--condominio-id", "-c", type=int, default=None,
              help="Filtrar por ID do condomínio (opcional)")
@click.option("--data-inicio", "-di",
              help="Data de início no formato YYYY-MM-DD (opcional)")
@click.option("--data-fim", "-df",
              help="Data de fim no formato YYYY-MM-DD (opcional)")
@with_appcontext
def verificar_alertas_rondas_command(output, condominio_id, data_inicio, data_fim):
    """
    Varre todas as rondas salvas no banco de dados e identifica quais têm alertas de erro.
    
    Os alertas são encontrados no campo relatorio_processado das rondas e indicam problemas
    como: rondas sem início, rondas sem término, horários inconsistentes, etc.
    
    Exemplos:
        flask verificar-alertas-rondas
        flask verificar-alertas-rondas -o relatorio_alertas.txt
        flask verificar-alertas-rondas --condominio-id 1
        flask verificar-alertas-rondas --data-inicio 2025-01-01 --data-fim 2025-12-31
    """
    try:
        # Constrói a query base
        query = Ronda.query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.id.desc())
        
        # Aplica filtros se fornecidos
        if condominio_id:
            query = query.filter(Ronda.condominio_id == condominio_id)
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d").date()
                query = query.filter(Ronda.data_plantao_ronda >= data_inicio_dt)
            except ValueError:
                click.echo(f"❌ Erro: Data de início inválida. Use o formato YYYY-MM-DD")
                return
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d").date()
                query = query.filter(Ronda.data_plantao_ronda <= data_fim_dt)
            except ValueError:
                click.echo(f"❌ Erro: Data de fim inválida. Use o formato YYYY-MM-DD")
                return
        
        # Busca todas as rondas
        rondas = query.all()
        
        if not rondas:
            click.echo("⚠️  Nenhuma ronda encontrada com os filtros especificados.")
            return
        
        click.echo(f"📊 Verificando {len(rondas)} ronda(s)...")
        
        # Padrões para identificar alertas
        padrao_secao_alertas = re.compile(
            r'Observações/Alertas de Pareamento:',
            re.IGNORECASE
        )
        padrao_alerta = re.compile(
            r'⚠️\s*(.+?)(?=\n|$)',
            re.MULTILINE
        )
        padrao_alerta_horario = re.compile(
            r'ALERTA DE HORÁRIO',
            re.IGNORECASE
        )
        
        rondas_com_alertas = []
        total_alertas = 0
        
        # Processa cada ronda
        for ronda in rondas:
            if not ronda.relatorio_processado:
                continue
            
            relatorio = ronda.relatorio_processado
            
            # Verifica se há seção de alertas
            if padrao_secao_alertas.search(relatorio):
                # Extrai os alertas
                alertas_encontrados = []
                
                # Encontra a posição da seção de alertas
                match_secao = padrao_secao_alertas.search(relatorio)
                if match_secao:
                    # Pega o texto a partir da seção de alertas
                    texto_alertas = relatorio[match_secao.end():]
                    
                    # Extrai cada alerta (linhas que começam com "- ⚠️")
                    linhas = texto_alertas.split('\n')
                    for linha in linhas:
                        linha = linha.strip()
                        if linha.startswith('- ⚠️') or linha.startswith('⚠️'):
                            # Remove o prefixo "- ⚠️" ou "⚠️"
                            alerta_limpo = re.sub(r'^-\s*⚠️\s*', '', linha)
                            alerta_limpo = re.sub(r'^⚠️\s*', '', alerta_limpo)
                            if alerta_limpo:
                                alertas_encontrados.append(alerta_limpo)
                
                if alertas_encontrados:
                    rondas_com_alertas.append({
                        'ronda': ronda,
                        'alertas': alertas_encontrados,
                        'total_alertas': len(alertas_encontrados)
                    })
                    total_alertas += len(alertas_encontrados)
        
        # Prepara o relatório
        linhas_relatorio = []
        linhas_relatorio.append("=" * 100)
        linhas_relatorio.append("RELATÓRIO DE VARREURA DE ALERTAS EM RONDAS")
        linhas_relatorio.append(f"Data da Verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas_relatorio.append(f"Total de Rondas Verificadas: {len(rondas)}")
        linhas_relatorio.append(f"Rondas com Alertas: {len(rondas_com_alertas)}")
        linhas_relatorio.append(f"Total de Alertas Encontrados: {total_alertas}")
        if condominio_id:
            linhas_relatorio.append(f"Filtro: Condomínio ID = {condominio_id}")
        if data_inicio or data_fim:
            linhas_relatorio.append(f"Período: {data_inicio or 'Início'} até {data_fim or 'Fim'}")
        linhas_relatorio.append("=" * 100)
        linhas_relatorio.append("")
        
        if not rondas_com_alertas:
            linhas_relatorio.append("✅ Nenhuma ronda com alertas encontrada!")
            linhas_relatorio.append("")
        else:
            # Agrupa por tipo de alerta
            tipos_alertas = {
                'horario': [],
                'sem_inicio': [],
                'sem_termino': [],
                'outros': []
            }
            
            for item in rondas_com_alertas:
                ronda = item['ronda']
                alertas = item['alertas']
                
                for alerta in alertas:
                    if 'ALERTA DE HORÁRIO' in alerta.upper() or 'ocorreu ANTES' in alerta:
                        tipos_alertas['horario'].append((ronda, alerta))
                    elif 'sem início' in alerta.lower() or 'sem inicio' in alerta.lower():
                        tipos_alertas['sem_inicio'].append((ronda, alerta))
                    elif 'sem término' in alerta.lower() or 'sem termino' in alerta.lower():
                        tipos_alertas['sem_termino'].append((ronda, alerta))
                    else:
                        tipos_alertas['outros'].append((ronda, alerta))
            
            # Resumo por tipo
            linhas_relatorio.append("📊 RESUMO POR TIPO DE ALERTA:")
            linhas_relatorio.append("-" * 100)
            linhas_relatorio.append(f"  ⚠️  Alertas de Horário: {len(tipos_alertas['horario'])}")
            linhas_relatorio.append(f"  ⚠️  Rondas sem Início: {len(tipos_alertas['sem_inicio'])}")
            linhas_relatorio.append(f"  ⚠️  Rondas sem Término: {len(tipos_alertas['sem_termino'])}")
            linhas_relatorio.append(f"  ⚠️  Outros Alertas: {len(tipos_alertas['outros'])}")
            linhas_relatorio.append("")
            
            # Lista detalhada de rondas com alertas
            linhas_relatorio.append("📋 LISTA DETALHADA DE RONDAS COM ALERTAS:")
            linhas_relatorio.append("=" * 100)
            
            for i, item in enumerate(rondas_com_alertas, 1):
                ronda = item['ronda']
                alertas = item['alertas']
                
                data_plantao = ronda.data_plantao_ronda.strftime('%d/%m/%Y') if ronda.data_plantao_ronda else "N/A"
                condominio_nome = ronda.condominio.nome if ronda.condominio else "N/A"
                supervisor_nome = ronda.supervisor.username if ronda.supervisor else "N/A"
                turno = ronda.turno_ronda or "N/A"
                
                linhas_relatorio.append(f"\n{i}. RONDA ID #{ronda.id}")
                linhas_relatorio.append(f"   📅 Data do Plantão: {data_plantao}")
                linhas_relatorio.append(f"   🏢 Condomínio: {condominio_nome} (ID: {ronda.condominio_id})")
                linhas_relatorio.append(f"   👨‍💼 Supervisor: {supervisor_nome}")
                linhas_relatorio.append(f"   ⏰ Turno: {turno}")
                linhas_relatorio.append(f"   📊 Total de Rondas no Log: {ronda.total_rondas_no_log or 0}")
                linhas_relatorio.append(f"   ⚠️  Total de Alertas: {item['total_alertas']}")
                linhas_relatorio.append("")
                linhas_relatorio.append("   ALERTAS ENCONTRADOS:")
                for j, alerta in enumerate(alertas, 1):
                    # Limita o tamanho do alerta para melhor visualização
                    alerta_exibido = alerta[:200] + "..." if len(alerta) > 200 else alerta
                    linhas_relatorio.append(f"      {j}. {alerta_exibido}")
                linhas_relatorio.append("-" * 100)
        
        # Adiciona rodapé
        linhas_relatorio.append("")
        linhas_relatorio.append("=" * 100)
        linhas_relatorio.append(f"Fim do Relatório - {len(rondas_com_alertas)} ronda(s) com alerta(s)")
        linhas_relatorio.append("=" * 100)
        
        # Exibe no console
        conteudo = "\n".join(linhas_relatorio)
        click.echo(conteudo)
        
        # Salva em arquivo se solicitado
        if output:
            output_dir = os.path.dirname(output) if os.path.dirname(output) else "."
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            tamanho_arquivo = os.path.getsize(output)
            click.echo(f"\n✅ Relatório salvo em: {os.path.abspath(output)}")
            click.echo(f"💾 Tamanho: {tamanho_arquivo:,} bytes")
        
        # Resumo final
        click.echo(f"\n📊 RESUMO:")
        click.echo(f"   Total de rondas verificadas: {len(rondas)}")
        click.echo(f"   Rondas com alertas: {len(rondas_com_alertas)}")
        click.echo(f"   Total de alertas: {total_alertas}")
        
        if len(rondas_com_alertas) > 0:
            porcentagem = (len(rondas_com_alertas) / len(rondas)) * 100
            click.echo(f"   Porcentagem com alertas: {porcentagem:.1f}%")
        
    except Exception as e:
        click.echo(f"❌ Erro ao verificar alertas: {e}")
        logger.error(f"Erro no comando verificar-alertas-rondas: {e}", exc_info=True) 