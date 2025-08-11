# app/blueprints/main/routes.py
import logging
import os

from flask import Blueprint, flash, g, render_template, jsonify, request, redirect, url_for
from flask_login import current_user, login_required

from app import db, limiter
from app.forms import AnalisadorForm  # Verifique se este import está correto
from app.models import ProcessingHistory
from app.services.patrimonial_report_service import PatrimonialReportService
from app.services import ocorrencia_service

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

# Token para o endpoint de uptime
UPTIME_TOKEN = os.getenv("UPTIME_TOKEN", "defaulttoken")


def _get_patrimonial_service():
    if "patrimonial_service" not in g:
        g.patrimonial_service = PatrimonialReportService()
    return g.patrimonial_service


@main_bp.route("/", methods=["GET", "POST"])
@limiter.limit("200 per hour")
@login_required
def index():
    form = AnalisadorForm()
    relatorio_corrigido = None

    if form.validate_on_submit():
        relatorio_bruto = form.relatorio_bruto.data
        processing_success = False
        processing_error_message = None

        try:
            logger.info(f"Iniciando processamento para '{current_user.username}'.")
            patrimonial_service = _get_patrimonial_service()
            relatorio_corrigido = patrimonial_service.gerar_relatorio_seguranca(
                relatorio_bruto
            )
            flash("Relatório processado com sucesso!", "success")
            processing_success = True

        except Exception as e:
            logger.error(f"Erro ao processar relatório: {e}", exc_info=True)
            processing_error_message = f"Falha no serviço de IA: {str(e)}"
            flash(f"Ocorreu um erro ao processar o relatório.", "danger")

        # Salva o histórico (mesma lógica de antes)
        try:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type="patrimonial_report",
                success=processing_success,
                error_message=processing_error_message,
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e_history:
            db.session.rollback()
            logger.error(
                f"CRÍTICO: Falha ao salvar histórico: {e_history}", exc_info=True
            )
            flash("Erro grave ao registrar a operação.", "danger")

        # Ao final do POST, re-renderiza a página com o formulário e o resultado
        return render_template(
            "index.html",
            title="Resultado da Análise",
            form=form,
            relatorio_corrigido=relatorio_corrigido,
        )

    # Para requisições GET, renderiza a página com o formulário vazio
    # --- PONTO DA CORREÇÃO ---
    # A variável 'form' agora é passada também no GET inicial.
    
    # Verificar ocorrências pendentes para alerta
    ocorrencias_pendentes_count = ocorrencia_service.contar_ocorrencias_pendentes()
    
    return render_template(
        "index.html",
        title="Analisador de Relatórios IA",
        form=form,
        relatorio_corrigido=relatorio_corrigido,
        ocorrencias_pendentes_count=ocorrencias_pendentes_count,
    )


@main_bp.route("/uptime")
def uptime():
    """Endpoint de monitoramento para UptimeRobot e ferramentas similares."""
    token = request.args.get('token')
    
    if not token or token != UPTIME_TOKEN:
        return jsonify({"error": "unauthorized"}), 403
    
    return jsonify({"status": "ok"}), 200


@main_bp.route("/processar_relatorio", methods=["POST"])
@login_required
def processar_relatorio_redirect():
    """
    Rota para processar relatórios diretamente, mantendo compatibilidade com o frontend.
    Usa a autenticação da sessão Flask-Login em vez de JWT.
    """
    from app.utils.classificador import classificar_ocorrencia
    from app.services.patrimonial_report_service import PatrimonialReportService
    
    try:
        # Obter dados do formulário
        data = request.get_json()
        if not data or not data.get('relatorio_bruto'):
            return jsonify({'error': 'Relatório bruto é obrigatório'}), 400
        
        relatorio_bruto = data['relatorio_bruto']
        
        # Classificar ocorrência
        classificacao = classificar_ocorrencia(relatorio_bruto)
        
        # Processar relatório patrimonial
        patrimonial_service = PatrimonialReportService()
        relatorio_processado = patrimonial_service.gerar_relatorio_seguranca(relatorio_bruto)
        
        # Salvar histórico
        history = ProcessingHistory(
            user_id=current_user.id,
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
                user_id=current_user.id,
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
