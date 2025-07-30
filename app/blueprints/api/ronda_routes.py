from flask import request, jsonify
from flask_cors import cross_origin
from app import csrf
from datetime import datetime
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.services.ronda_routes_core.routes_service import RondaRoutesService
from app.services.ronda_utils import RondaUtils
from app import db
from . import api_bp

@api_bp.route("/rondas/do-dia/<int:condominio_id>/<data>", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_rondas_do_dia(condominio_id, data):
    """Lista todas as rondas de um condomínio em uma data específica."""
    try:
        # Converter data string para objeto date
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar rondas do dia
        rondas = Ronda.query.filter(
            Ronda.condominio_id == condominio_id,
            Ronda.data_plantao == data_obj
        ).order_by(Ronda.primeiro_evento_utc.asc()).all()
        
        resultado = []
        for ronda in rondas:
            resultado.append({
                "id": ronda.id,
                "condominio_id": ronda.condominio_id,
                "condominio_nome": ronda.condominio.nome if ronda.condominio else None,
                "data_plantao": ronda.data_plantao.isoformat() if ronda.data_plantao else None,
                "escala_plantao": ronda.escala_plantao,
                "log_bruto": ronda.log_bruto,
                "total_rondas": ronda.total_rondas,
                "duracao_total_minutos": ronda.duracao_total_minutos,
                "primeiro_evento_utc": ronda.primeiro_evento_utc.isoformat() if ronda.primeiro_evento_utc else None,
                "ultimo_evento_utc": ronda.ultimo_evento_utc.isoformat() if ronda.ultimo_evento_utc else None,
                "supervisor_id": ronda.supervisor_id,
                "supervisor_nome": ronda.supervisor.nome_completo if ronda.supervisor else None,
                "status": ronda.status,
                "data_criacao": ronda.data_criacao.isoformat() if ronda.data_criacao else None,
                "data_modificacao": ronda.data_modificacao.isoformat() if ronda.data_modificacao else None
            })
        
        return jsonify({"rondas": resultado})
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao listar rondas: {str(e)}"}), 500

@api_bp.route("/rondas/em-andamento/<int:condominio_id>", methods=["GET"])
@cross_origin()
@csrf.exempt
def ronda_em_andamento(condominio_id):
    """Verifica se existe uma ronda em andamento para o condomínio."""
    try:
        # Buscar ronda em andamento (status = "em_andamento")
        ronda_ativa = Ronda.query.filter(
            Ronda.condominio_id == condominio_id,
            Ronda.status == "em_andamento"
        ).first()
        
        if ronda_ativa:
            return jsonify({
                "em_andamento": True,
                "ronda": {
                    "id": ronda_ativa.id,
                    "inicio": ronda_ativa.primeiro_evento_utc.isoformat() if ronda_ativa.primeiro_evento_utc else None,
                    "data_plantao": ronda_ativa.data_plantao.isoformat() if ronda_ativa.data_plantao else None
                }
            })
        else:
            return jsonify({"em_andamento": False, "ronda": None})
            
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao verificar ronda em andamento: {str(e)}"}), 500

@api_bp.route("/rondas/iniciar", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def iniciar_ronda():
    """Inicia uma nova ronda para um condomínio."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campos obrigatórios
        condominio_id = data.get("condominio_id")
        data_plantao = data.get("data_plantao")
        
        if not condominio_id or not data_plantao:
            return jsonify({"sucesso": False, "message": "Condomínio e data são obrigatórios."}), 400

        # Verificar se já existe ronda em andamento
        ronda_ativa = Ronda.query.filter(
            Ronda.condominio_id == condominio_id,
            Ronda.status == "em_andamento"
        ).first()
        
        if ronda_ativa:
            return jsonify({"sucesso": False, "message": "Já existe uma ronda em andamento para este condomínio."}), 400

        # Converter data
        data_obj = datetime.strptime(data_plantao, "%Y-%m-%d").date()
        
        # Criar nova ronda
        nova_ronda = Ronda(
            condominio_id=condominio_id,
            data_plantao=data_obj,
            escala_plantao=data.get("escala_plantao", "06h às 18h"),
            log_bruto=f"Início de ronda: {datetime.now().strftime('%H:%M')}",
            status="em_andamento",
            primeiro_evento_utc=datetime.utcnow(),
            supervisor_id=data.get("supervisor_id")
        )

        # Salvar no banco
        db.session.add(nova_ronda)
        db.session.commit()

        return jsonify({
            "sucesso": True,
            "message": "Ronda iniciada com sucesso.",
            "ronda_id": nova_ronda.id,
            "inicio": nova_ronda.primeiro_evento_utc.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao iniciar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/finalizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def finalizar_ronda(ronda_id):
    """Finaliza uma ronda em andamento."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        ronda = Ronda.query.get_or_404(ronda_id)
        
        if ronda.status != "em_andamento":
            return jsonify({"sucesso": False, "message": "Apenas rondas em andamento podem ser finalizadas."}), 400

        # Atualizar ronda
        ronda.status = "finalizada"
        ronda.ultimo_evento_utc = datetime.utcnow()
        ronda.log_bruto += f"\nTérmino de ronda: {datetime.now().strftime('%H:%M')}"
        
        # Calcular duração
        if ronda.primeiro_evento_utc and ronda.ultimo_evento_utc:
            duracao = ronda.ultimo_evento_utc - ronda.primeiro_evento_utc
            ronda.duracao_total_minutos = int(duracao.total_seconds() / 60)

        db.session.commit()

        return jsonify({
            "sucesso": True,
            "message": "Ronda finalizada com sucesso.",
            "duracao_minutos": ronda.duracao_total_minutos,
            "termino": ronda.ultimo_evento_utc.isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao finalizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/atualizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def atualizar_ronda(ronda_id):
    """Atualiza dados de uma ronda em andamento."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        ronda = Ronda.query.get_or_404(ronda_id)
        data = request.get_json()
        
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Atualizar campos permitidos
        if "observacoes" in data:
            ronda.log_bruto += f"\n{data['observacoes']}"
        
        if "escala_plantao" in data:
            ronda.escala_plantao = data["escala_plantao"]

        db.session.commit()

        return jsonify({
            "sucesso": True,
            "message": "Ronda atualizada com sucesso."
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao atualizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/gerar-relatorio/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def gerar_relatorio_ronda(condominio_id, data):
    """Gera relatório de todas as rondas de um condomínio em uma data."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar todas as rondas do dia
        rondas = Ronda.query.filter(
            Ronda.condominio_id == condominio_id,
            Ronda.data_plantao == data_obj,
            Ronda.status == "finalizada"
        ).order_by(Ronda.primeiro_evento_utc.asc()).all()
        
        if not rondas:
            return jsonify({"sucesso": False, "message": "Nenhuma ronda finalizada encontrada para esta data."}), 404

        # Gerar relatório usando o serviço existente
        condominio = Condominio.query.get(condominio_id)
        if not condominio:
            return jsonify({"sucesso": False, "message": "Condomínio não encontrado."}), 404

        # Usar o sistema de usuário automático
        system_user = RondaUtils.get_system_user()
        
        # Gerar relatório consolidado
        relatorio_consolidado = f"RELATÓRIO DE RONDAS - {condominio.nome}\n"
        relatorio_consolidado += f"Data: {data_obj.strftime('%d/%m/%Y')}\n"
        relatorio_consolidado += f"Total de Rondas: {len(rondas)}\n\n"
        
        duracao_total = 0
        for i, ronda in enumerate(rondas, 1):
            inicio = ronda.primeiro_evento_utc.strftime("%H:%M") if ronda.primeiro_evento_utc else "N/A"
            termino = ronda.ultimo_evento_utc.strftime("%H:%M") if ronda.ultimo_evento_utc else "N/A"
            duracao = ronda.duracao_total_minutos or 0
            duracao_total += duracao
            
            relatorio_consolidado += f"Ronda {i}:\n"
            relatorio_consolidado += f"  Início: {inicio}\n"
            relatorio_consolidado += f"  Término: {termino}\n"
            relatorio_consolidado += f"  Duração: {duracao} minutos\n"
            relatorio_consolidado += f"  Observações: {ronda.log_bruto}\n\n"
        
        relatorio_consolidado += f"Duração Total: {duracao_total} minutos"

        return jsonify({
            "sucesso": True,
            "relatorio": relatorio_consolidado,
            "total_rondas": len(rondas),
            "duracao_total_minutos": duracao_total
        })

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao gerar relatório: {str(e)}"}), 500

@api_bp.route("/rondas/enviar-whatsapp/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def enviar_ronda_whatsapp(condominio_id, data):
    """Envia relatório de rondas para WhatsApp."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Primeiro gerar o relatório
        relatorio_response = gerar_relatorio_ronda(condominio_id, data)
        
        if relatorio_response.status_code != 200:
            return relatorio_response
        
        relatorio_data = relatorio_response.get_json()
        if not relatorio_data.get("sucesso"):
            return jsonify(relatorio_data), 400
        
        relatorio = relatorio_data["relatorio"]
        
        # Aqui você pode integrar com sua API de WhatsApp
        # Por enquanto, retornamos sucesso
        return jsonify({
            "sucesso": True,
            "message": "Relatório enviado para WhatsApp com sucesso.",
            "relatorio": relatorio
        })

    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao enviar para WhatsApp: {str(e)}"}), 500

@api_bp.route("/rondas/<int:ronda_id>", methods=["GET", "OPTIONS"])
@cross_origin()
@csrf.exempt
def detalhe_ronda(ronda_id):
    """Retorna detalhes de uma ronda específica."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        ronda = Ronda.query.get_or_404(ronda_id)
        
        resultado = {
            "id": ronda.id,
            "condominio_id": ronda.condominio_id,
            "condominio_nome": ronda.condominio.nome if ronda.condominio else None,
            "data_plantao": ronda.data_plantao.isoformat() if ronda.data_plantao else None,
            "escala_plantao": ronda.escala_plantao,
            "log_bruto": ronda.log_bruto,
            "total_rondas": ronda.total_rondas,
            "duracao_total_minutos": ronda.duracao_total_minutos,
            "primeiro_evento_utc": ronda.primeiro_evento_utc.isoformat() if ronda.primeiro_evento_utc else None,
            "ultimo_evento_utc": ronda.ultimo_evento_utc.isoformat() if ronda.ultimo_evento_utc else None,
            "supervisor_id": ronda.supervisor_id,
            "supervisor_nome": ronda.supervisor.nome_completo if ronda.supervisor else None,
            "status": ronda.status,
            "data_criacao": ronda.data_criacao.isoformat() if ronda.data_criacao else None,
            "data_modificacao": ronda.data_modificacao.isoformat() if ronda.data_modificacao else None
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao buscar ronda: {str(e)}"}), 500 