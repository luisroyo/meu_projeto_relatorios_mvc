# Rotas da API para sistema de rondas em tempo real
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, time, date
from app.services.ronda_tempo_real_service import RondaTempoRealService
from app.models.condominio import Condominio
from app.models.ronda_esporadica import RondaEsporadica
from app import db, csrf
import json

from . import api_bp


@api_bp.route('/ronda-tempo-real/condominios', methods=['GET'])
@login_required
def listar_condominios_tempo_real():
    """Lista todos os condomínios disponíveis para registro de rondas."""
    try:
        service = RondaTempoRealService(current_user.id)
        condominios = service.obter_condominios_disponiveis()
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': c.id,
                    'nome': c.nome
                } for c in condominios
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao listar condomínios: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao listar condomínios'
        }), 500


@api_bp.route('/ronda-tempo-real/iniciar', methods=['POST'])
@login_required
@csrf.exempt
def iniciar_ronda_tempo_real():
    """Inicia uma nova ronda em um condomínio."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        condominio_id = data.get('condominio_id')
        hora_entrada_str = data.get('hora_entrada')  # formato "HH:MM"
        observacoes = data.get('observacoes')
        
        if not condominio_id or not hora_entrada_str:
            return jsonify({
                'success': False,
                'error': 'condominio_id e hora_entrada são obrigatórios'
            }), 400
        
        # Converter string de hora para objeto time
        try:
            hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M').time()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Formato de hora inválido. Use HH:MM'
            }), 400
        
        service = RondaTempoRealService(current_user.id)
        ronda_data = service.iniciar_ronda(condominio_id, hora_entrada, observacoes)
        
        return jsonify({
            'success': True,
            'data': ronda_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Erro ao iniciar ronda: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/finalizar/<int:ronda_id>', methods=['POST'])
@login_required
@csrf.exempt
def finalizar_ronda_tempo_real(ronda_id):
    """Finaliza uma ronda em andamento."""
    try:
        data = request.get_json() or {}
        hora_saida_str = data.get('hora_saida')  # formato "HH:MM"
        observacoes = data.get('observacoes')
        
        if not hora_saida_str:
            return jsonify({
                'success': False,
                'error': 'hora_saida é obrigatória'
            }), 400
        
        # Converter string de hora para objeto time
        try:
            hora_saida = datetime.strptime(hora_saida_str, '%H:%M').time()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Formato de hora inválido. Use HH:MM'
            }), 400
        
        service = RondaTempoRealService(current_user.id)
        ronda_data = service.finalizar_ronda(ronda_id, hora_saida, observacoes)
        
        return jsonify({
            'success': True,
            'data': ronda_data
        })
        
    except ValueError as e:
        current_app.logger.error(f"Erro de validação ao finalizar ronda {ronda_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Erro ao finalizar ronda: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/em-andamento', methods=['GET'])
@login_required
def listar_rondas_em_andamento_tempo_real():
    """Lista todas as rondas em andamento do usuário."""
    try:
        service = RondaTempoRealService(current_user.id)
        rondas = service.listar_rondas_em_andamento()
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': r.id,
                    'condominio_id': r.condominio_id,
                    'condominio_nome': r.condominio.nome if r.condominio else f"Condomínio {r.condominio_id}",
                    'hora_entrada': r.hora_entrada_formatada,
                    'status': r.status,
                    'plantao': r.escala_plantao,
                    'turno': r.turno,
                    'data_plantao': r.data_plantao.strftime('%d/%m/%Y') if r.data_plantao else 'N/A',
                    'data_criacao': r.data_criacao.strftime('%d/%m/%Y %H:%M') if r.data_criacao else 'N/A'
                } for r in rondas if r is not None
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao listar rondas em andamento: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/relatorio', methods=['GET'])
@login_required
def gerar_relatorio_tempo_real():
    """Gera relatório formatado das rondas do plantão."""
    try:
        data_plantao_str = request.args.get('data_plantao')  # formato "YYYY-MM-DD"
        
        data_plantao = None
        if data_plantao_str:
            try:
                data_plantao = datetime.strptime(data_plantao_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de data inválido. Use YYYY-MM-DD'
                }), 400
        
        service = RondaTempoRealService(current_user.id)
        relatorios = service.gerar_relatorio_plantao(data_plantao)
        estatisticas = service.obter_estatisticas_plantao(data_plantao)
        
        return jsonify({
            'success': True,
            'data': {
                'relatorios': relatorios,
                'estatisticas': estatisticas,
                'data_plantao': data_plantao.strftime('%d/%m/%Y') if data_plantao else 'Hoje'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/cancelar/<int:ronda_id>', methods=['POST'])
@login_required
@csrf.exempt
def cancelar_ronda_tempo_real(ronda_id):
    """Cancela uma ronda em andamento."""
    try:
        service = RondaTempoRealService(current_user.id)
        sucesso = service.cancelar_ronda(ronda_id)
        
        if not sucesso:
            return jsonify({
                'success': False,
                'error': 'Não foi possível cancelar a ronda'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Ronda cancelada com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao cancelar ronda: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/estatisticas', methods=['GET'])
@login_required
def obter_estatisticas_tempo_real():
    """Retorna estatísticas do plantão atual."""
    try:
        data_plantao_str = request.args.get('data_plantao')  # formato "YYYY-MM-DD"
        
        data_plantao = None
        if data_plantao_str:
            try:
                data_plantao = datetime.strptime(data_plantao_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de data inválido. Use YYYY-MM-DD'
                }), 400
        
        service = RondaTempoRealService(current_user.id)
        estatisticas = service.obter_estatisticas_plantao(data_plantao)
        
        return jsonify({
            'success': True,
            'data': estatisticas
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@api_bp.route('/ronda-tempo-real/hora-atual', methods=['GET'])
@login_required
def obter_hora_atual_tempo_real():
    """Retorna a hora atual do servidor para sincronização."""
    try:
        agora = datetime.now()
        return jsonify({
            'success': True,
            'data': {
                'hora_atual': agora.strftime('%H:%M'),
                'data_atual': agora.strftime('%d/%m/%Y'),
                'timestamp': agora.isoformat()
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao obter hora atual: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500 


@api_bp.route('/ronda-tempo-real/condominios-com-ronda', methods=['GET'])
@login_required
def listar_condominios_com_ronda():
    service = RondaTempoRealService(current_user.id)
    em_andamento = service.condominios_com_ronda_em_andamento()
    realizadas = service.condominios_com_ronda_realizada_plantao()
    return jsonify({
        'success': True,
        'em_andamento': em_andamento,
        'realizadas': realizadas
    }) 


@api_bp.route('/ronda-tempo-real/rondas-condominio/<int:condominio_id>', methods=['GET'])
@login_required
def listar_rondas_do_condominio_plantao(condominio_id):
    service = RondaTempoRealService(current_user.id)
    info = service.listar_rondas_do_condominio_plantao(condominio_id)
    return jsonify({'success': True, **info}) 


@api_bp.route('/ronda-tempo-real/pendente-exportacao-anterior', methods=['GET'])
@login_required
def pendente_exportacao_anterior():
    service = RondaTempoRealService(current_user.id)
    info = service.plantao_anterior_pendente_exportacao()
    if info:
        return jsonify({'success': True, **info})
    else:
        return jsonify({'success': False}) 


@api_bp.route('/ronda-tempo-real/marcar-exportado-plantao-anterior', methods=['POST'])
@login_required
@csrf.exempt
def marcar_exportado_plantao_anterior():
    service = RondaTempoRealService(current_user.id)
    sucesso = service.marcar_plantao_anterior_como_exportado()
    if sucesso:
        return jsonify({'success': True, 'message': 'Plantão anterior marcado como exportado.'})
    else:
        return jsonify({'success': False, 'error': 'Nenhum plantão anterior pendente ou erro ao exportar.'}), 400 