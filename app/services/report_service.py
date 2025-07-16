# app/services/report_service.py
import logging
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class RondaReportService:
    """
    Serviço para geração de relatórios PDF do dashboard de rondas.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos customizados para o relatório."""
        # Título principal
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Subtítulo
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Cabeçalho de seção
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Texto normal
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # KPI style
        self.kpi_style = ParagraphStyle(
            'KPIStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_CENTER
        )
    
    def _format_filters_section(self, filters_info):
        """Formata a seção de filtros aplicados."""
        if not filters_info:
            return []
        
        story = []
        story.append(Paragraph("Filtros Aplicados", self.section_style))
        
        filters_data = [['Filtro', 'Valor']]
        
        # Data de início
        if filters_info.get('data_inicio'):
            try:
                data_inicio = datetime.strptime(filters_info['data_inicio'], '%Y-%m-%d').strftime('%d/%m/%Y')
                filters_data.append(['Data Início', data_inicio])
            except Exception:
                filters_data.append(['Data Início', filters_info['data_inicio']])
        
        # Data de fim
        if filters_info.get('data_fim'):
            try:
                data_fim = datetime.strptime(filters_info['data_fim'], '%Y-%m-%d').strftime('%d/%m/%Y')
                filters_data.append(['Data Fim', data_fim])
            except Exception:
                filters_data.append(['Data Fim', filters_info['data_fim']])
        
        # Supervisor
        if filters_info.get('supervisor_name'):
            filters_data.append(['Supervisor', filters_info['supervisor_name']])
        
        # Condomínio
        if filters_info.get('condominio_name'):
            filters_data.append(['Condomínio', filters_info['condominio_name']])
        
        # Turno
        if filters_info.get('turno'):
            filters_data.append(['Turno', filters_info['turno']])
        
        # Tipo (para ocorrências)
        if filters_info.get('tipo_name'):
            filters_data.append(['Tipo', filters_info['tipo_name']])
        
        # Status (para ocorrências)
        if filters_info.get('status'):
            filters_data.append(['Status', filters_info['status']])
        
        # Mês
        if filters_info.get('mes'):
            meses = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            mes_nome = meses.get(filters_info['mes'], f'Mês {filters_info["mes"]}')
            filters_data.append(['Mês', mes_nome])
        
        # Se não há filtros aplicados
        if len(filters_data) == 1:
            filters_data.append(['Nenhum filtro específico', 'Todos os dados'])
        
        filters_table = Table(filters_data, colWidths=[2*inch, 4*inch])
        filters_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(filters_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def generate_ronda_dashboard_pdf(self, dashboard_data, filters_info=None):
        """
        Gera um relatório PDF com os dados do dashboard de rondas.
        
        Args:
            dashboard_data (dict): Dados do dashboard
            filters_info (dict): Informações sobre os filtros aplicados
            
        Returns:
            BytesIO: Buffer com o PDF gerado
        """
        try:
            # Cria o buffer para o PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            # Lista de elementos do PDF
            story = []
            
            # Título do relatório
            title = Paragraph("Relatório de Dashboard - Rondas", self.title_style)
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Data de geração
            generation_date = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
            date_para = Paragraph(generation_date, self.normal_style)
            story.append(date_para)
            story.append(Spacer(1, 20))
            
            # Seção de filtros aplicados
            story.extend(self._format_filters_section(filters_info))
            
            # Seção de KPIs Principais
            story.append(Paragraph("Principais Indicadores (KPIs)", self.section_style))
            
            # Tabela de KPIs
            kpi_data = [
                ['Indicador', 'Valor', 'Descrição'],
                ['Total de Rondas', str(dashboard_data.get('total_rondas', 0)), 'Soma total de rondas no período'],
                ['Média por Dia', f"{dashboard_data.get('media_rondas_dia', 0)}", 'Média de rondas por dia trabalhado'],
                ['Duração Média', f"{dashboard_data.get('duracao_media_geral', 0)} min", 'Tempo médio por ronda'],
                ['Supervisor Mais Ativo', dashboard_data.get('supervisor_mais_ativo', 'N/A'), 'Supervisor com mais rondas']
            ]
            
            kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 3*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 20))
            
            # Informações do período (se disponível)
            if dashboard_data.get('periodo_info'):
                story.append(Paragraph("Informações do Período", self.section_style))
                periodo = dashboard_data['periodo_info']
                
                # Ajusta datas para formato brasileiro
                primeira_data = periodo.get('primeira_data_registrada')
                ultima_data = periodo.get('ultima_data_registrada')
                if primeira_data and isinstance(primeira_data, (datetime,)):
                    primeira_data = primeira_data.strftime('%d/%m/%Y')
                elif primeira_data:
                    try:
                        primeira_data = datetime.strptime(str(primeira_data), '%Y-%m-%d').strftime('%d/%m/%Y')
                    except Exception:
                        pass
                if ultima_data and isinstance(ultima_data, (datetime,)):
                    ultima_data = ultima_data.strftime('%d/%m/%Y')
                elif ultima_data:
                    try:
                        ultima_data = datetime.strptime(str(ultima_data), '%Y-%m-%d').strftime('%d/%m/%Y')
                    except Exception:
                        pass
                periodo_data = [
                    ['Informação', 'Valor'],
                    ['Primeira Data', primeira_data or 'N/A'],
                    ['Última Data', ultima_data or 'N/A'],
                    ['Dias com Dados', f"{periodo.get('dias_com_dados', 0)} / {periodo.get('periodo_solicitado_dias', 0)}"],
                    ['Cobertura', f"{periodo.get('cobertura_periodo', 0)}%"]
                ]
                
                periodo_table = Table(periodo_data, colWidths=[2.5*inch, 4*inch])
                periodo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                story.append(periodo_table)
                story.append(Spacer(1, 20))
            
            # Comparação com período anterior (se disponível)
            if dashboard_data.get('comparacao_periodo'):
                story.append(Paragraph("Comparação com Período Anterior", self.section_style))
                comparacao = dashboard_data['comparacao_periodo']
                
                comparacao_data = [
                    ['Métrica', 'Período Atual', 'Período Anterior', 'Variação'],
                    ['Total de Rondas', 
                     str(comparacao.get('total_atual', 0)), 
                     str(comparacao.get('total_anterior', 0)),
                     f"{comparacao.get('variacao_percentual', 0)}%"]
                ]
                
                comparacao_table = Table(comparacao_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                comparacao_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                story.append(comparacao_table)
                story.append(Spacer(1, 20))
            
            # Resumo dos dados por categoria
            story.append(Paragraph("Resumo por Categoria", self.section_style))
            
            # Top 5 Supervisores
            if dashboard_data.get('supervisor_labels') and dashboard_data.get('rondas_por_supervisor_data'):
                story.append(Paragraph("Top 5 Supervisores", self.normal_style))
                supervisor_data = [['Supervisor', 'Total de Rondas']]
                for i, (label, value) in enumerate(zip(dashboard_data['supervisor_labels'][:5], 
                                                      dashboard_data['rondas_por_supervisor_data'][:5])):
                    supervisor_data.append([label, str(value)])
                
                supervisor_table = Table(supervisor_data, colWidths=[3*inch, 2*inch])
                supervisor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(supervisor_table)
                story.append(Spacer(1, 15))
            
            # Top 5 Condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('rondas_por_condominio_data'):
                story.append(Paragraph("Top 5 Condomínios", self.normal_style))
                condominio_data = [['Condomínio', 'Total de Rondas']]
                for i, (label, value) in enumerate(zip(dashboard_data['condominio_labels'][:5], 
                                                      dashboard_data['rondas_por_condominio_data'][:5])):
                    condominio_data.append([label, str(value)])
                
                condominio_table = Table(condominio_data, colWidths=[3*inch, 2*inch])
                condominio_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(condominio_table)
                story.append(Spacer(1, 15))
            
            # Gera o PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF: {e}", exc_info=True)
            raise

    def generate_ocorrencia_dashboard_pdf(self, dashboard_data, filters_info=None):
        """
        Gera um relatório PDF com os dados do dashboard de ocorrências.
        
        Args:
            dashboard_data (dict): Dados do dashboard
            filters_info (dict): Informações sobre os filtros aplicados
            
        Returns:
            BytesIO: Buffer com o PDF gerado
        """
        try:
            # Cria o buffer para o PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            # Lista de elementos do PDF
            story = []
            
            # Título do relatório
            title = Paragraph("Relatório de Dashboard - Ocorrências", self.title_style)
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Data de geração
            generation_date = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
            date_para = Paragraph(generation_date, self.normal_style)
            story.append(date_para)
            story.append(Spacer(1, 20))
            
            # Seção de filtros aplicados
            story.extend(self._format_filters_section(filters_info))
            
            # Seção de KPIs Principais
            story.append(Paragraph("Principais Indicadores (KPIs)", self.section_style))
            
            # Tabela de KPIs
            kpi_data = [
                ['Indicador', 'Valor', 'Descrição'],
                ['Total de Ocorrências', str(dashboard_data.get('total_ocorrencias', 0)), 'Soma total de ocorrências no período'],
                ['Ocorrências Abertas', str(dashboard_data.get('ocorrencias_abertas', 0)), 'Ocorrências não concluídas'],
                ['Tipo Mais Comum', dashboard_data.get('tipo_mais_comum', 'N/A'), 'Tipo de ocorrência mais frequente'],
                ['Supervisor Principal', dashboard_data.get('kpi_supervisor_name', 'N/A'), 'Supervisor com mais ocorrências']
            ]
            
            kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 3*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 20))
            
            # Informações do período (se disponível)
            if dashboard_data.get('periodo_info'):
                story.append(Paragraph("Informações do Período", self.section_style))
                periodo = dashboard_data['periodo_info']
                
                # Ajusta datas para formato brasileiro
                primeira_data = periodo.get('primeira_data_registrada')
                ultima_data = periodo.get('ultima_data_registrada')
                if primeira_data and isinstance(primeira_data, (datetime,)):
                    primeira_data = primeira_data.strftime('%d/%m/%Y')
                elif primeira_data:
                    try:
                        primeira_data = datetime.strptime(str(primeira_data), '%Y-%m-%d').strftime('%d/%m/%Y')
                    except Exception:
                        pass
                if ultima_data and isinstance(ultima_data, (datetime,)):
                    ultima_data = ultima_data.strftime('%d/%m/%Y')
                elif ultima_data:
                    try:
                        ultima_data = datetime.strptime(str(ultima_data), '%Y-%m-%d').strftime('%d/%m/%Y')
                    except Exception:
                        pass
                
                periodo_data = [
                    ['Informação', 'Valor'],
                    ['Primeira Data', primeira_data or 'N/A'],
                    ['Última Data', ultima_data or 'N/A'],
                    ['Dias com Dados', f"{periodo.get('dias_com_dados', 0)} / {periodo.get('periodo_solicitado_dias', 0)}"],
                    ['Cobertura', f"{periodo.get('cobertura_periodo', 0)}%"]
                ]
                
                periodo_table = Table(periodo_data, colWidths=[2.5*inch, 4*inch])
                periodo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                story.append(periodo_table)
                story.append(Spacer(1, 20))
            
            # Comparação com período anterior (se disponível)
            if dashboard_data.get('comparacao_periodo'):
                story.append(Paragraph("Comparação com Período Anterior", self.section_style))
                comparacao = dashboard_data['comparacao_periodo']
                
                comparacao_data = [
                    ['Métrica', 'Período Atual', 'Período Anterior', 'Variação'],
                    ['Total de Ocorrências', 
                     str(comparacao.get('total_atual', 0)), 
                     str(comparacao.get('total_anterior', 0)),
                     f"{comparacao.get('variacao_percentual', 0)}%"]
                ]
                
                comparacao_table = Table(comparacao_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                comparacao_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                story.append(comparacao_table)
                story.append(Spacer(1, 20))
            
            # Resumo dos dados por categoria
            story.append(Paragraph("Resumo por Categoria", self.section_style))
            
            # Top 5 Tipos de Ocorrência
            if dashboard_data.get('tipo_labels') and dashboard_data.get('ocorrencias_por_tipo_data'):
                story.append(Paragraph("Top 5 Tipos de Ocorrência", self.normal_style))
                tipo_data = [['Tipo', 'Total de Ocorrências']]
                for i, (label, value) in enumerate(zip(dashboard_data['tipo_labels'][:5], 
                                                      dashboard_data['ocorrencias_por_tipo_data'][:5])):
                    tipo_data.append([label, str(value)])
                
                tipo_table = Table(tipo_data, colWidths=[3*inch, 2*inch])
                tipo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(tipo_table)
                story.append(Spacer(1, 15))
            
            # Top 5 Condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('ocorrencias_por_condominio_data'):
                story.append(Paragraph("Top 5 Condomínios", self.normal_style))
                condominio_data = [['Condomínio', 'Total de Ocorrências']]
                for i, (label, value) in enumerate(zip(dashboard_data['condominio_labels'][:5], 
                                                      dashboard_data['ocorrencias_por_condominio_data'][:5])):
                    condominio_data.append([label, str(value)])
                
                condominio_table = Table(condominio_data, colWidths=[3*inch, 2*inch])
                condominio_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(condominio_table)
                story.append(Spacer(1, 15))
            
            # Top 5 Colaboradores
            if dashboard_data.get('top_colaboradores_labels') and dashboard_data.get('top_colaboradores_data'):
                story.append(Paragraph("Top 5 Colaboradores Envolvidos", self.normal_style))
                colaborador_data = [['Colaborador', 'Total de Ocorrências']]
                for i, (label, value) in enumerate(zip(dashboard_data['top_colaboradores_labels'][:5], 
                                                      dashboard_data['top_colaboradores_data'][:5])):
                    colaborador_data.append([label, str(value)])
                
                colaborador_table = Table(colaborador_data, colWidths=[3*inch, 2*inch])
                colaborador_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(colaborador_table)
                story.append(Spacer(1, 15))
            
            # Gera o PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF de ocorrências: {e}", exc_info=True)
            raise 