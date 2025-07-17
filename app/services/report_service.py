# app/services/report_service.py
"""
Módulo principal de relatórios - Mantido para compatibilidade.
Use os módulos específicos em app/services/report/ para melhor organização.
"""

from .report import RondaReportService, OcorrenciaReportService

# Mantém a interface original para compatibilidade
__all__ = ['RondaReportService', 'OcorrenciaReportService'] 