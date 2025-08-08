"""
APIs de rondas para fornecer dados para o frontend.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from app import db
from sqlalchemy import desc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ronda_api_bp = Blueprint('ronda_api', __name__, url_prefix='/api/rondas')

@ronda_api_bp.route('', methods=['GET'])
@ronda_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_rondas():
    """Listar rondas com paginação e filtros."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        condominio_id = request.args.get('condominio_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        query = RondaEsporadica.query
        if condominio_id:
            query = query.filter(RondaEsporadica.condominio_id == condominio_id)
        if data_inicio:
            query = query.filter(RondaEsporadica.data_plantao >= data_inicio)
        if data_fim:
            query = query.filter(RondaEsporadica.data_plantao <= data_fim)
        if status and status.strip():
            query = query.filter(RondaEsporadica.status == status)
        query = query.order_by(desc(RondaEsporadica.data_plantao))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        rondas = []
        for r in pagination.items:
            try:
                rondas.append({
                    'id': r.id,
                    'condominio': r.condominio.nome if r.condominio else 'N/A',
                    'data_plantao': r.data_plantao.isoformat() if r.data_plantao else None,
                    'escala_plantao': r.escala_plantao,
                    'status': r.status,
                    'total_rondas': r.total_rondas,
                    'duracao_minutos': r.duracao_minutos,
                    'observacoes': r.observacoes,
                    'user': r.user.username if r.user else 'N/A',
                    'data_criacao': r.data_criacao.isoformat() if r.data_criacao else None
                })
            except Exception as e:
                logger.error(f"Erro ao serializar ronda {r.id}: {e}")
                continue
        return jsonify({
            'rondas': rondas,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar rondas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/<int:ronda_id>', methods=['GET'])
@jwt_required()
def obter_ronda(ronda_id):
    """Obter detalhes de uma ronda específica."""
    try:
        ronda = RondaEsporadica.query.get_or_404(ronda_id)
        
        return jsonify({
            'id': ronda.id,
            'condominio': {
                'id': ronda.condominio.id,
                'nome': ronda.condominio.nome
            } if ronda.condominio else None,
            'data_plantao': ronda.data_plantao.isoformat() if ronda.data_plantao else None,
            'escala_plantao': ronda.escala_plantao,
            'status': ronda.status,
            'total_rondas': ronda.total_rondas,
            'duracao_minutos': ronda.duracao_minutos,
            'observacoes': ronda.observacoes,
            'user': {
                'id': ronda.user.id,
                'username': ronda.user.username
            } if ronda.user else None,
            'data_criacao': ronda.data_criacao.isoformat() if ronda.data_criacao else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ronda {ronda_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/hora-atual', methods=['GET'])
@jwt_required()
def obter_hora_atual():
    """Obter hora atual do servidor."""
    try:
        hora_atual = datetime.now().strftime('%H:%M:%S')
        return jsonify({
            'hora_atual': hora_atual
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter hora atual: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios_rondas():
    """Listar condomínios para rondas."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        return jsonify({
            'condominios': [{
                'id': condominio.id,
                'nome': condominio.nome
            } for condominio in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 

@ronda_api_bp.route('', methods=['POST'])
@ronda_api_bp.route('/', methods=['POST'])
@jwt_required()
def create_ronda():
    """Criar nova ronda."""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    required_fields = ['condominio_id', 'data_plantao_ronda', 'escala_plantao', 'log_ronda_bruto']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    try:
        from app.models.ronda import Ronda
        from datetime import datetime
        
        nova_ronda = Ronda()
        nova_ronda.condominio_id = data['condominio_id']
        nova_ronda.data_plantao_ronda = datetime.fromisoformat(data['data_plantao_ronda'])
        nova_ronda.escala_plantao = data['escala_plantao']
        nova_ronda.log_ronda_bruto = data['log_ronda_bruto']
        nova_ronda.supervisor_id = data.get('supervisor_id')
        nova_ronda.user_id = current_user_id
        
        # Processar relatório se fornecido
        if data.get('relatorio_processado'):
            nova_ronda.relatorio_processado = data['relatorio_processado']
        
        db.session.add(nova_ronda)
        db.session.commit()
        
        logger.info(f"Ronda {nova_ronda.id} criada por usuário {current_user_id}")
        
        return jsonify({
            'message': 'Ronda criada com sucesso',
            'ronda_id': nova_ronda.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ronda: {e}")
        return jsonify({'error': 'Erro ao criar ronda'}), 500

@ronda_api_bp.route('/<int:ronda_id>', methods=['PUT'])
@jwt_required()
def update_ronda(ronda_id):
    """Atualizar ronda."""
    ronda = RondaEsporadica.query.get_or_404(ronda_id)
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar permissões
    user = User.query.get(current_user_id)
    if not (user.is_admin or ronda.supervisor_id == current_user_id):
        return jsonify({'error': 'Sem permissão para editar esta ronda'}), 403
    
    try:
        if 'condominio_id' in data:
            ronda.condominio_id = data['condominio_id']
        if 'data_plantao_ronda' in data:
            ronda.data_plantao_ronda = datetime.fromisoformat(data['data_plantao_ronda'])
        if 'escala_plantao' in data:
            ronda.escala_plantao = data['escala_plantao']
        if 'log_ronda_bruto' in data:
            ronda.log_ronda_bruto = data['log_ronda_bruto']
        if 'supervisor_id' in data:
            ronda.supervisor_id = data['supervisor_id']
        if 'relatorio_processado' in data:
            ronda.relatorio_processado = data['relatorio_processado']
        
        db.session.commit()
        
        logger.info(f"Ronda {ronda_id} atualizada por usuário {current_user_id}")
        
        return jsonify({'message': 'Ronda atualizada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar ronda {ronda_id}: {e}")
        return jsonify({'error': 'Erro ao atualizar ronda'}), 500

@ronda_api_bp.route('/<int:ronda_id>', methods=['DELETE'])
@jwt_required()
def delete_ronda(ronda_id):
    """Deletar ronda."""
    ronda = RondaEsporadica.query.get_or_404(ronda_id)
    current_user_id = get_jwt_identity()
    
    # Apenas admins podem deletar
    user = User.query.get(current_user_id)
    if not user or not user.is_admin:
        return jsonify({'error': 'Apenas administradores podem deletar rondas'}), 403
    
    try:
        db.session.delete(ronda)
        db.session.commit()
        
        logger.info(f"Ronda {ronda_id} deletada por usuário {current_user_id}")
        return jsonify({'message': 'Ronda deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar ronda {ronda_id}: {e}")
        return jsonify({'error': 'Erro ao deletar ronda'}), 500

@ronda_api_bp.route('/process-whatsapp', methods=['POST'])
@jwt_required()
def process_whatsapp():
    """Processar arquivo WhatsApp."""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        from app.services.whatsapp_processor import WhatsAppProcessor
        import tempfile
        import os
        
        # Salvar arquivo temporário
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Processar arquivo
        processor = WhatsAppProcessor()
        resultado = processor.processar_arquivo(temp_path)
        
        # Limpar arquivo temporário
        os.remove(temp_path)
        
        return jsonify({
            'message': 'Arquivo processado com sucesso',
            'resultado': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo WhatsApp: {e}")
        return jsonify({'error': 'Erro ao processar arquivo'}), 500

@ronda_api_bp.route('/upload-process', methods=['POST'])
@jwt_required()
def upload_process_ronda():
    """Upload e processamento de ronda."""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        from app.services.ronda_automation_service import RondaAutomationService
        import tempfile
        import os
        
        # Salvar arquivo temporário
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Processar arquivo
        service = RondaAutomationService()
        resultado = service.processar_arquivo(temp_path)
        
        # Limpar arquivo temporário
        os.remove(temp_path)
        
        return jsonify({
            'message': 'Arquivo processado com sucesso',
            'resultado': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo de ronda: {e}")
        return jsonify({'error': 'Erro ao processar arquivo'}), 500

@ronda_api_bp.route('/tempo-real', methods=['GET'])
@jwt_required()
def get_rondas_tempo_real():
    """Obter rondas em tempo real."""
    try:
        from app.services.ronda_tempo_real_service import RondaTempoRealService
        
        service = RondaTempoRealService()
        rondas = service.obter_rondas_tempo_real()
        
        return jsonify({
            'rondas': rondas
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter rondas em tempo real: {e}")
        return jsonify({'error': 'Erro ao obter rondas em tempo real'}), 500 