"""
APIs de rondas para fornecer dados para o frontend.
Versão refatorada - usando apenas modelo Ronda unificado.
"""
import logging
from datetime import datetime
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, func

from app import db
from app.models import Ronda, Condominio, User
from app.blueprints.api.utils import success_response, error_response

logger = logging.getLogger(__name__)

ronda_api_bp = Blueprint('ronda_api', __name__, url_prefix='/api/rondas')


@ronda_api_bp.route('', methods=['GET'])
@ronda_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_rondas():
    """Listar rondas com paginação e filtros."""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtros
        condominio_id = request.args.get('condominio_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        supervisor_id = request.args.get('supervisor_id', type=int)
        
        # Query base com relacionamentos
        query = Ronda.query.options(
            db.joinedload(Ronda.condominio),
            db.joinedload(Ronda.supervisor),
            db.joinedload(Ronda.criador)
        )
        
        # Aplicar filtros
        if condominio_id:
            query = query.filter(Ronda.condominio_id == condominio_id)
        if data_inicio:
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio)
        if data_fim:
            query = query.filter(Ronda.data_plantao_ronda <= data_fim)
        if status and status.strip():
            query = query.filter(Ronda.status == status)
        if supervisor_id:
            query = query.filter(Ronda.supervisor_id == supervisor_id)
        
        # Ordenação
        query = query.order_by(desc(Ronda.data_plantao_ronda))
        
        # Paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Calcular estatísticas do filtro atual (Paridade com legado)
        try:
            # 1. Total de rondas (soma das rondas no log)
            total_rondas_stats = query.with_entities(func.sum(Ronda.total_rondas_no_log)).scalar() or 0
            
            # 2. Duração total (minutos)
            duracao_total_stats = query.with_entities(func.sum(Ronda.duracao_total_rondas_minutos)).scalar() or 0
            
            # 3. Média de duração
            count_rondas = query.count()
            duracao_media_stats = round(duracao_total_stats / count_rondas, 2) if count_rondas > 0 else 0
            
            # 4. Supervisor mais ativo
            supervisor_mais_ativo_stats = "N/A"
            if count_rondas > 0:
                # Agrupa por ID para evitar conflitos de join com query principal
                top_sup_data = query.with_entities(
                    Ronda.supervisor_id, 
                    func.sum(Ronda.total_rondas_no_log).label('total')
                ).group_by(Ronda.supervisor_id).order_by(desc('total')).first()
                
                if top_sup_data and top_sup_data.supervisor_id:
                    supervisor_obj = User.query.get(top_sup_data.supervisor_id)
                    if supervisor_obj:
                        supervisor_mais_ativo_stats = supervisor_obj.username

            # 5. Média de rondas por dia
            media_rondas_dia_stats = "N/A"
            if data_inicio and data_fim:
                dt_inicio = datetime.fromisoformat(str(data_inicio))
                dt_fim = datetime.fromisoformat(str(data_fim))
                delta_days = (dt_fim - dt_inicio).days + 1
                if delta_days > 0:
                    media_rondas_dia_stats = round(total_rondas_stats / delta_days, 1)
        except Exception as e_stats:
            logger.error(f"Erro ao calcular estatísticas: {e_stats}")
            # Valores default em caso de erro nos stats
            total_rondas_stats = 0
            duracao_total_stats = 0
            duracao_media_stats = 0
            supervisor_mais_ativo_stats = "Erro"
            media_rondas_dia_stats = "N/A"

        # Serializar rondas
        rondas = []
        for r in pagination.items:
            try:
                rondas.append({
                    'id': r.id,
                    'condominio': {'id': r.condominio.id, 'nome': r.condominio.nome} if r.condominio else None,
                    'condominio_id': r.condominio_id,
                    'data_plantao_ronda': r.data_plantao_ronda.isoformat() if r.data_plantao_ronda else None,
                    'escala_plantao': r.escala_plantao,
                    'turno_ronda': r.turno_ronda,
                    'supervisor': {'id': r.supervisor.id, 'username': r.supervisor.username} if r.supervisor else None,
                    'supervisor_id': r.supervisor_id,
                    'user': r.criador.username if r.criador else 'N/A',
                    'user_id': r.user_id,
                    'data_criacao': r.data_hora_inicio.isoformat() if r.data_hora_inicio else None,
                    'total_rondas_no_log': r.total_rondas_no_log,
                    'duracao_minutos': r.duracao_total_rondas_minutos,
                    'log_ronda_bruto': r.log_ronda_bruto,
                    'status': r.status,
                    'primeiro_evento_log_dt': r.primeiro_evento_log_dt.isoformat() if r.primeiro_evento_log_dt else None
                })
            except Exception as e:
                logger.error(f"Erro ao serializar ronda {r.id}: {e}")
                continue
        
        return success_response(
            data={
                'rondas': rondas,
                'pagination': {
                    'page': page,
                    'pages': pagination.pages,
                    'total': pagination.total,
                    'per_page': per_page,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'stats': {
                    'total_rondas': total_rondas_stats,
                    'duracao_total': duracao_total_stats,
                    'duracao_media': duracao_media_stats,
                    'supervisor_mais_ativo': supervisor_mais_ativo_stats,
                    'media_rondas_dia': media_rondas_dia_stats
                }
            },
            message='Rondas listadas com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar rondas: {e}")
        return error_response('Erro interno ao listar rondas', status_code=500)


@ronda_api_bp.route('/<int:ronda_id>', methods=['GET'])
@jwt_required()
def obter_ronda(ronda_id):
    """Obter detalhes de uma ronda específica."""
    try:
        ronda = Ronda.query.options(
            db.joinedload(Ronda.condominio),
            db.joinedload(Ronda.supervisor),
            db.joinedload(Ronda.criador)
        ).get(ronda_id)
        
        if not ronda:
            return error_response('Ronda não encontrada', status_code=404)
        
        ronda_data = {
            'id': ronda.id,
            'condominio': {
                'id': ronda.condominio.id,
                'nome': ronda.condominio.nome
            } if ronda.condominio else None,
            'data_plantao_ronda': ronda.data_plantao_ronda.isoformat() if ronda.data_plantao_ronda else None,
            'escala_plantao': ronda.escala_plantao,
            'status': ronda.status,
            'tipo': ronda.tipo,
            'log_ronda_bruto': ronda.log_ronda_bruto,
            'relatorio_processado': ronda.relatorio_processado,
            'supervisor': {
                'id': ronda.supervisor.id,
                'username': ronda.supervisor.username
            } if ronda.supervisor else None,
            'user': {
                'id': ronda.criador.id,
                'username': ronda.criador.username
            } if ronda.criador else None,
            'data_criacao': ronda.data_criacao.isoformat() if ronda.data_criacao else None,
            'data_modificacao': ronda.data_modificacao.isoformat() if ronda.data_modificacao else None
        }
        
        return success_response(
            data={'ronda': ronda_data},
            message='Ronda obtida com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter ronda {ronda_id}: {e}")
        return error_response('Erro interno ao obter ronda', status_code=500)


@ronda_api_bp.route('', methods=['POST'])
@ronda_api_bp.route('/', methods=['POST'])
@jwt_required()
def criar_ronda():
    """Criar nova ronda."""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        if not data:
            return error_response('Dados não fornecidos', status_code=400)
        
        # Campos obrigatórios
        required_fields = ['condominio_id', 'data_plantao_ronda', 'escala_plantao']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return error_response(f'Campos obrigatórios: {", ".join(missing_fields)}', status_code=400)
        
        # Criar nova ronda
        nova_ronda = Ronda(
            condominio_id=data['condominio_id'],
            data_plantao_ronda=datetime.fromisoformat(data['data_plantao_ronda']),
            escala_plantao=data['escala_plantao'],
            log_ronda_bruto=data.get('log_ronda_bruto', ''),
            relatorio_processado=data.get('relatorio_processado', ''),
            supervisor_id=data.get('supervisor_id'),
            status=data.get('status', 'Agendada'),
            tipo=data.get('tipo', 'Regular'),
            user_id=current_user_id
        )
        
        db.session.add(nova_ronda)
        db.session.commit()
        
        logger.info(f"Ronda {nova_ronda.id} criada por usuário {current_user_id}")
        
        return success_response(
            data={'ronda_id': nova_ronda.id},
            message='Ronda criada com sucesso',
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ronda: {e}")
        return error_response('Erro interno ao criar ronda', status_code=500)


@ronda_api_bp.route('/<int:ronda_id>', methods=['PUT'])
@jwt_required()
def atualizar_ronda(ronda_id):
    """Atualizar ronda."""
    try:
        ronda = Ronda.query.get(ronda_id)
        
        if not ronda:
            return error_response('Ronda não encontrada', status_code=404)
        
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        if not data:
            return error_response('Dados não fornecidos', status_code=400)
        
        # Verificar permissões
        user = User.query.get(current_user_id)
        if not user:
            return error_response('Usuário não encontrado', status_code=404)
        if not (user.is_admin or ronda.supervisor_id == current_user_id or ronda.user_id == current_user_id):
            return error_response('Sem permissão para editar esta ronda', status_code=403)
        
        # Atualizar campos permitidos
        if 'condominio_id' in data:
            ronda.condominio_id = data['condominio_id']
        if 'data_plantao_ronda' in data:
            ronda.data_plantao_ronda = datetime.fromisoformat(data['data_plantao_ronda'])
        if 'escala_plantao' in data:
            ronda.escala_plantao = data['escala_plantao']
        if 'log_ronda_bruto' in data:
            ronda.log_ronda_bruto = data['log_ronda_bruto']
        if 'relatorio_processado' in data:
            ronda.relatorio_processado = data['relatorio_processado']
        if 'supervisor_id' in data:
            ronda.supervisor_id = data['supervisor_id']
        if 'status' in data:
            ronda.status = data['status']
        if 'tipo' in data:
            ronda.tipo = data['tipo']
        
        db.session.commit()
        
        logger.info(f"Ronda {ronda_id} atualizada por usuário {current_user_id}")
        
        return success_response(
            data={'ronda_id': ronda_id},
            message='Ronda atualizada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar ronda {ronda_id}: {e}")
        return error_response('Erro interno ao atualizar ronda', status_code=500)


@ronda_api_bp.route('/<int:ronda_id>', methods=['DELETE'])
@jwt_required()
def deletar_ronda(ronda_id):
    """Deletar ronda."""
    try:
        ronda = Ronda.query.get(ronda_id)
        
        if not ronda:
            return error_response('Ronda não encontrada', status_code=404)
        
        current_user_id = get_jwt_identity()
        
        # Apenas admins podem deletar
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return error_response('Apenas administradores podem deletar rondas', status_code=403)
        
        db.session.delete(ronda)
        db.session.commit()
        
        logger.info(f"Ronda {ronda_id} deletada por usuário {current_user_id}")
        
        return success_response(
            data={'ronda_id': ronda_id},
            message='Ronda deletada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar ronda {ronda_id}: {e}")
        return error_response('Erro interno ao deletar ronda', status_code=500)


@ronda_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios():
    """Listar condomínios para rondas."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        condominios_data = [{
            'id': condominio.id,
            'nome': condominio.nome,
            'endereco': condominio.endereco
        } for condominio in condominios]
        
        return success_response(
            data={'condominios': condominios_data},
            message='Condomínios obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return error_response('Erro interno ao listar condomínios', status_code=500)


@ronda_api_bp.route('/supervisores', methods=['GET'])
@jwt_required()
def listar_supervisores():
    """Listar supervisores para rondas."""
    try:
        supervisores = User.query.filter_by(
            is_supervisor=True, 
            is_approved=True
        ).order_by(User.username).all()
        
        supervisores_data = [{
            'id': supervisor.id,
            'username': supervisor.username,
            'email': supervisor.email
        } for supervisor in supervisores]
        
        return success_response(
            data={'supervisores': supervisores_data},
            message='Supervisores obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar supervisores: {e}")
        return error_response('Erro interno ao listar supervisores', status_code=500)


@ronda_api_bp.route('/status', methods=['GET'])
@jwt_required()
def listar_status():
    """Listar status disponíveis para rondas."""
    try:
        status_list = [
            "Agendada",
            "Em Andamento", 
            "Concluída",
            "Cancelada",
            "Pausada"
        ]
        
        return success_response(
            data={'status': status_list},
            message='Status obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar status: {e}")
        return error_response('Erro interno ao listar status', status_code=500)


@ronda_api_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos():
    """Listar tipos disponíveis para rondas."""
    try:
        tipos_list = [
            "Regular",
            "Esporádica",
            "Emergencial",
            "Noturna",
            "Diurna"
        ]
        
        return success_response(
            data={'tipos': tipos_list},
            message='Tipos obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar tipos: {e}")
        return error_response('Erro interno ao listar tipos', status_code=500)


@ronda_api_bp.route('/process-whatsapp', methods=['POST'])
@jwt_required()
def processar_whatsapp():
    """Processar arquivo WhatsApp para ronda."""
    try:
        if 'file' not in request.files:
            return error_response('Nenhum arquivo enviado', status_code=400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('Nenhum arquivo selecionado', status_code=400)
        
        # Validação de arquivo
        allowed_extensions = {'txt', 'csv'}
        if not (file.filename and '.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return error_response('Tipo de arquivo não permitido. Use .txt ou .csv', status_code=400)
        
        # TODO: Implementar processamento do arquivo WhatsApp
        # Por enquanto, retornar dados mockados
        resultado_processado = {
            'arquivo_processado': file.filename,
            'total_mensagens': 0,
            'rondas_detectadas': 0,
            'status': 'processado'
        }
        
        return success_response(
            data={'resultado': resultado_processado},
            message='Arquivo WhatsApp processado com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo WhatsApp: {e}")
        return error_response('Erro interno ao processar arquivo', status_code=500)


@ronda_api_bp.route('/upload-process', methods=['POST'])
@jwt_required()
def upload_processar_ronda():
    """Upload e processamento de arquivo de ronda."""
    try:
        import os
        import tempfile
        from app.services.whatsapp_processor import WhatsAppProcessor
        from app.services.ronda_utils import infer_condominio_from_filename, get_system_user
        from app.services.ronda_routes_core.routes_service import RondaRoutesService

        if 'file' not in request.files:
            return error_response('Nenhum arquivo enviado', status_code=400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('Nenhum arquivo selecionado', status_code=400)
        
        # Validação de arquivo
        # Por enquanto, focamos em .txt que é o padrão do WhatsApp exportado
        allowed_extensions = {'txt'}
        if not (file.filename and '.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return error_response(
                'Tipo de arquivo não permitido. Apenas .txt é suportado no momento.', 
                status_code=400
            )
        
        # Filtros opcionais de Mês/Ano
        month = request.form.get('month', type=int)
        year = request.form.get('year', type=int)

        # Salvar arquivo temporariamente
        temp_dir = tempfile.gettempdir()
        temp_filepath = os.path.join(temp_dir, file.filename)
        file.save(temp_filepath)
        
        try:
            # 1. Identificar condomínio
            condominio = infer_condominio_from_filename(file.filename)
            if not condominio:
                return error_response(
                    f"Não foi possível identificar o condomínio pelo nome do arquivo '{file.filename}'.", 
                    status_code=400
                )
            
            # 2. Processar arquivo
            processor = WhatsAppProcessor()
            plantoes_encontrados = processor.process_file(temp_filepath)
            
            if not plantoes_encontrados:
                return error_response(
                    "Nenhuma mensagem de plantão válida encontrada no arquivo.", 
                    status_code=404
                )
            
            # 3. Filtrar plantões por mês/ano
            filtered_plantoes = []
            for plantao in plantoes_encontrados:
                process_this = True
                if month and plantao.data.month != month:
                    process_this = False
                if year and plantao.data.year != year:
                    process_this = False
                
                if process_this:
                    filtered_plantoes.append(plantao)
            
            if not filtered_plantoes:
                return error_response(
                    "Nenhum plantão no arquivo corresponde aos filtros selecionados.", 
                    status_code=404
                )
            
            # 4. Salvar rondas
            # Obtém usuário do sistema para ser o "criador" automático, ou usa o usuário logado
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            total_rondas_salvas = 0
            messages = []
            
            for plantao in filtered_plantoes:
                try:
                    log_bruto = processor.format_for_ronda_log(plantao)
                    escala_plantao = "06h às 18h" if plantao.tipo == "diurno" else "18h às 06h"
                    
                    ronda_data = {
                        "condominio_id": str(condominio.id),
                        "data_plantao": plantao.data.strftime("%Y-%m-%d"),
                        "escala_plantao": escala_plantao,
                        "log_bruto": log_bruto,
                        "ronda_id": None,
                        "supervisor_id": None,
                    }
                    
                    success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(ronda_data, current_user)
                    
                    if success:
                        total_rondas_salvas += 1
                        messages.append(f"Ronda para {condominio.nome} em {plantao.data.strftime('%d/%m/%Y')} salva com sucesso (ID: {ronda_id}).")
                    else:
                        messages.append(f"Falha ao salvar ronda de {plantao.data.strftime('%d/%m/%Y')}: {message}")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar plantão individual: {e}")
                    messages.append(f"Erro ao processar plantão de {plantao.data.strftime('%d/%m/%Y')}: {str(e)}")

            if total_rondas_salvas > 0:
                return success_response(
                    data={
                        'total_salvas': total_rondas_salvas,
                        'detalhes': messages
                    },
                    message=f"Processamento concluído. {total_rondas_salvas} ronda(s) salva(s)."
                )
            else:
                return error_response(
                    "Nenhuma ronda foi salva. Verifique os detalhes.",
                    status_code=500,
                    data={'detalhes': messages}
                )
                
        finally:
            # Limpeza
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo de ronda: {e}", exc_info=True)
        return error_response(f'Erro interno ao processar arquivo: {str(e)}', status_code=500)


@ronda_api_bp.route('/tempo-real/hora-atual', methods=['GET'])
@jwt_required()
def obter_hora_atual():
    """Obter hora atual do servidor."""
    try:
        import pytz
        tz = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(tz)
        
        return success_response(
            data={
                'hora_atual': hora_atual.strftime('%H:%M:%S'),
                'data_atual': hora_atual.strftime('%Y-%m-%d'),
                'timestamp': hora_atual.isoformat(),
                'timezone': 'America/Sao_Paulo'
            },
            message='Hora atual obtida com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter hora atual: {e}")
        return error_response('Erro interno ao obter hora atual', status_code=500)