import logging
import os
import shutil
from datetime import datetime
from typing import Optional

from app.models import Condominio, Ronda, User # User ainda é necessário para tipagem
from app.services.ronda_routes_core.business_service import atribuir_supervisor
from app.services.ronda_routes_core.persistence_service import (
    get_ronda_by_id, save_ronda, update_ronda
)
from app.services.ronda_routes_core.helpers import inferir_turno
from app.services.ronda_routes_core.validation import validar_campos_essenciais, validar_condominio_existe
from app.services.rondaservice import processar_log_de_rondas
from app.services.whatsapp_processor import WhatsAppProcessor, Plantao
from app.services.ronda_utils import RondaUtils # Importa o novo módulo de utilitários

logger = logging.getLogger(__name__)

class RondaAutomationService:
    def __init__(self, whatsapp_files_dir: str, processed_files_dir: str, error_files_dir: str):
        self.whatsapp_files_dir = whatsapp_files_dir
        self.processed_files_dir = processed_files_dir
        self.error_files_dir = error_files_dir
        self.whatsapp_processor = WhatsAppProcessor()
        
        os.makedirs(self.whatsapp_files_dir, exist_ok=True)
        os.makedirs(self.processed_files_dir, exist_ok=True)
        os.makedirs(self.error_files_dir, exist_ok=True)

    def process_new_whatsapp_files(self, month: Optional[int] = None, year: Optional[int] = None):
        """
        Varre o diretório e processa novos arquivos WhatsApp.
        Pode filtrar por mês e ano específicos.
        """
        logger.info(f"Iniciando varredura por novos arquivos WhatsApp em: {self.whatsapp_files_dir} (Filtro: Mês={month}, Ano={year})")
        
        system_user = RondaUtils.get_system_user() # Usa o utilitário

        for filename in os.listdir(self.whatsapp_files_dir):
            if filename.lower().endswith(".txt"):
                filepath = os.path.join(self.whatsapp_files_dir, filename)
                logger.info(f"Processando arquivo: {filepath}")
                
                try:
                    condominio = RondaUtils.infer_condominio_from_filename(filename) # Usa o utilitário
                    if not condominio:
                        logger.error(f"Não foi possível identificar o condomínio pelo nome do arquivo '{filename}'. Movendo para pasta de erros.")
                        shutil.move(filepath, os.path.join(self.error_files_dir, filename))
                        continue

                    plantoes_encontrados = self.whatsapp_processor.process_file(filepath)

                    if not plantoes_encontrados:
                        logger.warning(f"Nenhum plantão válido encontrado no conteúdo do arquivo: {filename}. Movendo para pasta de erros.")
                        shutil.move(filepath, os.path.join(self.error_files_dir, filename))
                        continue

                    filtered_plantoes = []
                    for plantao in plantoes_encontrados:
                        process_this_plantao = True
                        if month and plantao.data.month != month:
                            process_this_plantao = False
                        if year and plantao.data.year != year:
                            process_this_plantao = False
                        
                        if process_this_plantao:
                            filtered_plantoes.append(plantao)
                        else:
                            logger.info(f"Pulando plantão em {plantao.data.strftime('%d/%m/%Y')} ({plantao.tipo}) do arquivo {filename} devido a filtros de mês/ano.")

                    if not filtered_plantoes:
                        logger.warning(f"Nenhum plantão no arquivo '{filename}' corresponde aos filtros de mês/ano. Arquivo não processado para rondas.")
                        shutil.move(filepath, os.path.join(self.processed_files_dir, filename))
                        continue

                    for plantao in filtered_plantoes:
                        log_bruto = self.whatsapp_processor.format_for_ronda_log(plantao)
                        escala_plantao = "06h às 18h" if plantao.tipo == "diurno" else "18h às 06h"

                        ronda_data = {
                            "condominio_id": str(condominio.id),
                            "data_plantao": plantao.data.strftime("%Y-%m-%d"),
                            "escala_plantao": escala_plantao,
                            "log_bruto_rondas": log_bruto,
                            "ronda_id": None,
                            "supervisor_id": None,
                        }
                        
                        from app.services.ronda_routes_core.routes_service import RondaRoutesService
                        success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(ronda_data, system_user)

                        if success:
                            logger.info(
                                f"Ronda registrada automaticamente para {condominio.nome} em {plantao.data.strftime('%d/%m/%Y')} ({plantao.tipo}). Ronda ID: {ronda_id}"
                            )
                        else:
                            logger.error(
                                f"Falha ao registrar ronda automática para {condominio.nome} em {plantao.data.strftime('%d/%m/%Y')} ({plantao.tipo}): {message}"
                            )

                    shutil.move(filepath, os.path.join(self.processed_files_dir, filename))
                    logger.info(f"Arquivo {filename} processado e movido para {self.processed_files_dir}")

                except Exception as e:
                    from app import db
                    db.session.rollback()
                    logger.error(f"Erro inesperado ao processar o arquivo {filename}: {e}", exc_info=True)
                    shutil.move(filepath, os.path.join(self.error_files_dir, filename))
                    logger.warning(f"Arquivo {filename} movido para pasta de erros devido a exceção.")

