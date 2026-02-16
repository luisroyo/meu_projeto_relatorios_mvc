from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required
from app import db
from app.models.colaborador import Colaborador
from . import api_bp

@api_bp.route('/colaboradores', methods=['GET'])
@jwt_required()
def list_colaboradores():
    """Listar colaboradores com paginação e filtro."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'Ativo')

        query = Colaborador.query

        if status and status != 'Todos':
            query = query.filter_by(status=status)
        
        if search:
            query = query.filter(Colaborador.nome_completo.ilike(f'%{search}%'))
        
        pagination = query.order_by(Colaborador.nome_completo).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'colaboradores': [{
                'id': c.id,
                'nome_completo': c.nome_completo,
                'cargo': c.cargo,
                'matricula': c.matricula,
                'data_admissao': c.data_admissao.isoformat() if c.data_admissao else None,
                'status': c.status
            } for c in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': per_page
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar colaboradores: {e}", exc_info=True)
        return jsonify({'error': 'Erro ao listar colaboradores'}), 500

@api_bp.route('/colaboradores', methods=['POST'])
@jwt_required()
def create_colaborador():
    """Criar novo colaborador."""
    try:
        data = request.get_json()
        
        # Validação básica
        if not data.get('nome_completo') or not data.get('cargo'):
            return jsonify({'error': 'Nome e Cargo são obrigatórios'}), 400

        novo_colaborador = Colaborador(
            nome_completo=data['nome_completo'],
            cargo=data['cargo'],
            matricula=data.get('matricula'),
            status=data.get('status', 'Ativo')
        )
        
        if data.get('data_admissao'):
            from datetime import datetime
            novo_colaborador.data_admissao = datetime.strptime(data['data_admissao'], '%Y-%m-%d').date()

        db.session.add(novo_colaborador)
        db.session.commit()
        
        return jsonify({
            'message': 'Colaborador criado com sucesso',
            'id': novo_colaborador.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar colaborador: {e}", exc_info=True)
        return jsonify({'error': 'Erro ao criar colaborador'}), 500

@api_bp.route('/colaboradores/<int:id>', methods=['GET'])
@jwt_required()
def get_colaborador(id):
    """Obter detalhes de um colaborador."""
    try:
        colaborador = Colaborador.query.get_or_404(id)
        return jsonify({
            'id': colaborador.id,
            'nome_completo': colaborador.nome_completo,
            'cargo': colaborador.cargo,
            'matricula': colaborador.matricula,
            'data_admissao': colaborador.data_admissao.isoformat() if colaborador.data_admissao else None,
            'status': colaborador.status
        }), 200
    except Exception as e:
        return jsonify({'error': 'Colaborador não encontrado'}), 404

@api_bp.route('/colaboradores/<int:id>', methods=['PUT'])
@jwt_required()
def update_colaborador(id):
    """Atualizar colaborador."""
    try:
        colaborador = Colaborador.query.get_or_404(id)
        data = request.get_json()
        
        if 'nome_completo' in data:
            colaborador.nome_completo = data['nome_completo']
        if 'cargo' in data:
            colaborador.cargo = data['cargo']
        if 'matricula' in data:
            colaborador.matricula = data['matricula']
        if 'status' in data:
            colaborador.status = data['status']
        if 'data_admissao' in data:
            from datetime import datetime
            colaborador.data_admissao = datetime.strptime(data['data_admissao'], '%Y-%m-%d').date()

        db.session.commit()
        
        return jsonify({'message': 'Colaborador atualizado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar colaborador: {e}", exc_info=True)
        return jsonify({'error': 'Erro ao atualizar colaborador'}), 500

@api_bp.route('/colaboradores/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_colaborador(id):
    """Excluir (soft delete) colaborador."""
    try:
        colaborador = Colaborador.query.get_or_404(id)
        colaborador.status = 'Inativo' # Soft delete
        db.session.commit()
        return jsonify({'message': 'Colaborador inativado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao inativar colaborador'}), 500
