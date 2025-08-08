from flask import request, jsonify
from flask_cors import cross_origin
from app import csrf
from datetime import datetime, date
from app.services.ronda_esporadica_consolidacao_service import RondaEsporadicaConsolidacaoService
from . import api_bp

@api_bp.route("/rondas-esporadicas/consolidar-e-enviar/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def consolidar_e_enviar_whatsapp(condominio_id, data):
    """Consolida rondas esporádicas e envia via WhatsApp."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Consolidar e enviar
        resultado = RondaEsporadicaConsolidacaoService.consolidar_e_enviar_whatsapp(condominio_id, data_obj)
        
        if resultado["sucesso"]:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 404

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro na consolidação: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/marcar-processadas/<int:condominio_id>/<data>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def marcar_rondas_processadas(condominio_id, data):
    """Marca rondas esporádicas como processadas após consolidação."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Marcar como processadas
        sucesso = RondaEsporadicaConsolidacaoService.marcar_rondas_como_processadas(condominio_id, data_obj)
        
        if sucesso:
            return jsonify({
                "sucesso": True,
                "message": "Rondas marcadas como processadas com sucesso"
            })
        else:
            return jsonify({
                "sucesso": False,
                "message": "Erro ao marcar rondas como processadas"
            }), 500

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/estatisticas/<int:condominio_id>", methods=["GET"])
@cross_origin()
@csrf.exempt
def obter_estatisticas_consolidacao(condominio_id):
    """Obtém estatísticas de consolidação para um período."""
    try:
        # Parâmetros de data
        data_inicio_str = request.args.get("data_inicio")
        data_fim_str = request.args.get("data_fim")
        
        if not data_inicio_str or not data_fim_str:
            return jsonify({"sucesso": False, "message": "Data início e fim são obrigatórias"}), 400

        # Converter datas
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"sucesso": False, "message": "Formato de data inválido. Use YYYY-MM-DD"}), 400

        # Obter estatísticas
        resultado = RondaEsporadicaConsolidacaoService.obter_estatisticas_consolidacao(
            condominio_id, data_inicio, data_fim
        )
        
        if resultado["sucesso"]:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 404

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao obter estatísticas: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/processo-completo/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def processo_completo_consolidacao(condominio_id, data):
    """Executa o processo completo: consolidar, enviar WhatsApp e marcar como processadas."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # 1. Consolidar e enviar WhatsApp
        resultado_consolidacao = RondaEsporadicaConsolidacaoService.consolidar_e_enviar_whatsapp(condominio_id, data_obj)
        
        if not resultado_consolidacao["sucesso"]:
            return jsonify(resultado_consolidacao), 404

        # 2. Marcar como processadas (se WhatsApp foi enviado com sucesso)
        rondas_processadas = False
        if resultado_consolidacao["whatsapp_enviado"]:
            rondas_processadas = RondaEsporadicaConsolidacaoService.marcar_rondas_como_processadas(condominio_id, data_obj)

        return jsonify({
            "sucesso": True,
            "message": "Processo completo executado com sucesso",
            "consolidacao": resultado_consolidacao,
            "rondas_processadas": rondas_processadas,
            "resumo": {
                "total_rondas": resultado_consolidacao["total_rondas"],
                "duracao_total_minutos": resultado_consolidacao["duracao_total_minutos"],
                "whatsapp_enviado": resultado_consolidacao["whatsapp_enviado"],
                "ronda_principal_id": resultado_consolidacao["ronda_principal_id"],
                "rondas_marcadas_processadas": rondas_processadas
            }
        })

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro no processo completo: {str(e)}"}), 500

@api_bp.route("/rondas-esporadicas/status-consolidacao/<int:condominio_id>/<data>", methods=["GET"])
@cross_origin()
@csrf.exempt
def status_consolidacao(condominio_id, data):
    """Verifica o status de consolidação de um dia específico."""
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        from app.models.ronda_esporadica import RondaEsporadica
        from app.models.ronda import Ronda
        
        # Buscar rondas esporádicas do dia
        rondas_esporadicas = RondaEsporadica.query.filter_by(
            condominio_id=condominio_id,
            data_plantao=data_obj
        ).all()
        
        # Buscar ronda principal criada
        ronda_principal = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj,
            tipo="esporadica"
        ).first()
        
        # Calcular estatísticas
        total_rondas = len(rondas_esporadicas)
        rondas_finalizadas = len([r for r in rondas_esporadicas if r.status == "finalizada"])
        rondas_processadas = len([r for r in rondas_esporadicas if r.status == "processada"])
        duracao_total = sum(r.duracao_minutos or 0 for r in rondas_esporadicas)
        
        return jsonify({
            "sucesso": True,
            "data": data,
            "condominio_id": condominio_id,
            "status": {
                "total_rondas_esporadicas": total_rondas,
                "rondas_finalizadas": rondas_finalizadas,
                "rondas_processadas": rondas_processadas,
                "duracao_total_minutos": duracao_total,
                "ronda_principal_criada": ronda_principal is not None,
                "ronda_principal_id": ronda_principal.id if ronda_principal else None,
                "pode_consolidar": total_rondas > 0 and rondas_finalizadas > 0,
                "ja_consolidado": ronda_principal is not None
            },
            "rondas": [
                {
                    "id": r.id,
                    "hora_entrada": r.hora_entrada_formatada,
                    "hora_saida": r.hora_saida_formatada,
                    "duracao_formatada": r.duracao_formatada,
                    "status": r.status,
                    "observacoes": r.observacoes
                } for r in rondas_esporadicas
            ]
        })

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao verificar status: {str(e)}"}), 500 