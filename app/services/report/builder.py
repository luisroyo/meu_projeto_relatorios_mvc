# app/services/report/builder.py
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from .styles import ReportStyles, TableStyles


class ReportBuilder:
    """Classe para construir relatórios PDF."""
    
    def __init__(self):
        self.styles = ReportStyles()
        self.table_styles = TableStyles()
    
    def create_cover_page(self, title: str, subtitle: str, periodo_inicio: str = "", periodo_fim: str = "") -> List:
        """Cria a página de capa do relatório."""
        story = []
        
        # Logo
        try:
            logo_path = 'app/static/images/logo_master.png'
            img = Image(logo_path, width=180, height=80)
            img.hAlign = 'CENTER'
            story.append(img)
        except Exception:
            pass
        
        story.append(Spacer(1, 20))
        
        # Slogan
        slogan_style = ParagraphStyle('slogan', fontSize=16, leading=22, alignment=TA_CENTER)
        story.append(Paragraph('É <b>segurança</b>.<br/>É <b>manutenção</b>.<br/>É <b>sustentabilidade</b>.<br/>', slogan_style))
        
        story.append(Spacer(1, 10))
        
        # Nome da empresa
        company_style = ParagraphStyle('company', fontSize=18, leading=24, alignment=TA_CENTER, textColor=colors.HexColor('#1e2d3b'))
        story.append(Paragraph('É <b>ASSOCIAÇÃO MASTER</b>', company_style))
        
        story.append(Spacer(1, 30))
        
        # Título e subtítulo
        story.append(Paragraph(title, self.styles.title_style))
        story.append(Paragraph(subtitle, self.styles.subtitle_style))
        
        story.append(Spacer(1, 30))
        
        # Período
        if periodo_inicio or periodo_fim:
            periodo_text = f'Período: {periodo_inicio} a {periodo_fim}'
            story.append(Paragraph(periodo_text, self.styles.normal_style))
        
        story.append(PageBreak())
        return story
    
    def add_generation_info(self) -> List:
        """Adiciona informações de geração do relatório."""
        story = []
        generation_date = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        story.append(Paragraph(generation_date, self.styles.normal_style))
        story.append(Spacer(1, 20))
        return story
    
    def format_filters_section(self, filters_info: Optional[Dict]) -> List:
        """Formata a seção de filtros aplicados."""
        if not filters_info:
            return []
        
        story = []
        story.append(Paragraph("Filtros Aplicados", self.styles.section_style))
        
        filters_data = [['Filtro', 'Valor']]
        
        # Mapeamento de filtros
        filter_mappings = {
            'data_inicio': ('Data Início', self._format_date),
            'data_fim': ('Data Fim', self._format_date),
            'supervisor_name': ('Supervisor', lambda x: x),
            'condominio_name': ('Condomínio', lambda x: x),
            'turno': ('Turno', lambda x: x),
            'tipo_name': ('Tipo', lambda x: x),
            'status': ('Status', lambda x: x),
            'mes': ('Mês', self._format_month),
        }
        
        for key, (label, formatter) in filter_mappings.items():
            if filters_info.get(key):
                value = formatter(filters_info[key])
                filters_data.append([label, value])
        
        # Se não há filtros aplicados
        if len(filters_data) == 1:
            filters_data.append(['Nenhum filtro específico', 'Todos os dados'])
        
        filters_table = Table(filters_data, colWidths=[2*inch, 4*inch])
        filters_table.setStyle(TableStyle(
            self.table_styles.get_header_style() +
            self.table_styles.get_base_table_style() +
            [('ALIGN', (0, 0), (-1, -1), 'LEFT')]
        ))
        
        story.append(filters_table)
        story.append(Spacer(1, 20))
        return story
    
    def _format_date(self, date_str: str) -> str:
        """Formata data para formato brasileiro."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            return date_str
    
    def _format_month(self, month_num: int) -> str:
        """Formata número do mês para nome."""
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return meses.get(month_num, f'Mês {month_num}')
    
    def create_kpi_table(self, kpi_data: List[List[str]], title: str = "Principais Indicadores (KPIs)") -> List:
        """Cria tabela de KPIs."""
        story = []
        story.append(Paragraph(title, self.styles.section_style))
        
        kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 3*inch])
        kpi_table.setStyle(TableStyle(
            self.table_styles.get_header_style() +
            self.table_styles.get_base_table_style() +
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ]
        ))
        
        story.append(kpi_table)
        story.append(Spacer(1, 20))
        return story
    
    def create_period_info_table(self, periodo_info: Dict) -> List:
        """Cria tabela com informações do período."""
        story = []
        story.append(Paragraph('Informações do Período', self.styles.section_style))
        
        primeira_data = self._format_period_date(periodo_info.get('primeira_data_registrada'))
        ultima_data = self._format_period_date(periodo_info.get('ultima_data_registrada'))
        
        periodo_data = [
            ['Informação', 'Valor'],
            ['Primeira Data', primeira_data or 'N/A'],
            ['Última Data', ultima_data or 'N/A'],
            ['Dias com Dados', f"{periodo_info.get('dias_com_dados', 0)} / {periodo_info.get('periodo_solicitado_dias', 0)}"],
            ['Cobertura', f"{periodo_info.get('cobertura_periodo', 0)}%"]
        ]
        
        periodo_table = Table(periodo_data, colWidths=[2.5*inch, 4*inch])
        periodo_table.setStyle(TableStyle(
            self.table_styles.get_header_style() +
            self.table_styles.get_base_table_style() +
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ]
        ))
        
        story.append(periodo_table)
        story.append(Spacer(1, 20))
        return story
    
    def _format_period_date(self, date_value) -> Optional[str]:
        """Formata data do período."""
        if not date_value:
            return None
        
        if isinstance(date_value, datetime):
            return date_value.strftime('%d/%m/%Y')
        
        try:
            return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            return str(date_value)
    
    def create_zebra_table(self, data: List[List[str]], title: str, col_widths: List[float]) -> List:
        """Cria tabela com estilo zebra."""
        story = []
        story.append(Paragraph(title, self.styles.section_style))
        
        table = Table(data, colWidths=[w * inch for w in col_widths])
        table.setStyle(TableStyle(
            self.table_styles.get_header_style() +
            self.table_styles.get_zebra_style(len(data)) +
            self.table_styles.get_base_table_style()
        ))
        
        story.append(table)
        story.append(Spacer(1, 20))
        return story
    
    def create_analysis_table(self, data: List[List[str]], title: str, col_widths: List[float]) -> List:
        """Cria tabela de análise com estilo específico."""
        story = []
        story.append(Paragraph(title, self.styles.section_style))
        
        table = Table(data, colWidths=[w * inch for w in col_widths])
        table.setStyle(TableStyle(
            self.table_styles.get_header_style() +
            self.table_styles.get_base_table_style() +
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ]
        ))
        
        story.append(table)
        story.append(Spacer(1, 20))
        return story
    
    def add_header_footer(self, canvas, doc):
        """Adiciona cabeçalho e rodapé às páginas."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(72, 50, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        canvas.drawRightString(595, 50, f'Página {doc.page}')
        canvas.restoreState() 