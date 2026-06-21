"""
APIs de paradas para fornecer dados para o frontend.
"""
import logging
import os
import tempfile
from datetime import datetime, date, timedelta
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, func

from app import db
from app.models import Parada, Condominio, User
from app.services.parada_routes_core.routes_service import ParadaRoutesService
from app.services.whatsapp_processor import WhatsAppProcessor
from app.services.excel_processor import ExcelProcessor
from app.services.parada_utils import get_system_user, infer_condominio_from_filename
from app.blueprints.api.utils import success_response, error_response

logger = logging.getLogger(__name__)

parada_api_bp = Blueprint('parada_api', __name__, url_prefix='/api/paradas')


@parada_api_bp.route('', methods=['GET'])
@parada_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_paradas():
    """Listar paradas com paginação e filtros."""
    try:
        page = request.args.get('page', 1, type=int)
        
        # Filtros
        condominio_id = request.args.get('condominio_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        turno = request.args.get('turno')
        supervisor_id = request.args.get('supervisor_id')
        
        filter_params = {}
        if condominio_id:
            filter_params['condominio_id'] = condominio_id
        if data_inicio:
            filter_params['data_inicio'] = data_inicio
        if data_fim:
            filter_params['data_fim'] = data_fim
        if turno and turno.strip():
            filter_params['turno'] = turno
        if supervisor_id:
            filter_params['supervisor_id'] = supervisor_id

        # Obter dados usando o serviço
        (
            paradas_pagination,
            total_paradas,
            soma_duracao,
            duracao_media,
            _,
            supervisor_mais_ativo,
            _,
            _,
            _,
            _
        ) = ParadaRoutesService.listar_paradas(page=page, filter_params=filter_params)

        # Serializar paradas
        paradas = []
        for p in paradas_pagination.items:
            try:
                paradas.append({
                    'id': p.id,
                    'condominio': {'id': p.condominio.id, 'nome': p.condominio.nome} if p.condominio else None,
                    'condominio_id': p.condominio_id,
                    'data_plantao_parada': p.data_plantao_parada.isoformat() if p.data_plantao_parada else None,
                    'escala_plantao': p.escala_plantao,
                    'turno_parada': p.turno_parada,
                    'supervisor': {'id': p.supervisor.id, 'username': p.supervisor.username} if p.supervisor else None,
                    'supervisor_id': p.supervisor_id,
                    'user': p.criador.username if p.criador else 'N/A',
                    'user_id': p.user_id,
                    'data_criacao': p.data_hora_inicio.isoformat() if p.data_hora_inicio else None,
                    'total_paradas_no_log': p.total_paradas_no_log,
                    'duracao_minutos': p.duracao_total_paradas_minutos,
                    'log_parada_bruto': p.log_parada_bruto,
                    'primeiro_evento_log_dt': p.primeiro_evento_log_dt.isoformat() if p.primeiro_evento_log_dt else None
                })
            except Exception as e:
                logger.error(f"Erro ao serializar parada {p.id}: {e}")
                continue

        # Mapeamento do has_next/has_prev de paginação
        has_next = paradas_pagination.has_next
        has_prev = paradas_pagination.has_prev

        return success_response(
            data={
                'paradas': paradas,
                'pagination': {
                    'page': page,
                    'pages': paradas_pagination.pages,
                    'total': paradas_pagination.total,
                    'per_page': 10,
                    'has_next': has_next,
                    'has_prev': has_prev
                },
                'stats': {
                    'total_paradas': total_paradas,
                    'duracao_total': soma_duracao,
                    'duracao_media': duracao_media,
                    'supervisor_mais_ativo': supervisor_mais_ativo
                }
            },
            message='Paradas listadas com sucesso'
        )
    except Exception as e:
        logger.error(f"Erro ao listar paradas: {e}", exc_info=True)
        return error_response('Erro interno ao listar paradas', status_code=500)


@parada_api_bp.route('/<int:parada_id>', methods=['GET'])
@jwt_required()
def obter_parada(parada_id):
    """Obter detalhes de uma parada específica."""
    try:
        p = Parada.query.options(
            db.joinedload(Parada.condominio),
            db.joinedload(Parada.supervisor),
            db.joinedload(Parada.criador)
        ).get(parada_id)
        
        if not p:
            return error_response('Parada não encontrada', status_code=404)
        
        parada_data = {
            'id': p.id,
            'condominio': {
                'id': p.condominio.id,
                'nome': p.condominio.nome
            } if p.condominio else None,
            'condominio_id': p.condominio_id,
            'data_plantao_parada': p.data_plantao_parada.isoformat() if p.data_plantao_parada else None,
            'escala_plantao': p.escala_plantao,
            'turno_parada': p.turno_parada,
            'log_parada_bruto': p.log_parada_bruto,
            'relatorio_processado': p.relatorio_processado,
            'total_paradas_no_log': p.total_paradas_no_log,
            'duracao_minutos': p.duracao_total_paradas_minutos,
            'supervisor': {
                'id': p.supervisor.id,
                'username': p.supervisor.username
            } if p.supervisor else None,
            'user': {
                'id': p.criador.id,
                'username': p.criador.username
            } if p.criador else None,
            'data_criacao': p.data_hora_inicio.isoformat() if p.data_hora_inicio else None,
            'primeiro_evento_log_dt': p.primeiro_evento_log_dt.isoformat() if p.primeiro_evento_log_dt else None,
            'ultimo_evento_log_dt': p.ultimo_evento_log_dt.isoformat() if p.ultimo_evento_log_dt else None
        }
        
        return success_response(
            data={'parada': parada_data},
            message='Parada obtida com sucesso'
        )
    except Exception as e:
        logger.error(f"Erro ao obter parada {parada_id}: {e}", exc_info=True)
        return error_response('Erro interno ao obter parada', status_code=500)


@parada_api_bp.route('/<int:parada_id>', methods=['DELETE'])
@jwt_required()
def deletar_parada(parada_id):
    """Deletar parada (Apenas Admins)."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return error_response('Apenas administradores podem deletar paradas', status_code=403)
            
        success, message, status_code = ParadaRoutesService.excluir_parada(parada_id, user)
        if success:
            return success_response(data={'parada_id': parada_id}, message=message)
        else:
            return error_response(message, status_code=status_code)
    except Exception as e:
        logger.error(f"Erro ao deletar parada {parada_id}: {e}", exc_info=True)
        return error_response('Erro interno ao deletar parada', status_code=500)


@parada_api_bp.route('/upload-process', methods=['POST'])
@jwt_required()
def upload_processar_parada():
    """Upload e processamento de arquivos de parada (local ou Google Drive)."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        google_file_id = request.form.get('google_file_id')
        google_access_token = request.form.get('google_access_token')
        google_file_name = request.form.get('google_file_name')
        
        # Filtros de data e escala opcionais (para log .txt do WhatsApp)
        condominio_id = request.form.get('condominio_id', type=int)
        data_plantao_str = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        supervisor_id = request.form.get('supervisor_id')
        
        temp_filepath = None
        
        if google_file_id and google_access_token:
            # Import via Google Drive
            try:
                import requests
                headers = {"Authorization": f"Bearer {google_access_token}"}
                download_url = f"https://www.googleapis.com/drive/v3/files/{google_file_id}?alt=media"
                response = requests.get(download_url, headers=headers)
                if response.status_code != 200:
                    return error_response(f"Erro ao baixar do Google Drive (Status {response.status_code}): {response.text}", status_code=400)
                
                temp_dir = os.path.join(tempfile.gettempdir(), "whatsapp_parada_api")
                os.makedirs(temp_dir, exist_ok=True)
                google_file_name_use = google_file_name or 'google_drive_file.xlsx'
                temp_filepath = os.path.join(temp_dir, google_file_name_use)
                with open(temp_filepath, 'wb') as f:
                    f.write(response.content)
                filename = google_file_name_use
            except Exception as e:
                logger.error(f"Erro ao acessar Google Drive: {e}", exc_info=True)
                return error_response(f"Erro ao baixar do Google Drive: {str(e)}", status_code=500)
        else:
            # Upload local
            # Aceitamos tanto 'file' quanto 'whatsapp_file' para compatibilidade
            file = request.files.get('file') or request.files.get('whatsapp_file')
            if not file or file.filename == '':
                return error_response('Nenhum arquivo enviado', status_code=400)
                
            temp_dir = os.path.join(tempfile.gettempdir(), "whatsapp_parada_api")
            os.makedirs(temp_dir, exist_ok=True)
            temp_filepath = os.path.join(temp_dir, file.filename)
            file.save(temp_filepath)
            filename = file.filename

        try:
            is_excel = filename.lower().endswith('.xlsx')
            
            if is_excel:
                # ---------------- PROCESSAMENTO EXCEL (LOTE) ----------------
                parsed_data = ExcelProcessor.parse_excel_file_paradas(temp_filepath)
                if not parsed_data.get("success"):
                    return error_response(parsed_data.get("message", "Erro ao processar planilha Excel."), status_code=400)
                
                system_user = get_system_user() or current_user
                
                supervisor_id_db = None
                if parsed_data.get("supervisor"):
                    sup_name = parsed_data["supervisor"].strip().lower()
                    supervisors = User.query.filter_by(is_supervisor=True).all()
                    for s in supervisors:
                        username_lower = s.username.lower()
                        if sup_name in username_lower or username_lower in sup_name:
                            supervisor_id_db = str(s.id)
                            break
                
                total_paradas_salvas = 0
                messages = []
                
                for condo_name, rounds in parsed_data.get("condominios", {}).items():
                    if not rounds:
                        continue
                    try:
                        condominio = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condo_name)).first()
                        if not condominio:
                            condominio = Condominio(nome=condo_name)
                            db.session.add(condominio)
                            db.session.flush()
                            logger.info(f"Condomínio '{condo_name}' criado via importação REST API.")
                            
                        log_bruto = ExcelProcessor.generate_simulated_whatsapp_log_parada(parsed_data, condo_name)
                        if not log_bruto:
                            continue
                            
                        parada_data = {
                            "condominio_id": str(condominio.id),
                            "data_plantao": parsed_data.get("data_iso"),
                            "escala_plantao": parsed_data.get("escala_plantao"),
                            "log_bruto": log_bruto,
                            "parada_id": None,
                            "supervisor_id": supervisor_id_db,
                        }
                        
                        success, message, status_code, parada_id = ParadaRoutesService.salvar_parada(parada_data, system_user)
                        if success:
                            total_paradas_salvas += 1
                            messages.append(f"Parada para {condo_name} salva com ID {parada_id}.")
                        else:
                            messages.append(f"Falha em {condo_name}: {message}")
                    except Exception as e_condo:
                        messages.append(f"Erro em {condo_name}: {str(e_condo)}")
                        
                return success_response(
                    data={
                        'total_salvas': total_paradas_salvas,
                        'detalhes': messages
                    },
                    message=f"Processamento concluído. {total_paradas_salvas} parada(s) importada(s)."
                )
                
            else:
                # ---------------- PROCESSAMENTO TXT (WHATSAPP INDIVIDUAL) ----------------
                # Para TXT, os campos adicionais são obrigatórios
                if not condominio_id or not data_plantao_str or not escala_plantao:
                    return error_response('Para logs em texto (.txt), condomínio, data do plantão e escala do plantão são obrigatórios.', status_code=400)
                
                condominio_obj = Condominio.query.get(condominio_id)
                if not condominio_obj:
                    return error_response('Condomínio não encontrado.', status_code=404)
                
                # Definir range de datas
                data_plantao = date.fromisoformat(data_plantao_str)
                data_dt = datetime.combine(data_plantao, datetime.min.time())
                if escala_plantao == "06h às 18h":
                    data_inicio = data_dt.replace(hour=6, minute=0, second=0)
                    data_fim = data_dt.replace(hour=17, minute=59, second=59)
                else:
                    data_inicio = data_dt.replace(hour=18, minute=0, second=0)
                    data_fim = (data_dt + timedelta(days=1)).replace(hour=5, minute=59, second=59)
                
                processor = WhatsAppProcessor()
                plantoes = processor.process_file(temp_filepath, data_inicio, data_fim)
                
                if not plantoes:
                    return error_response('Nenhum plantão correspondente encontrado no arquivo de texto.', status_code=404)
                
                log_formatado = processor.format_for_ronda_log(plantoes[0])
                
                parada_data = {
                    "condominio_id": str(condominio_obj.id),
                    "data_plantao": data_plantao_str,
                    "escala_plantao": escala_plantao,
                    "log_bruto": log_formatado,
                    "parada_id": None,
                    "supervisor_id": supervisor_id,
                }
                
                success, message, status_code, parada_id = ParadaRoutesService.salvar_parada(parada_data, current_user)
                if success:
                    return success_response(
                        data={'parada_id': parada_id},
                        message='Parada de texto processada e registrada com sucesso!'
                    )
                else:
                    return error_response(message, status_code=status_code)
                
        finally:
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception as e_clean:
                    logger.error(f"Erro ao remover arquivo temporário {temp_filepath}: {e_clean}")
                    
    except Exception as e:
        logger.error(f"Erro ao fazer upload e processar parada: {e}", exc_info=True)
        return error_response(f'Erro interno ao processar arquivo: {str(e)}', status_code=500)


@parada_api_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def obter_dashboard_stats():
    """Obter estatísticas de paradas para gráficos do dashboard."""
    try:
        # Filtros de query
        year = request.args.get('year', datetime.now().year, type=int)
        condominio_id = request.args.get('condominio_id', type=int)
        
        # Filtro de data do ano completo
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        query = Parada.query.filter(Parada.data_plantao_parada >= start_date, Parada.data_plantao_parada <= end_date)
        if condominio_id:
            query = query.filter(Parada.condominio_id == condominio_id)
            
        paradas = query.all()
        
        # Agrupar dados mensalmente
        mensal_stats = {m: {'count': 0, 'duracao': 0} for m in range(1, 13)}
        condominio_breakdown = {}
        supervisor_breakdown = {}
        
        total_paradas = 0
        total_duracao = 0
        
        for p in paradas:
            m = p.data_plantao_parada.month
            cnt = p.total_paradas_no_log or 0
            dur = p.duracao_total_paradas_minutos or 0
            
            mensal_stats[m]['count'] += cnt
            mensal_stats[m]['duracao'] += dur
            total_paradas += cnt
            total_duracao += dur
            
            # Condominio breakdown
            c_name = p.condominio.nome if p.condominio else 'Desconhecido'
            condominio_breakdown[c_name] = condominio_breakdown.get(c_name, 0) + cnt
            
            # Supervisor breakdown
            s_name = p.supervisor.username if p.supervisor else 'Automático'
            supervisor_breakdown[s_name] = supervisor_breakdown.get(s_name, 0) + cnt

        # Formatar históricos para o frontend
        historico_count = [mensal_stats[m]['count'] for m in range(1, 13)]
        historico_duracao = [mensal_stats[m]['duracao'] for m in range(1, 13)]
        
        return success_response(
            data={
                'stats': {
                    'total_paradas': total_paradas,
                    'duracao_total': total_duracao,
                    'duracao_media': round(total_duracao / total_paradas, 2) if total_paradas > 0 else 0
                },
                'historico': {
                    'meses': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                    'count': historico_count,
                    'duracao': historico_duracao
                },
                'breakdown': {
                    'condominios': [{'name': k, 'value': v} for k, v in condominio_breakdown.items()],
                    'supervisores': [{'name': k, 'value': v} for k, v in supervisor_breakdown.items()]
                }
            },
            message='Estatísticas do dashboard de paradas obtidas com sucesso'
        )
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do dashboard de paradas: {e}", exc_info=True)
        return error_response('Erro interno ao obter estatísticas', status_code=500)
