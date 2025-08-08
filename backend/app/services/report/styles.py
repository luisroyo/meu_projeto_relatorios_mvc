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
        # Título principal - Reduzido de 24 para 20
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=15,  # Reduzido de 30 para 15
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Subtítulo - Reduzido de 16 para 14
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,  # Reduzido de 20 para 10
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Cabeçalho de seção - Reduzido de 14 para 12
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,   # Reduzido de 15 para 8
            spaceBefore=10, # Reduzido de 20 para 10
            textColor=colors.darkblue
        )
        
        # Texto normal - Mantido em 10
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4    # Reduzido de 6 para 4
        )
        
        # KPI style - Reduzido de 12 para 11
        self.kpi_style = ParagraphStyle(
            'KPIStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,   # Reduzido de 8 para 6
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
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduzido de 11 para 10
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Reduzido de 12 para 8
            ('TOPPADDING', (0, 0), (-1, 0), 6),     # Adicionado padding superior
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
            ('FONTSIZE', (0, 1), (-1, -1), 9),  # Reduzido de 10 para 9
            ('TOPPADDING', (0, 1), (-1, -1), 4),  # Adicionado padding superior
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),  # Adicionado padding inferior
        ] 