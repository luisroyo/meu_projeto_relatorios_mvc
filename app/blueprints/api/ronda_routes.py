from flask import request, jsonify
from flask_cors import cross_origin
from app import csrf
from datetime import datetime, date
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.models.user import User
from app.services.ronda_routes_core.routes_service import RondaRoutesService
from app.services.ronda_routes_core.persistence_service import get_ronda_by_id, list_rondas, build_ronda_query
from app.services.ronda_routes_core.business_service import atribuir_supervisor
from app import db
from . import api_bp

@api_bp.route("/rondas/do-dia/<int:condominio_id>/<data>", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_rondas_do_dia(condominio_id, data):
    """Lista todas as rondas de um condomínio em uma data específica."""
    try:
        # Converter data
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar rondas
        query = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj
        ).options(
            db.joinedload(Ronda.condominio),
            db.joinedload(Ronda.supervisor)
        )
        
        rondas = query.order_by(Ronda.id.desc()).all()
        
        # Formatar resposta
        rondas_list = []
        for ronda in rondas:
            rondas_list.append({
                "id": ronda.id,
                "condominio_id": ronda.condominio_id,
                "condominio_nome": ronda.condominio.nome if ronda.condominio else "N/A",
                "data_plantao": ronda.data_plantao_ronda.isoformat(),
                "escala_plantao": ronda.escala_plantao_ronda,
                "log_bruto": ronda.log_bruto_rondas,
                "total_rondas": ronda.total_rondas,
                "duracao_total_minutos": ronda.duracao_total_rondas_minutos,
                "primeiro_evento_utc": ronda.primeiro_evento_log_dt.isoformat() if ronda.primeiro_evento_log_dt else None,
                "ultimo_evento_utc": ronda.ultimo_evento_log_dt.isoformat() if ronda.ultimo_evento_log_dt else None,
                "supervisor_id": ronda.supervisor_id,
                "supervisor_nome": ronda.supervisor.username if ronda.supervisor else None,
                "status": ronda.status_ronda,
                "data_criacao": ronda.data_hora_inicio.isoformat() if ronda.data_hora_inicio else None,
                "data_modificacao": ronda.data_hora_fim.isoformat() if ronda.data_hora_fim else None
            })
        
        return jsonify({
            "rondas": rondas_list,
            "total": len(rondas_list)
        })
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao listar rondas: {str(e)}"}), 500

@api_bp.route("/rondas/em-andamento/<int:condominio_id>", methods=["GET"])
@cross_origin()
@csrf.exempt
def verificar_ronda_em_andamento(condominio_id):
    """Verifica se existe uma ronda em andamento para o condomínio."""
    try:
        data_plantao = request.args.get("data_plantao")
        if not data_plantao:
            return jsonify({"sucesso": False, "message": "Data do plantão é obrigatória."}), 400

        # Converter data
        data_obj = datetime.strptime(data_plantao, "%Y-%m-%d").date()
        
        # Verificar ronda em andamento
        ronda_ativa = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj,
            status_ronda="em_andamento"
        ).first()
        
        if ronda_ativa:
            return jsonify({
                "em_andamento": True,
                "ronda": {
                    "id": ronda_ativa.id,
                    "inicio": ronda_ativa.data_hora_inicio.isoformat() if ronda_ativa.data_hora_inicio else None,
                    "data_plantao": ronda_ativa.data_plantao_ronda.isoformat(),
                    "escala_plantao": ronda_ativa.escala_plantao_ronda,
                    "turno": ronda_ativa.turno_ronda,
                    "observacoes": ronda_ativa.log_bruto_rondas,
                    "user_id": ronda_ativa.user_id,
                    "supervisor_id": ronda_ativa.supervisor_id
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
    """Inicia uma nova ronda."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campos obrigatórios
        condominio_id = data.get("condominio_id")
        data_plantao = data.get("data_plantao")
        escala_plantao = data.get("escala_plantao", "06h às 18h")
        supervisor_id = data.get("supervisor_id")
        user_id = data.get("user_id", 1)  # Default user

        if not condominio_id or not data_plantao:
            return jsonify({"sucesso": False, "message": "Condomínio e data são obrigatórios."}), 400

        # Converter data
        data_obj = datetime.strptime(data_plantao, "%Y-%m-%d").date()
        
        # Verificar se já existe ronda em andamento
        ronda_existente = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj,
            status_ronda="em_andamento"
        ).first()
        
        if ronda_existente:
            return jsonify({"sucesso": False, "message": "Já existe uma ronda em andamento para este condomínio e data."}), 400

        # Criar nova ronda
        nova_ronda = Ronda(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj,
            escala_plantao_ronda=escala_plantao,
            supervisor_id=supervisor_id,
            user_id=user_id,
            status_ronda="em_andamento",
            data_hora_inicio=datetime.now()
        )
        
        db.session.add(nova_ronda)
        db.session.commit()
        
        return jsonify({
            "sucesso": True,
            "message": "Ronda iniciada com sucesso!",
            "ronda_id": nova_ronda.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao iniciar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/finalizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def finalizar_ronda(ronda_id):
    """Finaliza uma ronda existente."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Buscar ronda
        ronda = get_ronda_by_id(ronda_id)
        if not ronda:
            return jsonify({"sucesso": False, "message": "Ronda não encontrada."}), 404

        # Atualizar dados
        if "log_bruto" in data:
            ronda.log_bruto_rondas = data["log_bruto"]
        
        if "observacoes" in data:
            ronda.observacoes = data["observacoes"]
        
        ronda.status_ronda = "finalizada"
        ronda.data_hora_fim = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            "sucesso": True,
            "message": "Ronda finalizada com sucesso!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao finalizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/atualizar/<int:ronda_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
@csrf.exempt
def atualizar_ronda(ronda_id):
    """Atualiza uma ronda existente."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Buscar ronda
        ronda = get_ronda_by_id(ronda_id)
        if not ronda:
            return jsonify({"sucesso": False, "message": "Ronda não encontrada."}), 404

        # Atualizar dados
        if "log_bruto" in data:
            ronda.log_bruto_rondas = data["log_bruto"]
        
        if "observacoes" in data:
            ronda.observacoes = data["observacoes"]
        
        db.session.commit()
        
        return jsonify({
            "sucesso": True,
            "message": "Ronda atualizada com sucesso!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao atualizar ronda: {str(e)}"}), 500

@api_bp.route("/rondas/gerar-relatorio/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def gerar_relatorio_ronda(condominio_id, data):
    """Gera relatório de ronda para um condomínio e data."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar ronda
        ronda = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj
        ).first()
        
        if not ronda:
            return jsonify({"sucesso": False, "message": "Ronda não encontrada."}), 404

        # Gerar relatório básico
        relatorio = f"""
RELATÓRIO DE RONDA - {ronda.condominio.nome if ronda.condominio else 'N/A'}
Data: {ronda.data_plantao_ronda.strftime('%d/%m/%Y')}
Escala: {ronda.escala_plantao_ronda}
Status: {ronda.status_ronda}

Log Bruto:
{ronda.log_bruto_rondas or 'Nenhum log registrado'}

Observações:
{ronda.observacoes or 'Nenhuma observação'}
        """.strip()
        
        return jsonify({
            "sucesso": True,
            "message": "Relatório gerado com sucesso!",
            "relatorio": relatorio
        })
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao gerar relatório: {str(e)}"}), 500

@api_bp.route("/rondas/enviar-whatsapp/<int:condominio_id>/<data>", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def enviar_ronda_whatsapp(condominio_id, data):
    """Envia relatório de ronda via WhatsApp."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Converter data
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        
        # Buscar ronda
        ronda = Ronda.query.filter_by(
            condominio_id=condominio_id,
            data_plantao_ronda=data_obj
        ).first()
        
        if not ronda:
            return jsonify({"sucesso": False, "message": "Ronda não encontrada."}), 404

        # Gerar relatório
        relatorio = f"""
🔄 RELATÓRIO DE RONDA - {ronda.condominio.nome if ronda.condominio else 'N/A'}
📅 Data: {ronda.data_plantao_ronda.strftime('%d/%m/%Y')}
⏰ Escala: {ronda.escala_plantao_ronda}
📊 Status: {ronda.status_ronda}

📝 Log:
{ronda.log_bruto_rondas or 'Nenhum log registrado'}

💬 Observações:
{ronda.observacoes or 'Nenhuma observação'}
        """.strip()
        
        # Aqui você pode integrar com o serviço de WhatsApp
        # Por enquanto, retornamos o relatório formatado
        
        return jsonify({
            "sucesso": True,
            "message": "Relatório preparado para envio via WhatsApp!",
            "relatorio": relatorio
        })
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao enviar via WhatsApp: {str(e)}"}), 500

@api_bp.route("/rondas/<int:ronda_id>", methods=["GET", "OPTIONS"])
@cross_origin()
@csrf.exempt
def detalhe_ronda(ronda_id):
    """Retorna detalhes de uma ronda específica."""
    if request.method == "OPTIONS":
        return '', 200
        
    try:
        # Buscar ronda
        ronda = get_ronda_by_id(ronda_id)
        if not ronda:
            return jsonify({"sucesso": False, "message": "Ronda não encontrada."}), 404

        # Formatar resposta
        ronda_data = {
            "id": ronda.id,
            "condominio_id": ronda.condominio_id,
            "condominio_nome": ronda.condominio.nome if ronda.condominio else "N/A",
            "data_plantao": ronda.data_plantao_ronda.isoformat(),
            "escala_plantao": ronda.escala_plantao_ronda,
            "log_bruto": ronda.log_bruto_rondas,
            "total_rondas": ronda.total_rondas,
            "duracao_total_minutos": ronda.duracao_total_rondas_minutos,
            "primeiro_evento_utc": ronda.primeiro_evento_log_dt.isoformat() if ronda.primeiro_evento_log_dt else None,
            "ultimo_evento_utc": ronda.ultimo_evento_log_dt.isoformat() if ronda.ultimo_evento_log_dt else None,
            "supervisor_id": ronda.supervisor_id,
            "supervisor_nome": ronda.supervisor.username if ronda.supervisor else None,
            "status": ronda.status_ronda,
            "data_criacao": ronda.data_hora_inicio.isoformat() if ronda.data_hora_inicio else None,
            "data_modificacao": ronda.data_hora_fim.isoformat() if ronda.data_hora_fim else None
        }
        
        return jsonify({
            "sucesso": True,
            "ronda": ronda_data
        })
        
    except Exception as e:
        return jsonify({"sucesso": False, "message": f"Erro ao buscar ronda: {str(e)}"}), 500 