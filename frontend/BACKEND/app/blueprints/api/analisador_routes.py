"""
APIs para análise de relatórios usando IA.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.processing_history import ProcessingHistory
from app.services.patrimonial_report_service import PatrimonialReportService
from app.utils.classificador import classificar_ocorrencia
from app import db
import logging

logger = logging.getLogger(__name__)

analisador_api_bp = Blueprint('analisador_api', __name__, url_prefix='/api/analisador')

@analisador_api_bp.route('/processar-relatorio', methods=['POST'])
@jwt_required()
def processar_relatorio():
    """Processar relatório usando IA."""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if not data or not data.get('relatorio_bruto'):
        return jsonify({'error': 'Relatório bruto é obrigatório'}), 400
    
    try:
        # Classificar ocorrência
        classificacao = classificar_ocorrencia(data['relatorio_bruto'])
        
        # Processar relatório patrimonial
        patrimonial_service = PatrimonialReportService()
        relatorio_processado = patrimonial_service.gerar_relatorio_seguranca(data['relatorio_bruto'])
        
        # Salvar histórico
        history = ProcessingHistory(
            user_id=current_user_id,
            processing_type="patrimonial_report",
            success=True,
            error_message=None
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'classificacao': classificacao,
            'relatorio_processado': relatorio_processado
        }), 200
        
    except Exception as e:
        # Salvar histórico de erro
        try:
            history = ProcessingHistory(
                user_id=current_user_id,
                processing_type="patrimonial_report",
                success=False,
                error_message=str(e)
            )
            db.session.add(history)
            db.session.commit()
        except Exception as history_error:
            logger.error(f"Erro ao salvar histórico: {history_error}")
        
        logger.error(f"Erro ao processar relatório: {e}")
        return jsonify({'error': 'Erro ao processar relatório'}), 500

@analisador_api_bp.route('/historico', methods=['GET'])
@jwt_required()
def obter_historico():
    """Obter histórico de processamentos do usuário."""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        historico_pagination = ProcessingHistory.query.filter_by(
            user_id=current_user_id
        ).order_by(ProcessingHistory.data_processamento.desc()).paginate(
            page=page, per_page=per_page
        )
        
        historico = []
        for h in historico_pagination.items:
            historico.append({
                'id': h.id,
                'tipo_processamento': h.processing_type,
                'sucesso': h.success,
                'mensagem_erro': h.error_message,
                'data_processamento': h.data_processamento.isoformat() if h.data_processamento else None
            })
        
        return jsonify({
            'historico': historico,
            'pagination': {
                'page': historico_pagination.page,
                'pages': historico_pagination.pages,
                'per_page': historico_pagination.per_page,
                'total': historico_pagination.total,
                'has_next': historico_pagination.has_next,
                'has_prev': historico_pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return jsonify({'error': 'Erro ao obter histórico'}), 500 