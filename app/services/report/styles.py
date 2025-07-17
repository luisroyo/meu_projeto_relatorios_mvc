# app/services/report/styles.py
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


class ReportStyles:
    """Classe para gerenciar estilos dos relatórios."""
    
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


class TableStyles:
    """Classe para gerenciar estilos de tabelas."""
    
    @staticmethod
    def get_header_style():
        """Retorna estilo para cabeçalhos de tabela."""
        return [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]
    
    @staticmethod
    def get_zebra_style(data_length: int, base_color: colors.Color = colors.beige):
        """Retorna estilo zebra para tabelas."""
        zebra_style = []
        for i in range(1, data_length):
            if i % 2 == 0:
                zebra_style.append(('BACKGROUND', (0, i), (-1, i), colors.whitesmoke))
            else:
                zebra_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
        return zebra_style
    
    @staticmethod
    def get_base_table_style():
        """Retorna estilo base para tabelas."""
        return [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ] 