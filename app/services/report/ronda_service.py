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
                rightMargin=72,
                leftMargin=72,
                topMargin=120,
                bottomMargin=60
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
            story.append(PageBreak())

            # Informações de geração
            story.extend(self.builder.add_generation_info())
            story.append(Spacer(1, 20))

            # Filtros
            story.extend(self.builder.format_filters_section(filters_info))
            story.append(Spacer(1, 20))

            # KPIs
            kpi_data = [
                ['Indicador', 'Valor', 'Descrição'],
                ['Total de Rondas', str(dashboard_data.get('total_rondas', 0)), 'Soma total de rondas no período'],
                ['Média por Dia', f"{dashboard_data.get('media_rondas_dia', 0)}", 'Média de rondas por dia trabalhado'],
                ['Duração Média', f"{dashboard_data.get('duracao_media_geral', 0)} min", 'Tempo médio por ronda'],
                ['Supervisor Mais Ativo', dashboard_data.get('supervisor_mais_ativo', 'N/A'), 'Supervisor com mais rondas']
            ]
            story.extend(self.builder.create_kpi_table(kpi_data))
            story.append(PageBreak())

            # Informações do período
            if dashboard_data.get('periodo_info'):
                story.extend(self.builder.create_period_info_table(dashboard_data['periodo_info']))
                story.append(Spacer(1, 20))

            # Tabela de condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('rondas_por_condominio_data'):
                condominio_data = [['Condomínio', 'Total de Rondas']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['rondas_por_condominio_data']):
                    condominio_data.append([label, str(value)])
                story.extend(self.builder.create_zebra_table(
                    condominio_data,
                    'Todos os Condomínios com Ronda no Período',
                    [3, 2]
                ))
                story.append(PageBreak())

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
                story.append(Spacer(1, 20))

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
                story.append(PageBreak())

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
                story.append(Spacer(1, 20))

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
                story.append(PageBreak())

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
        story.append(Spacer(1, 20))
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
        story.append(Spacer(1, 20))
        return story
