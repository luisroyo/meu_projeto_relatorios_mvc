# app/services/report/ronda_service.py
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from .builder import ReportBuilder

logger = logging.getLogger(__name__)


class RondaReportService:
    """Serviço para geração de relatórios PDF do dashboard de rondas."""

    def __init__(self):
        self.builder = ReportBuilder()

    def generate_ronda_dashboard_pdf(self, dashboard_data: Dict, filters_info: Optional[Dict] = None) -> BytesIO:
        """Gera relatório PDF do dashboard de rondas."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=50,  # Reduzido de 72 para 50
                leftMargin=50,   # Reduzido de 72 para 50
                topMargin=80,    # Reduzido de 120 para 80
                bottomMargin=50  # Reduzido de 60 para 50
            )

            story = []

            # Capa
            periodo_inicio = filters_info.get("data_inicio", "") if filters_info else ""
            periodo_fim = filters_info.get("data_fim", "") if filters_info else ""
            story.extend(self.builder.create_cover_page(
                "Relatório de Dashboard - Rondas",
                "Assistente IA Seg",
                periodo_inicio,
                periodo_fim
            ))

            # Informações de geração
            story.extend(self.builder.add_generation_info())

            # Filtros
            story.extend(self.builder.format_filters_section(filters_info))

            # KPIs
            kpi_data = [
                ['Indicador', 'Valor', 'Descrição'],
                ['Total de Rondas', str(dashboard_data.get('total_rondas', 0)), 'Soma total de rondas no período'],
                ['Média por Dia', f"{dashboard_data.get('media_rondas_dia', 0)}", 'Média de rondas por dia trabalhado'],
                ['Duração Média', f"{dashboard_data.get('duracao_media_geral', 0)} min", 'Tempo médio por ronda'],
                ['Supervisor Mais Ativo', dashboard_data.get('supervisor_mais_ativo', 'N/A'), 'Supervisor com mais rondas']
            ]
            story.extend(self.builder.create_kpi_table(kpi_data))

            # Informações do período
            if dashboard_data.get('periodo_info'):
                story.extend(self.builder.create_period_info_table(dashboard_data['periodo_info'], filters_info))

            # Tabela de condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
                condominio_data = [['Condomínio', 'Total de Rondas']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data']):
                    condominio_data.append([label, str(value)])
                story.extend(self.builder.create_zebra_table(
                    condominio_data,
                    'Todos os Condomínios com Ronda no Período',
                    [3, 2]
                ))

            # [NOVO] Seção detalhada de quantidades por residencial
            story.extend(self._create_residencial_quantities_section(dashboard_data, periodo_inicio, periodo_fim, filters_info))

            # Análise por turno
            if dashboard_data.get('turno_labels') and dashboard_data.get('rondas_por_turno_data'):
                turno_data = [['Turno', 'Total de Rondas', 'Percentual']]
                total_rondas_turno = sum(dashboard_data['rondas_por_turno_data'])
                for label, value in zip(dashboard_data['turno_labels'], dashboard_data['rondas_por_turno_data']):
                    percentual = round((value / total_rondas_turno * 100), 1) if total_rondas_turno > 0 else 0
                    turno_data.append([label, str(value), f"{percentual}%"])
                story.extend(self.builder.create_analysis_table(
                    turno_data,
                    'Análise por Turno',
                    [2.5, 1.5, 1.5]
                ))

            # Ranking de supervisores
            if dashboard_data.get('supervisor_labels') and dashboard_data.get('rondas_por_supervisor_data'):
                supervisor_data = [['Posição', 'Supervisor', 'Total de Rondas', 'Percentual']]
                total_rondas_supervisor = sum(dashboard_data['rondas_por_supervisor_data'])
                for i, (label, value) in enumerate(zip(dashboard_data['supervisor_labels'], dashboard_data['rondas_por_supervisor_data']), 1):
                    percentual = round((value / total_rondas_supervisor * 100), 1) if total_rondas_supervisor > 0 else 0
                    supervisor_data.append([str(i), label, str(value), f"{percentual}%"])
                story.extend(self.builder.create_analysis_table(
                    supervisor_data,
                    'Ranking de Supervisores',
                    [0.8, 2.2, 1.5, 1.5]
                ))

            # Duração média por condomínio
            if dashboard_data.get('duracao_condominio_labels') and dashboard_data.get('duracao_media_data'):
                duracao_data = [['Condomínio', 'Duração Média (min)']]
                for label, value in zip(dashboard_data['duracao_condominio_labels'], dashboard_data['duracao_media_data']):
                    duracao_data.append([label, f"{value:.1f}"])
                story.extend(self.builder.create_analysis_table(
                    duracao_data,
                    'Duração Média por Condomínio',
                    [3.5, 2]
                ))

            # Comparação com período anterior
            if dashboard_data.get('comparacao_periodo'):
                comparacao = dashboard_data['comparacao_periodo']
                comparacao_data = [
                    ['Métrica', 'Período Atual', 'Período Anterior', 'Variação'],
                    ['Total de Rondas',
                     str(comparacao.get('total_atual', 0)),
                     str(comparacao.get('total_anterior', 0)),
                     f"{comparacao.get('variacao_percentual', 0):+.1f}%"]
                ]
                story.extend(self.builder.create_analysis_table(
                    comparacao_data,
                    'Comparação com Período Anterior',
                    [2, 1.5, 1.5, 1.5]
                ))

            # Resumo executivo
            story.extend(self._create_executive_summary(dashboard_data, periodo_inicio, periodo_fim))

            # Debug info
            story.extend(self._create_debug_info(dashboard_data))

            # Build do documento
            doc.build(story, onFirstPage=self.builder.add_header_footer, onLaterPages=self.builder.add_header_footer)
            buffer.seek(0)
            return buffer

        except Exception as e:
            logger.error(f'Erro ao gerar relatório PDF de rondas: {e}', exc_info=True)
            raise

    def generate_compact_ronda_dashboard_pdf(self, dashboard_data: Dict, filters_info: Optional[Dict] = None) -> BytesIO:
        """Gera relatório PDF ultra-compacto do dashboard de rondas."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=40,  # Ainda mais reduzido
                leftMargin=40,   # Ainda mais reduzido
                topMargin=60,    # Ainda mais reduzido
                bottomMargin=40  # Ainda mais reduzido
            )

            story = []

            # Capa compacta
            periodo_inicio = filters_info.get("data_inicio", "") if filters_info else ""
            periodo_fim = filters_info.get("data_fim", "") if filters_info else ""
            story.extend(self.builder.create_cover_page(
                "Relatório Compacto - Rondas",
                "Assistente IA Seg",
                periodo_inicio,
                periodo_fim
            ))

            # Resumo executivo compacto
            kpi_data = [
                ['Indicador', 'Valor'],
                ['Total de Rondas', str(dashboard_data.get('total_rondas', 0))],
                ['Média por Dia', f"{dashboard_data.get('media_rondas_dia', 0)}"],
                ['Duração Média', f"{dashboard_data.get('duracao_media_geral', 0)} min"],
                ['Supervisor Mais Ativo', dashboard_data.get('supervisor_mais_ativo', 'N/A')]
            ]
            
            story.extend(self.builder.create_compact_summary_table(
                kpi_data, 
                dashboard_data.get('periodo_info', {}),
                filters_info
            ))

            # Tabelas combinadas em layout compacto
            tables_data = []
            
            # Condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
                condominio_data = [['Condomínio', 'Total']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data']):
                    condominio_data.append([label, str(value)])
                tables_data.append({
                    'title': 'Rondas por Condomínio',
                    'data': condominio_data,
                    'col_widths': [3, 1]
                })

            # [NOVO] Seção compacta de residenciais
            if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
                residencial_data = [['Residencial', 'Total', 'Status']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data']):
                    # Determina status baseado na quantidade
                    if value == 0:
                        status = "❌"
                    elif value < 5:
                        status = "⚠️"
                    elif value < 15:
                        status = "✅"
                    else:
                        status = "🟢"
                    residencial_data.append([label, str(value), status])
                tables_data.append({
                    'title': 'Status por Residencial',
                    'data': residencial_data,
                    'col_widths': [3, 1, 0.5]
                })

            # Turnos
            if dashboard_data.get('turno_labels') and dashboard_data.get('rondas_por_turno_data'):
                turno_data = [['Turno', 'Total', '%']]
                total_rondas_turno = sum(dashboard_data['rondas_por_turno_data'])
                for label, value in zip(dashboard_data['turno_labels'], dashboard_data['rondas_por_turno_data']):
                    percentual = round((value / total_rondas_turno * 100), 1) if total_rondas_turno > 0 else 0
                    turno_data.append([label, str(value), f"{percentual}%"])
                tables_data.append({
                    'title': 'Análise por Turno',
                    'data': turno_data,
                    'col_widths': [2, 1, 1]
                })

            # Supervisores (top 5)
            if dashboard_data.get('supervisor_labels') and dashboard_data.get('rondas_por_supervisor_data'):
                supervisor_data = [['Pos', 'Supervisor', 'Total', '%']]
                total_rondas_supervisor = sum(dashboard_data['rondas_por_supervisor_data'])
                for i, (label, value) in enumerate(zip(dashboard_data['supervisor_labels'][:5], dashboard_data['rondas_por_supervisor_data'][:5]), 1):
                    percentual = round((value / total_rondas_supervisor * 100), 1) if total_rondas_supervisor > 0 else 0
                    supervisor_data.append([str(i), label, str(value), f"{percentual}%"])
                tables_data.append({
                    'title': 'Top 5 Supervisores',
                    'data': supervisor_data,
                    'col_widths': [0.5, 2.5, 1, 1]
                })

            # Duração por condomínio (top 5)
            if dashboard_data.get('duracao_condominio_labels') and dashboard_data.get('duracao_media_data'):
                duracao_data = [['Condomínio', 'Duração (min)']]
                for label, value in zip(dashboard_data['duracao_condominio_labels'][:5], dashboard_data['duracao_media_data'][:5]):
                    duracao_data.append([label, f"{value:.1f}"])
                tables_data.append({
                    'title': 'Duração Média por Condomínio (Top 5)',
                    'data': duracao_data,
                    'col_widths': [3.5, 1.5]
                })

            # Comparação com período anterior
            if dashboard_data.get('comparacao_periodo'):
                comparacao = dashboard_data['comparacao_periodo']
                comparacao_data = [
                    ['Métrica', 'Atual', 'Anterior', 'Var.'],
                    ['Total de Rondas',
                     str(comparacao.get('total_atual', 0)),
                     str(comparacao.get('total_anterior', 0)),
                     f"{comparacao.get('variacao_percentual', 0):+.1f}%"]
                ]
                tables_data.append({
                    'title': 'Comparação Período Anterior',
                    'data': comparacao_data,
                    'col_widths': [2, 1, 1, 1]
                })

            story.extend(self.builder.create_compact_combined_tables(tables_data))

            # Build do documento
            doc.build(story, onFirstPage=self.builder.add_header_footer, onLaterPages=self.builder.add_header_footer)
            buffer.seek(0)
            return buffer

        except Exception as e:
            logger.error(f'Erro ao gerar relatório PDF compacto de rondas: {e}', exc_info=True)
            raise

    def _create_residencial_quantities_section(self, dashboard_data: Dict, periodo_inicio: str, periodo_fim: str, filters_info: Optional[Dict] = None) -> List:
        """Cria seção detalhada com quantidades de rondas por residencial no período."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        story = []
        styles = getSampleStyleSheet()
        
        # Título da seção
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        story.append(Paragraph("📊 Quantidades de Rondas por Residencial", title_style))
        story.append(Spacer(1, 6))
        
        # Descrição do período
        desc_style = ParagraphStyle(
            'CustomDesc',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            textColor=colors.grey
        )
        periodo_text = f"Período analisado: {periodo_inicio} a {periodo_fim}" if periodo_inicio and periodo_fim else "Período: Todos os dados disponíveis"
        story.append(Paragraph(periodo_text, desc_style))
        story.append(Spacer(1, 12))
        
        # Dados dos condomínios
        if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
            # Cria tabela com informações detalhadas
            table_data = [['Residencial', 'Total de Rondas', 'Média por Dia*', 'Status']]
            
            total_periodo = sum(dashboard_data['condominio_data'])
            total_dias = 1  # Valor padrão
            
            # Verifica se um supervisor foi selecionado
            supervisor_selected = filters_info and filters_info.get('supervisor_name')
            
            if supervisor_selected:
                # Se supervisor foi selecionado, usa os dias trabalhados do período_info
                periodo_info = dashboard_data.get('periodo_info', {})
                total_dias = periodo_info.get('dias_com_dados', 1)
            else:
                # Calcula total de dias se temos datas (comportamento original)
                if periodo_inicio and periodo_fim:
                    try:
                        from datetime import datetime
                        inicio = datetime.strptime(periodo_inicio, "%Y-%m-%d").date()
                        fim = datetime.strptime(periodo_fim, "%Y-%m-%d").date()
                        total_dias = (fim - inicio).days + 1
                    except:
                        total_dias = 1
            
            for i, (label, value) in enumerate(zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data'])):
                # Calcula média por dia
                media_dia = round(value / total_dias, 1) if total_dias > 0 else 0
                
                # Determina status baseado na quantidade
                if value == 0:
                    status = "❌ Sem rondas"
                    status_color = colors.red
                elif value < 5:
                    status = "⚠️ Baixa frequência"
                    status_color = colors.orange
                elif value < 15:
                    status = "✅ Frequência normal"
                    status_color = colors.green
                else:
                    status = "🟢 Alta frequência"
                    status_color = colors.darkgreen
                
                table_data.append([label, str(value), f"{media_dia}", status])
            
            # Adiciona linha de total
            media_total = round(total_periodo / total_dias, 1) if total_dias > 0 else 0
            table_data.append(['**TOTAL GERAL**', f"**{total_periodo}**", f"**{media_total}**", "**Resumo**"])
            
            # Cria a tabela
            table = Table(table_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.5*inch])
            
            # Estilo da tabela
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                # Linhas de dados
                ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Nome do residencial
                ('ALIGN', (1, 1), (2, -2), 'CENTER'),  # Números
                ('ALIGN', (3, 1), (3, -2), 'CENTER'),  # Status
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                
                # Linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                
                # Bordas
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ])
            
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Nota explicativa
            nota_style = ParagraphStyle(
                'CustomNota',
                parent=styles['Normal'],
                fontSize=8,
                spaceAfter=6,
                textColor=colors.grey,
                leftIndent=20
            )
            if supervisor_selected:
                nota_text = "* Média calculada considerando apenas os dias trabalhados pelo supervisor (jornada 12x36)"
            else:
                nota_text = "* Média calculada considerando o período total selecionado"
            story.append(Paragraph(nota_text, nota_style))
            
            # Estatísticas adicionais
            if total_periodo > 0:
                stats_style = ParagraphStyle(
                    'CustomStats',
                    parent=styles['Normal'],
                    fontSize=9,
                    spaceAfter=6,
                    textColor=colors.darkblue
                )
                
                # Encontra o residencial com mais rondas
                max_rondas = max(dashboard_data['condominio_data'])
                max_residencial = dashboard_data['condominio_labels'][dashboard_data['condominio_data'].index(max_rondas)]
                
                # Encontra o residencial com menos rondas (excluindo zeros)
                rondas_nao_zero = [r for r in dashboard_data['condominio_data'] if r > 0]
                if rondas_nao_zero:
                    min_rondas = min(rondas_nao_zero)
                    min_residencial = dashboard_data['condominio_labels'][dashboard_data['condominio_data'].index(min_rondas)]
                else:
                    min_rondas = 0
                    min_residencial = "N/A"
                
                stats_text = f"""
                <b>Estatísticas:</b><br/>
                • Residencial com mais rondas: <b>{max_residencial}</b> ({max_rondas} rondas)<br/>
                • Residencial com menos rondas: <b>{min_residencial}</b> ({min_rondas} rondas)<br/>
                • Residenciais com atividade: {len([r for r in dashboard_data['condominio_data'] if r > 0])} de {len(dashboard_data['condominio_labels'])}
                """
                story.append(Paragraph(stats_text, stats_style))
        else:
            # Mensagem quando não há dados
            no_data_style = ParagraphStyle(
                'CustomNoData',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                textColor=colors.red
            )
            story.append(Paragraph("⚠️ Nenhum dado de residencial disponível para o período selecionado.", no_data_style))
        
        story.append(Spacer(1, 20))
        return story

    def _create_executive_summary(self, dashboard_data: Dict, periodo_inicio: str, periodo_fim: str) -> List:
        story = []
        story.append(Paragraph('Resumo Executivo', self.builder.styles.section_style))

        resumo_text = f"""
        <b>Período Analisado:</b> {periodo_inicio} a {periodo_fim}<br/>
        <b>Total de Rondas:</b> {dashboard_data.get('total_rondas', 0)}<br/>
        <b>Média por Dia:</b> {dashboard_data.get('media_rondas_dia', 0)}<br/>
        <b>Duração Média:</b> {dashboard_data.get('duracao_media_geral', 0)} minutos<br/>
        <b>Supervisor Mais Ativo:</b> {dashboard_data.get('supervisor_mais_ativo', 'N/A')}<br/>
        <b>Cobertura do Período:</b> {dashboard_data.get('periodo_info', {}).get('cobertura_periodo', 0)}%<br/>
        """
        story.append(Paragraph(resumo_text, self.builder.styles.normal_style))
        story.append(Spacer(1, 12))  # Reduzido de 20 para 12
        return story

    def _create_debug_info(self, dashboard_data: Dict) -> List:
        story = []
        story.append(Paragraph('Informações de Debug', self.builder.styles.section_style))

        debug_text = f"""
        <b>Dados Disponíveis:</b><br/>
        • Turnos: {len(dashboard_data.get('turno_labels', []))} registros<br/>
        • Supervisores: {len(dashboard_data.get('supervisor_labels', []))} registros<br/>
        • Condomínios: {len(dashboard_data.get('condominio_labels', []))} registros<br/>
        • Duração por Condomínio: {len(dashboard_data.get('duracao_condominio_labels', []))} registros<br/>
        • Comparação de Período: {'Sim' if dashboard_data.get('comparacao_periodo') else 'Não'}<br/>
        """
        story.append(Paragraph(debug_text, self.builder.styles.normal_style))
        story.append(Spacer(1, 12))  # Reduzido de 20 para 12
        return story
