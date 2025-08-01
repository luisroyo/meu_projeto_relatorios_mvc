# app/services/report/ocorrencia_service.py
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from app import db
from app.models import Ocorrencia
from .builder import ReportBuilder

logger = logging.getLogger(__name__)


class OcorrenciaReportService:
    """Serviço para geração de relatórios PDF do dashboard de ocorrências."""
    
    def __init__(self):
        self.builder = ReportBuilder()
    
    def generate_ocorrencia_dashboard_pdf(self, dashboard_data: Dict, filters_info: Optional[Dict] = None) -> BytesIO:
        """Gera relatório PDF do dashboard de ocorrências."""
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
                "Relatório de Dashboard - Ocorrências",
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
                ['Total de Ocorrências', str(dashboard_data.get('total_ocorrencias', 0)), 'Soma total de ocorrências no período'],
                ['Ocorrências Abertas', str(dashboard_data.get('ocorrencias_abertas', 0)), 'Ocorrências não concluídas'],
                ['Média Diária', f"{dashboard_data.get('media_diaria_ocorrencias', 0)}", 'Média de ocorrências por dia'],
                ['Tempo Médio Resolução', f"{dashboard_data.get('tempo_medio_resolucao_minutos', 0)} min", 'Tempo médio para resolver ocorrências'],
                ['Tipo Mais Comum', dashboard_data.get('tipo_mais_comum', 'N/A'), 'Tipo de ocorrência mais frequente'],
                ['Supervisor Principal', dashboard_data.get('kpi_supervisor_name', 'N/A'), 'Supervisor com mais ocorrências']
            ]
            story.extend(self.builder.create_kpi_table(kpi_data))
            
            # Informações do período
            if dashboard_data.get('periodo_info'):
                story.extend(self.builder.create_period_info_table(dashboard_data['periodo_info']))
            
            # Tabela de condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('ocorrencias_por_condominio_data'):
                condominio_data = [['Condomínio', 'Total de Ocorrências']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['ocorrencias_por_condominio_data']):
                    condominio_data.append([label, str(value)])
                story.extend(self.builder.create_zebra_table(
                    condominio_data,
                    'Todos os Condomínios com Ocorrência no Período',
                    [3, 2]
                ))
            
            # Tipos de Ocorrência
            if dashboard_data.get('tipo_labels') and dashboard_data.get('ocorrencias_por_tipo_data'):
                tipo_data = [['Tipo de Ocorrência', 'Quantidade', 'Percentual']]
                total_tipos = sum(dashboard_data['ocorrencias_por_tipo_data'])
                for label, value in zip(dashboard_data['tipo_labels'], dashboard_data['ocorrencias_por_tipo_data']):
                    percentual = round((value / total_tipos * 100), 1) if total_tipos > 0 else 0
                    tipo_data.append([label, str(value), f"{percentual}%"])
                story.extend(self.builder.create_analysis_table(
                    tipo_data,
                    'Análise por Tipo de Ocorrência',
                    [2.5, 1.5, 1.5]
                ))
            
            # Colaboradores com Quantidades
            story.extend(self._create_colaboradores_section(dashboard_data))
            
            # Build do documento
            doc.build(story, onFirstPage=self.builder.add_header_footer, onLaterPages=self.builder.add_header_footer)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f'Erro ao gerar relatório PDF de ocorrências: {e}', exc_info=True)
            raise

    def generate_compact_ocorrencia_dashboard_pdf(self, dashboard_data: Dict, filters_info: Optional[Dict] = None) -> BytesIO:
        """Gera relatório PDF ultra-compacto do dashboard de ocorrências."""
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
                "Relatório Compacto - Ocorrências",
                "Assistente IA Seg",
                periodo_inicio,
                periodo_fim
            ))
            
            # Resumo executivo compacto
            kpi_data = [
                ['Indicador', 'Valor'],
                ['Total de Ocorrências', str(dashboard_data.get('total_ocorrencias', 0))],
                ['Ocorrências Abertas', str(dashboard_data.get('ocorrencias_abertas', 0))],
                ['Média Diária', f"{dashboard_data.get('media_diaria_ocorrencias', 0)}"],
                ['Tempo Médio Resolução', f"{dashboard_data.get('tempo_medio_resolucao_minutos', 0)} min"],
                ['Tipo Mais Comum', dashboard_data.get('tipo_mais_comum', 'N/A')],
                ['Supervisor Principal', dashboard_data.get('kpi_supervisor_name', 'N/A')]
            ]
            
            story.extend(self.builder.create_compact_summary_table(
                kpi_data, 
                dashboard_data.get('periodo_info', {})
            ))

            # Tabelas combinadas em layout compacto
            tables_data = []
            
            # Condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('ocorrencias_por_condominio_data'):
                condominio_data = [['Condomínio', 'Total']]
                for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['ocorrencias_por_condominio_data']):
                    condominio_data.append([label, str(value)])
                tables_data.append({
                    'title': 'Ocorrências por Condomínio',
                    'data': condominio_data,
                    'col_widths': [3, 1]
                })

            # Tipos de Ocorrência
            if dashboard_data.get('tipo_labels') and dashboard_data.get('ocorrencias_por_tipo_data'):
                tipo_data = [['Tipo', 'Qtd', '%']]
                total_tipos = sum(dashboard_data['ocorrencias_por_tipo_data'])
                for label, value in zip(dashboard_data['tipo_labels'], dashboard_data['ocorrencias_por_tipo_data']):
                    percentual = round((value / total_tipos * 100), 1) if total_tipos > 0 else 0
                    tipo_data.append([label, str(value), f"{percentual}%"])
                tables_data.append({
                    'title': 'Tipos de Ocorrência',
                    'data': tipo_data,
                    'col_widths': [2, 1, 1]
                })

            # Colaboradores com Quantidades (top 5)
            if dashboard_data.get('top_colaboradores_labels') and dashboard_data.get('top_colaboradores_data'):
                colab_data = [['Pos', 'Colaborador', 'Qtd', '%']]
                total_colab = sum(dashboard_data['top_colaboradores_data'])
                for i, (label, value) in enumerate(zip(dashboard_data['top_colaboradores_labels'][:5], dashboard_data['top_colaboradores_data'][:5]), 1):
                    percentual = round((value / total_colab * 100), 1) if total_colab > 0 else 0
                    colab_data.append([str(i), label, str(value), f"{percentual}%"])
                tables_data.append({
                    'title': 'Top 5 Colaboradores',
                    'data': colab_data,
                    'col_widths': [0.5, 2.5, 1, 1]
                })

            story.extend(self.builder.create_compact_combined_tables(tables_data))
            
            # Build do documento
            doc.build(story, onFirstPage=self.builder.add_header_footer, onLaterPages=self.builder.add_header_footer)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f'Erro ao gerar relatório PDF compacto de ocorrências: {e}', exc_info=True)
            raise
    
    def _create_colaboradores_section(self, dashboard_data: Dict) -> List:
        """Cria seção de colaboradores com quantidades."""
        story = []
        story.append(Paragraph('Colaboradores que Atenderam Ocorrências no Período', self.builder.styles.section_style))
        
        if dashboard_data.get('top_colaboradores_labels') and dashboard_data.get('top_colaboradores_data'):
            colab_data = [['Posição', 'Colaborador', 'Quantidade de Ocorrências', 'Percentual']]
            total_colab = sum(dashboard_data['top_colaboradores_data'])
            
            for i, (label, value) in enumerate(zip(dashboard_data['top_colaboradores_labels'], dashboard_data['top_colaboradores_data']), 1):
                percentual = round((value / total_colab * 100), 1) if total_colab > 0 else 0
                colab_data.append([str(i), label, str(value), f"{percentual}%"])
            
            story.extend(self.builder.create_analysis_table(
                colab_data,
                'Top Colaboradores por Quantidade de Ocorrências Atendidas',
                [0.8, 2.2, 1.5, 1.5]
            ))
        else:
            story.append(Paragraph('Nenhum colaborador encontrado no período.', self.builder.styles.normal_style))
            story.append(Spacer(1, 12))  # Reduzido de 20 para 12
        
        return story

 