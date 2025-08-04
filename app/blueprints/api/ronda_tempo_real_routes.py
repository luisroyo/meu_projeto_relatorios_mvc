"""
APIs para rondas em tempo real usando RondaTempoRealService.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.services.ronda_tempo_real_service import RondaTempoRealService
from app import db
import logging
from datetime import datetime, time, date

logger = logging.getLogger(__name__)

ronda_tempo_real_api_bp = Blueprint('ronda_tempo_real_api', __name__, url_prefix='/api/ronda-tempo-real')

@ronda_tempo_real_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def get_condominios_disponiveis():
    """Obter condomínios disponíveis para rondas."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        condominios = service.obter_condominios_disponiveis()
        
        return jsonify({
            'condominios': [{
                'id': c.id,
                'nome': c.nome
            } for c in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter condomínios: {e}")
        return jsonify({'error': 'Erro ao obter condomínios'}), 500

@ronda_tempo_real_api_bp.route('/iniciar', methods=['POST'])
@jwt_required()
def iniciar_ronda():
    """Iniciar uma nova ronda."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('condominio_id') or not data.get('hora_entrada'):
            return jsonify({'error': 'Condomínio ID e hora de entrada são obrigatórios'}), 400
        
        # Converter hora de entrada
        hora_entrada_str = data['hora_entrada']
        try:
            hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400
        
        service = RondaTempoRealService(current_user_id)
        ronda_data = service.iniciar_ronda(
            condominio_id=data['condominio_id'],
            hora_entrada=hora_entrada,
            observacoes=data.get('observacoes')
        )
        
        return jsonify({
            'message': 'Ronda iniciada com sucesso',
            'ronda': ronda_data
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao iniciar ronda: {e}")
        return jsonify({'error': 'Erro ao iniciar ronda'}), 500

@ronda_tempo_real_api_bp.route('/finalizar/<int:ronda_id>', methods=['POST'])
@jwt_required()
def finalizar_ronda(ronda_id):
    """Finalizar uma ronda em andamento."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('hora_saida'):
            return jsonify({'error': 'Hora de saída é obrigatória'}), 400
        
        # Converter hora de saída
        hora_saida_str = data['hora_saida']
        try:
            hora_saida = datetime.strptime(hora_saida_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400
        
        service = RondaTempoRealService(current_user_id)
        ronda_data = service.finalizar_ronda(
            ronda_id=ronda_id,
            hora_saida=hora_saida,
            observacoes=data.get('observacoes')
        )
        
        return jsonify({
            'message': 'Ronda finalizada com sucesso',
            'ronda': ronda_data
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao finalizar ronda: {e}")
        return jsonify({'error': 'Erro ao finalizar ronda'}), 500

@ronda_tempo_real_api_bp.route('/cancelar/<int:ronda_id>', methods=['POST'])
@jwt_required()
def cancelar_ronda(ronda_id):
    """Cancelar uma ronda em andamento."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        
        sucesso = service.cancelar_ronda(ronda_id)
        
        if sucesso:
            return jsonify({'message': 'Ronda cancelada com sucesso'}), 200
        else:
            return jsonify({'error': 'Não foi possível cancelar a ronda'}), 400
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao cancelar ronda: {e}")
        return jsonify({'error': 'Erro ao cancelar ronda'}), 500

@ronda_tempo_real_api_bp.route('/em-andamento', methods=['GET'])
@jwt_required()
def get_rondas_em_andamento():
    """Obter rondas em andamento do usuário."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        rondas = service.listar_rondas_em_andamento()
        
        rondas_data = []
        for r in rondas:
            rondas_data.append({
                'id': r.id,
                'condominio': {
                    'id': r.condominio.id,
                    'nome': r.condominio.nome
                } if r.condominio else None,
                'hora_entrada': r.hora_entrada_formatada,
                'status': r.status,
                'plantao': r.escala_plantao,
                'turno': r.turno,
                'data_plantao': r.data_plantao.strftime('%d/%m/%Y'),
                'observacoes': r.observacoes
            })
        
        return jsonify({
            'rondas': rondas_data
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter rondas em andamento: {e}")
        return jsonify({'error': 'Erro ao obter rondas em andamento'}), 500

@ronda_tempo_real_api_bp.route('/relatorio', methods=['GET'])
@jwt_required()
def gerar_relatorio():
    """Gerar relatório de plantão."""
    try:
        current_user_id = get_jwt_identity()
        data_plantao_str = request.args.get('data_plantao')
        
        data_plantao = None
        if data_plantao_str:
            try:
                data_plantao = datetime.strptime(data_plantao_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        service = RondaTempoRealService(current_user_id)
        relatorio = service.gerar_relatorio_plantao(data_plantao)
        
        return jsonify({
            'relatorio': relatorio,
            'data_plantao': data_plantao.strftime('%d/%m/%Y') if data_plantao else 'Hoje'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'error': 'Erro ao gerar relatório'}), 500

@ronda_tempo_real_api_bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def get_estatisticas():
    """Obter estatísticas do plantão."""
    try:
        current_user_id = get_jwt_identity()
        data_plantao_str = request.args.get('data_plantao')
        
        data_plantao = None
        if data_plantao_str:
            try:
                data_plantao = datetime.strptime(data_plantao_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        service = RondaTempoRealService(current_user_id)
        estatisticas = service.obter_estatisticas_plantao(data_plantao)
        
        return jsonify(estatisticas), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro ao obter estatísticas'}), 500

@ronda_tempo_real_api_bp.route('/hora-atual', methods=['GET'])
@jwt_required()
def get_hora_atual():
    """Obter hora atual do servidor."""
    try:
        hora_atual = datetime.now().strftime('%H:%M:%S')
        return jsonify({
            'hora_atual': hora_atual
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter hora atual: {e}")
        return jsonify({'error': 'Erro ao obter hora atual'}), 500

@ronda_tempo_real_api_bp.route('/condominios-com-ronda-em-andamento', methods=['GET'])
@jwt_required()
def get_condominios_com_ronda_em_andamento():
    """Obter condomínios que têm ronda em andamento."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        condominios = service.condominios_com_ronda_em_andamento()
        
        return jsonify({
            'condominios': [{
                'id': c.id,
                'nome': c.nome
            } for c in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter condomínios com ronda em andamento: {e}")
        return jsonify({'error': 'Erro ao obter condomínios'}), 500

@ronda_tempo_real_api_bp.route('/condominios-com-ronda-realizada', methods=['GET'])
@jwt_required()
def get_condominios_com_ronda_realizada():
    """Obter condomínios que têm ronda realizada no plantão."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        condominios = service.condominios_com_ronda_realizada_plantao()
        
        return jsonify({
            'condominios': [{
                'id': c.id,
                'nome': c.nome
            } for c in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter condomínios com ronda realizada: {e}")
        return jsonify({'error': 'Erro ao obter condomínios'}), 500

@ronda_tempo_real_api_bp.route('/rondas-condominio/<int:condominio_id>', methods=['GET'])
@jwt_required()
def get_rondas_condominio(condominio_id):
    """Obter rondas de um condomínio específico no plantão."""
    try:
        current_user_id = get_jwt_identity()
        service = RondaTempoRealService(current_user_id)
        rondas = service.listar_rondas_do_condominio_plantao(condominio_id)
        
        rondas_data = []
        for r in rondas:
            rondas_data.append({
                'id': r.id,
                'hora_entrada': r.hora_entrada_formatada,
                'hora_saida': r.hora_saida_formatada,
                'status': r.status,
                'plantao': r.escala_plantao,
                'turno': r.turno,
                'duracao': r.duracao_formatada,
                'observacoes': r.observacoes
            })
        
        return jsonify({
            'rondas': rondas_data
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter rondas do condomínio: {e}")
        return jsonify({'error': 'Erro ao obter rondas do condomínio'}), 500 