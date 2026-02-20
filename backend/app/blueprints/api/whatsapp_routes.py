from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import WhatsAppMessage, Condominio, User
import logging
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ronda_logic.processor import processar_log_de_rondas
import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp_api', __name__, url_prefix='/api/whatsapp')

@whatsapp_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Recebe mensagens do serviço Node.js do WhatsApp em tempo real.
    """
    data = request.json
    
    # Expected payload:
    # {
    #   "message_id": "MSG123",
    #   "group_id": "123456789@g.us",
    #   "participant_id": "5511999999999@s.whatsapp.net",
    #   "push_name": "João Agente",
    #   "content": "Início da ronda VTR 01",
    #   "timestamp": 1678888888  # Unix timestamp
    # }
    
    if not data or 'message_id' not in data or 'group_id' not in data:
        return jsonify({"error": "Payload inválido"}), 400

    group_id = data.get('group_id')
    
    # Busca o condomínio vinculado a este grupo do WhatsApp
    condominio = Condominio.query.filter_by(whatsapp_group_id=group_id).first()
    
    if not condominio:
        logger.warning(f"Mensagem recebida de grupo não monitorado ou não vinculado: {group_id}")
        # Mesmo não tendo vínculo agora, o Node.js deve enviar apenas de grupos monitorados.
        # Por segurança, retornamos 200 pra ele não ficar tentando reenviar.
        return jsonify({"status": "ignored", "reason": "unlinked_group"}), 200

    timestamp = data.get('timestamp')
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
             dt = datetime.now() # Fallback
    except Exception:
        dt = datetime.now()

    try:
        new_msg = WhatsAppMessage(
            message_id=data.get('message_id'),
            condominio_id=condominio.id,
            remote_jid=group_id,
            participant_jid=data.get('participant_id', 'unknown'),
            push_name=data.get('push_name', ''),
            content=data.get('content', ''),
            timestamp=dt
        )
        db.session.add(new_msg)
        db.session.commit()
        logger.info(f"Mensagem do WhatsApp salva para o condomínio {condominio.nome}")
        return jsonify({"status": "success"}), 201
    except IntegrityError:
        db.session.rollback()
        # Ignora duplicatas silenciosamente (message_id repetido)
        return jsonify({"status": "ignored", "reason": "duplicate"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar mensagem do WhatsApp: {e}")
        return jsonify({"error": "Erro interno"}), 500

@whatsapp_bp.route('/sync', methods=['POST'])
def sync_historical():
    """
    Sincroniza mensagens históricas de um grupo específico através do Node.js.
    Normalmente chamado pelo Frontend ou internamente antes do parse.
    """
    import requests
    
    data = request.json
    condominio_id = data.get('condominio_id')
    # Pode opcionalmente receber date_start e count, mas por padrão puxa as últimas 100
    count = data.get('count', 100)
    
    if not condominio_id:
        return jsonify({"error": "condominio_id ausente"}), 400
        
    condominio = Condominio.query.get(condominio_id)
    if not condominio or not condominio.whatsapp_group_id:
        return jsonify({"error": "Condomínio não encontrado ou sem vínculo com WhatsApp"}), 404
        
    try:
        # Fazer requisição GET pro serviço Node.js pedindo as mensagens
        import os
        NODE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3001') + '/api/whatsapp/messages'
        response = requests.get(f"{NODE_URL}/{condominio.whatsapp_group_id}?count={count}")
        
        if response.status_code != 200:
            return jsonify({"error": f"Erro no serviço Node: {response.text}"}), response.status_code
            
        result = response.json()
        if not result.get('success'):
            return jsonify({"error": result.get('error', 'Falha desconhecida no Node')}), 500
            
        messages_data = result.get('messages', [])
        saved_count = 0
        
        for msg_data in messages_data:
            # Tentar processar timestamp
            timestamp = msg_data.get('timestamp')
            try:
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                     dt = datetime.now()
            except Exception:
                dt = datetime.now()

            # Evita duplicatas pelo message_id que é único na tabela
            exists = WhatsAppMessage.query.filter_by(message_id=msg_data.get('message_id')).first()
            if not exists:
                new_msg = WhatsAppMessage(
                    message_id=msg_data.get('message_id'),
                    condominio_id=condominio.id,
                    remote_jid=msg_data.get('group_id'),
                    participant_jid=msg_data.get('participant_id', 'unknown'),
                    push_name=msg_data.get('push_name', ''),
                    content=msg_data.get('content', ''),
                    timestamp=dt
                )
                db.session.add(new_msg)
                saved_count += 1
                
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": f"{saved_count} mensagens novas sincronizadas no histórico."
        }), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com Node.js no Sincronismo: {e}")
        return jsonify({"error": "Erro de conexão com o serviço WhatsApp"}), 503
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno no Sincronismo: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@whatsapp_bp.route('/process', methods=['POST'])
@jwt_required()
def processar_mensagens():
    """
    Busca mensagens do WhatsApp no banco para o período e condomínio selecionados,
    formata como um log de texto e passa para o analisador de rondas existente.
    """
    data = request.json
    condominio_id = data.get('condominio_id')
    date_start_str = data.get('date_start')
    date_end_str = data.get('date_end')
    
    if not all([condominio_id, date_start_str, date_end_str]):
        return jsonify({"error": "condominio_id, date_start e date_end são obrigatórios."}), 400
        
    try:
        # Formato esperado: YYYY-MM-DDTHH:MM:SS ou similar, adaptável
        try:
            date_start = datetime.fromisoformat(date_start_str)
            date_end = datetime.fromisoformat(date_end_str)
        except ValueError:
            # Tenta fallback format se isoformat falhar
            date_start = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M")
            date_end = datetime.strptime(date_end_str, "%Y-%m-%d %H:%M")
    except Exception as e:
        return jsonify({"error": f"Formato de data inválido: {e}"}), 400

    condominio = Condominio.query.get(condominio_id)
    if not condominio:
        return jsonify({"error": "Condomínio não encontrado"}), 404

    # Buscar mensagens no intervalo
    messages = WhatsAppMessage.query.filter(
        WhatsAppMessage.condominio_id == condominio_id,
        WhatsAppMessage.timestamp >= date_start,
        WhatsAppMessage.timestamp <= date_end
    ).order_by(WhatsAppMessage.timestamp.asc()).all()

    if not messages:
        return jsonify({
            "message": "Nenhuma mensagem encontrada para o período selecionado.",
            "rondas_completas": 0,
            "relatorio": ""
        }), 200

    # Formatar mensagens como Log de texto
    log_lines = []
    for msg in messages:
        # Formato compatível com o parser: [18:30, 01/01/2026] Nome: texto
        time_str = msg.timestamp.strftime('%H:%M')
        date_str = msg.timestamp.strftime('%d/%m/%Y')
        author = msg.push_name or msg.participant_jid
        log_lines.append(f"[{time_str}, {date_str}] {author}: {msg.content}")

    log_bruto = "\n".join(log_lines)
    
    try:
        # Passar para o processador real de rondas
        relatorio_final, rondas_completas_count, primeiro_dt, ultimo_dt, soma_minutos = processar_log_de_rondas(
            log_bruto_rondas_str=log_bruto,
            nome_condominio_str=condominio.nome,
            # Passamos string vazia para forçar o parser a tentar achar rondas completas
            data_plantao_manual_str="", 
            escala_plantao_str=""
        )
        
        return jsonify({
            "log_bruto": log_bruto, # Útil para exibir no painel de edição
            "relatorio_processado": relatorio_final,
            "estatisticas": {
                "rondas_completas": rondas_completas_count,
                "duracao_total_minutos": soma_minutos,
                "total_mensagens_usadas": len(messages),
                "primeiro_evento": primeiro_dt.isoformat() if primeiro_dt else None,
                "ultimo_evento": ultimo_dt.isoformat() if ultimo_dt else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar as mensagens extraídas: {e}")
        return jsonify({"error": f"Erro interno ao processar rondas: {str(e)}"}), 500


@whatsapp_bp.route('/condominios-mapping', methods=['GET'])
@jwt_required(optional=True) # Acessível para admins na tela antiga que usam session, ou JWT no app novo
def get_condominios_mapping():
    """Retorna os condomínios e seus grupos WhatsApp atuais"""
    condominios = Condominio.query.order_by(Condominio.nome).all()
    result = []
    for c in condominios:
        result.append({
            "id": c.id,
            "nome": c.nome,
            "whatsapp_group_id": c.whatsapp_group_id
        })
    return jsonify(result), 200


@whatsapp_bp.route('/condominio/<int:condominio_id>/map-group', methods=['POST'])
@jwt_required(optional=True)
def map_condominio_group(condominio_id):
    """Atualiza o grupo do WhatsApp de um Condomínio"""
    data = request.json
    group_id = data.get('whatsapp_group_id')
    
    condominio = Condominio.query.get(condominio_id)
    if not condominio:
        return jsonify({"error": "Condomínio não encontrado"}), 404
        
    condominio.whatsapp_group_id = group_id
    
    try:
        db.session.commit()
        return jsonify({"status": "success", "message": f"Grupo vinculado ao condomínio {condominio.nome}"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao mapear grupo de WhatsApp: {e}")
        return jsonify({"error": "Falha ao salvar no banco de dados"}), 500

