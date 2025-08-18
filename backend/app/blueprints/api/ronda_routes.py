"""
APIs de rondas para fornecer dados para o frontend.
Versão refatorada - usando apenas modelo Ronda unificado.
"""
import logging
from datetime import datetime
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

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
            db.joinedload(Ronda.user)
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
        
        # Serializar rondas
        rondas = []
        for r in pagination.items:
            try:
                rondas.append({
                    'id': r.id,
                    'condominio': r.condominio.nome if r.condominio else 'N/A',
                    'condominio_id': r.condominio_id,
                    'data_plantao_ronda': r.data_plantao_ronda.isoformat() if r.data_plantao_ronda else None,
                    'escala_plantao': r.escala_plantao,
                    'status': r.status,
                    'tipo': r.tipo,
                    'supervisor': r.supervisor.username if r.supervisor else 'N/A',
                    'supervisor_id': r.supervisor_id,
                    'user': r.user.username if r.user else 'N/A',
                    'user_id': r.user_id,
                    'data_criacao': r.data_criacao.isoformat() if r.data_criacao else None
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
            db.joinedload(Ronda.user)
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
                'id': ronda.user.id,
                'username': ronda.user.username
            } if ronda.user else None,
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
        if 'file' not in request.files:
            return error_response('Nenhum arquivo enviado', status_code=400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('Nenhum arquivo selecionado', status_code=400)
        
        # Validação de arquivo
        allowed_extensions = {'txt', 'csv', 'xlsx', 'pdf'}
        if not (file.filename and '.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return error_response(
                'Tipo de arquivo não permitido. Use .txt, .csv, .xlsx ou .pdf', 
                status_code=400
            )
        
        # TODO: Implementar processamento do arquivo
        # Por enquanto, retornar dados mockados
        resultado_processado = {
            'arquivo_processado': file.filename,
            'tamanho_arquivo': len(file.read()),
            'status': 'processado',
            'ronda_criada': False
        }
        
        return success_response(
            data={'resultado': resultado_processado},
            message='Arquivo de ronda processado com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo de ronda: {e}")
        return error_response('Erro interno ao processar arquivo', status_code=500)


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