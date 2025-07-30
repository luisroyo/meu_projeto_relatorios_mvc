from flask import request, jsonify
from flask_cors import cross_origin
from app import csrf
from datetime import datetime, time
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from app.models.user import User
from app.services.ronda_esporadica_service import RondaEsporadicaService
from app import db
from . import api_bp

@api_bp.route("/rondas-esporadicas/validar-horario", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def validar_horario_entrada():
    """Valida se o horário informado está próximo do horário atual."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Extrair horário do request
        hora_str = data.get("hora_entrada")
        if not hora_str:
            return jsonify({"sucesso": False, "message": "Hora de entrada é obrigatória."}), 400

        # Converter string para time
        try:
            hora_entrada = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            return jsonify({"sucesso": False, "message": "Formato de hora inválido. Use HH:MM."}), 400

        # Validar horário
        horario_valido, mensagem = RondaEsporadicaService.validar_horario_entrada(hora_entrada)
        
        return jsonify({
            "sucesso": True,
            "horario_valido": horario_valido,
            "mensagem": mensagem,
            "hora_atual": datetime.now().strftime("%H:%M"),
            "hora_informada": hora_str
        })

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao validar horário: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/em-andamento/<int:condominio_id>", methods=["GET"])
@cross_origin()
@csrf.exempt
def ronda_esporadica_em_andamento(condominio_id):
    """Verifica se existe uma ronda esporádica em andamento para o condomínio."""
    try:
        data_plantao = request.args.get("data_plantao")
        if not data_plantao:
            return jsonify({"sucesso": False, "message": "Data do plantão é obrigatória."}), 400

        # Converter data
        data_obj = datetime.strptime(data_plantao, "%Y-%m-%d").date()
        
        # Verificar ronda em andamento
        ronda_ativa = RondaEsporadicaService.verificar_ronda_em_andamento(condominio_id, data_obj)
        
        if ronda_ativa:
            return jsonify({
                "em_andamento": True,
                "ronda": {
                    "id": ronda_ativa.id,
                    "hora_entrada": ronda_ativa.hora_entrada_formatada,
                    "data_plantao": ronda_ativa.data_plantao.isoformat(),
                    "escala_plantao": ronda_ativa.escala_plantao,
                    "turno": ronda_ativa.turno,
                    "observacoes": ronda_ativa.observacoes,
                    "user_id": ronda_ativa.user_id,
                    "supervisor_id": ronda_ativa.supervisor_id
                }
            })
        else:
            return jsonify({"em_andamento": False, "ronda": None})
            
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao verificar ronda em andamento: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/iniciar", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def iniciar_ronda_esporadica():
    """Inicia uma nova ronda esporádica."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campos obrigatórios
        condominio_id = data.get("condominio_id")
        user_id = data.get("user_id")
        data_plantao = data.get("data_plantao")
        hora_entrada = data.get("hora_entrada")
        escala_plantao = data.get("escala_plantao")
        
        if not all([condominio_id, user_id, data_plantao, hora_entrada, escala_plantao]):
            return jsonify({"sucesso": False, "message": "Todos os campos obrigatórios devem ser fornecidos."}), 400

        # Converter data e hora
        try:
            data_obj = datetime.strptime(data_plantao, "%Y-%m-%d").date()
            hora_obj = datetime.strptime(hora_entrada, "%H:%M").time()
        except ValueError:
            return jsonify({"sucesso": False, "message": "Formato de data ou hora inválido."}), 400

        # Campos opcionais
        supervisor_id = data.get("supervisor_id")
        observacoes = data.get("observacoes")

        # Iniciar ronda
        sucesso, mensagem, ronda_id = RondaEsporadicaService.iniciar_ronda(
            condominio_id=condominio_id,
            user_id=user_id,
            data_plantao=data_obj,
            hora_entrada=hora_obj,
            escala_plantao=escala_plantao,
            supervisor_id=supervisor_id,
            observacoes=observacoes
        )

        if sucesso:
            return jsonify({
                "sucesso": True,
                "message": mensagem,
                "ronda_id": ronda_id
            }), 201
        else:
            return jsonify({"sucesso": False, "message": mensagem}), 400

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao iniciar ronda: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/finalizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def finalizar_ronda_esporadica(ronda_id):
    """Finaliza uma ronda esporádica em andamento."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campos obrigatórios
        hora_saida = data.get("hora_saida")
        if not hora_saida:
            return jsonify({"sucesso": False, "message": "Hora de saída é obrigatória."}), 400

        # Converter hora
        try:
            hora_obj = datetime.strptime(hora_saida, "%H:%M").time()
        except ValueError:
            return jsonify({"sucesso": False, "message": "Formato de hora inválido. Use HH:MM."}), 400

        # Campo opcional
        observacoes = data.get("observacoes")

        # Finalizar ronda
        sucesso, mensagem = RondaEsporadicaService.finalizar_ronda(
            ronda_id=ronda_id,
            hora_saida=hora_obj,
            observacoes=observacoes
        )

        if sucesso:
            return jsonify({
                "sucesso": True,
                "message": mensagem
            })
        else:
            return jsonify({"sucesso": False, "message": mensagem}), 400

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao finalizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/atualizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def atualizar_ronda_esporadica(ronda_id):
    """Atualiza uma ronda esporádica em andamento."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campo opcional
        observacoes = data.get("observacoes")

        # Atualizar ronda
        sucesso, mensagem = RondaEsporadicaService.atualizar_ronda(
            ronda_id=ronda_id,
            observacoes=observacoes
        )

        if sucesso:
            return jsonify({
                "sucesso": True,
                "message": mensagem
            })
        else:
            return jsonify({"sucesso": False, "message": mensagem}), 400

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao atualizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/do-dia/<int:condominio_id>/<data>", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_rondas_esporadicas_do_dia(condominio_id, data):
    """Lista todas as rondas esporádicas de um condomínio em uma data específica."""
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar rondas do dia
        rondas = RondaEsporadicaService.listar_rondas_do_dia(condominio_id, data_obj)
        
        resultado = []
        for ronda in rondas:
            resultado.append({
                "id": ronda.id,
                "condominio_id": ronda.condominio_id,
                "condominio_nome": ronda.condominio.nome if ronda.condominio else None,
                "user_id": ronda.user_id,
                "user_nome": ronda.user.username if ronda.user else None,
                "supervisor_id": ronda.supervisor_id,
                "supervisor_nome": ronda.supervisor.username if ronda.supervisor else None,
                "data_plantao": ronda.data_plantao.isoformat(),
                "escala_plantao": ronda.escala_plantao,
                "turno": ronda.turno,
                "hora_entrada": ronda.hora_entrada_formatada,
                "hora_saida": ronda.hora_saida_formatada,
                "duracao_formatada": ronda.duracao_formatada,
                "duracao_minutos": ronda.duracao_minutos,
                "status": ronda.status,
                "observacoes": ronda.observacoes,
                "data_criacao": ronda.data_criacao.isoformat() if ronda.data_criacao else None,
                "data_modificacao": ronda.data_modificacao.isoformat() if ronda.data_modificacao else None
            })
        
        return jsonify({"rondas": resultado})
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao listar rondas: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/consolidar-turno/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def consolidar_turno_rondas_esporadicas(condominio_id, data):
    """Consolida todas as rondas esporádicas de um turno para gerar relatório."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Consolidar turno
        resultado = RondaEsporadicaService.consolidar_turno(condominio_id, data_obj)
        
        if resultado["sucesso"]:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 404

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao consolidar turno: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/<int:ronda_id>", methods=["GET", "OPTIONS"])
@cross_origin()
@csrf.exempt
def detalhe_ronda_esporadica(ronda_id):
    """Retorna detalhes de uma ronda esporádica específica."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        ronda = RondaEsporadica.query.get_or_404(ronda_id)
        
        resultado = {
            "id": ronda.id,
            "condominio_id": ronda.condominio_id,
            "condominio_nome": ronda.condominio.nome if ronda.condominio else None,
            "user_id": ronda.user_id,
            "user_nome": ronda.user.username if ronda.user else None,
            "supervisor_id": ronda.supervisor_id,
            "supervisor_nome": ronda.supervisor.username if ronda.supervisor else None,
            "data_plantao": ronda.data_plantao.isoformat(),
            "escala_plantao": ronda.escala_plantao,
            "turno": ronda.turno,
            "hora_entrada": ronda.hora_entrada_formatada,
            "hora_saida": ronda.hora_saida_formatada,
            "duracao_formatada": ronda.duracao_formatada,
            "duracao_minutos": ronda.duracao_minutos,
            "status": ronda.status,
            "observacoes": ronda.observacoes,
            "log_bruto": ronda.log_bruto,
            "relatorio_processado": ronda.relatorio_processado,
            "data_criacao": ronda.data_criacao.isoformat() if ronda.data_criacao else None,
            "data_modificacao": ronda.data_modificacao.isoformat() if ronda.data_modificacao else None
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao buscar ronda: {str(e)}"}), 500 