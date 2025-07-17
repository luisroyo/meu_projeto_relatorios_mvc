# app/services/report/ocorrencia_service.py
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from app import db
from app.models import Colaborador, Ocorrencia, ocorrencia_colaboradores
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
            
            # Colaboradores
            story.extend(self._create_colaboradores_section(filters_info))
            
            # Build do documento
            doc.build(story, onFirstPage=self.builder.add_header_footer, onLaterPages=self.builder.add_header_footer)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f'Erro ao gerar relatório PDF de ocorrências: {e}', exc_info=True)
            raise
    
    def _create_colaboradores_section(self, filters_info: Optional[Dict]) -> List:
        """Cria seção de colaboradores."""
        story = []
        story.append(Paragraph('Colaboradores que Atenderam Ocorrências no Período', self.builder.styles.section_style))
        
        # Query para buscar colaboradores
        colab_query = db.session.query(Colaborador.nome_completo)\
            .join(ocorrencia_colaboradores, Colaborador.id == ocorrencia_colaboradores.c.colaborador_id)\
            .join(Ocorrencia, Ocorrencia.id == ocorrencia_colaboradores.c.ocorrencia_id)
        
        # Aplicar filtros de data se disponíveis
        if filters_info:
            data_inicio = filters_info.get('data_inicio')
            data_fim = filters_info.get('data_fim')
            if data_inicio and data_fim:
                try:
                    data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                    data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                    colab_query = colab_query.filter(Ocorrencia.data_hora_ocorrencia.between(data_inicio_dt, data_fim_dt))
                except Exception:
                    pass
        
        colaboradores = [row[0] for row in colab_query.distinct().order_by(Colaborador.nome_completo).all()]
        
        if colaboradores:
            colab_data = [['Colaborador']]
            for nome in colaboradores:
                colab_data.append([nome])
            story.extend(self.builder.create_zebra_table(
                colab_data,
                'Colaboradores que Atenderam Ocorrências no Período',
                [5]
            ))
        else:
            story.append(Paragraph('Nenhum colaborador encontrado no período.', self.builder.styles.normal_style))
            story.append(Spacer(1, 20))
        
        return story 