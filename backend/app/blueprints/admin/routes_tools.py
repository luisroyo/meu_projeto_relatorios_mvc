# app/blueprints/admin/routes_tools.py
import logging
from datetime import datetime

from flask import (flash, g, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required

from app.decorators.admin_required import admin_required
from app.forms import FormatEmailReportForm
from app.models import User
from app.services.escala_service import get_escala_mensal, salvar_escala_mensal
from app.services.justificativa_service import JustificativaAtestadoService
from app.services.justificativa_troca_plantao_service import \
    JustificativaTrocaPlantaoService

from . import admin_bp

logger = logging.getLogger(__name__)


# ... (funções auxiliares _get_justificativa... permanecem iguais) ...
def _get_justificativa_atestado_service():
    if "justificativa_atestado_service" not in g:
        g.justificativa_atestado_service = JustificativaAtestadoService()
    return g.justificativa_atestado_service


def _get_justificativa_troca_plantao_service():
    if "justificativa_troca_plantao_service" not in g:
        g.justificativa_troca_plantao_service = JustificativaTrocaPlantaoService()
    return g.justificativa_troca_plantao_service


@admin_bp.route("/escalas", methods=["GET", "POST"])
@login_required
@admin_required
def gerenciar_escalas():
    try:
        ano_selecionado = request.args.get("ano", default=datetime.now().year, type=int)
        mes_selecionado = request.args.get(
            "mes", default=datetime.now().month, type=int
        )
    except (ValueError, TypeError):
        ano_selecionado = datetime.now().year
        mes_selecionado = datetime.now().month

    # Usando lista de strings para os turnos
    turnos_definidos = ["Noturno Par", "Noturno Impar", "Diurno Par", "Diurno Impar"]

    if request.method == "POST":
        # ... (lógica do POST permanece a mesma) ...
        ano_form = request.form.get("ano", type=int)
        mes_form = request.form.get("mes", type=int)

        sucesso, mensagem = salvar_escala_mensal(ano_form, mes_form, request.form)

        if sucesso:
            flash(mensagem, "success")
        else:
            logger.error(f"Erro ao atualizar escala de supervisores: {mensagem}")
            flash(mensagem, "danger")

        return redirect(url_for("admin.gerenciar_escalas", ano=ano_form, mes=mes_form))

    # ---- Lógica para o método GET ----
    escalas_atuais = get_escala_mensal(ano_selecionado, mes_selecionado)
    supervisores = (
        User.query.filter_by(is_supervisor=True, is_approved=True)
        .order_by(User.username)
        .all()
    )
    anos_disponiveis = range(datetime.now().year - 2, datetime.now().year + 3)
    meses_disponiveis = [
        (1, "Janeiro"),
        (2, "Fevereiro"),
        (3, "Março"),
        (4, "Abril"),
        (5, "Maio"),
        (6, "Junho"),
        (7, "Julho"),
        (8, "Agosto"),
        (9, "Setembro"),
        (10, "Outubro"),
        (11, "Novembro"),
        (12, "Dezembro"),
    ]

    return render_template(
        "admin/gerenciar_escalas.html",
        title="Gerenciar Escalas de Supervisores",
        turnos=turnos_definidos,
        supervisores=supervisores,
        escalas_atuais=escalas_atuais,
        anos=anos_disponiveis,
        meses=meses_disponiveis,
        ano_selecionado=ano_selecionado,
        mes_selecionado=mes_selecionado,
    )


@admin_bp.route("/ferramentas/api/processar-justificativa", methods=["POST"])
@login_required
@admin_required
def api_processar_justificativa():
    payload = request.get_json()
    if not payload:
        return jsonify({"erro": "Dados não fornecidos."}), 400

    tipo_justificativa = payload.get("tipo_justificativa")
    dados_variaveis = payload.get("dados_variaveis")

    if not tipo_justificativa or not isinstance(dados_variaveis, dict):
        return jsonify({"erro": "Dados inválidos."}), 400

    logger.info(
        f"API Processar Justificativa: Tipo='{tipo_justificativa}' por '{current_user.username}'."
    )
    try:
        # Usando string diretamente para o tipo de justificativa
        if tipo_justificativa == "atestado":
            service = _get_justificativa_atestado_service()
            texto_gerado = service.gerar_justificativa(dados_variaveis)
        elif tipo_justificativa == "troca_plantao":
            service = _get_justificativa_troca_plantao_service()
            texto_gerado = service.gerar_justificativa_troca(dados_variaveis)
        else:
            return (
                jsonify(
                    {
                        "erro": f"Tipo de justificativa desconhecido: {tipo_justificativa}"
                    }
                ),
                400,
            )
        return jsonify({"justificativa_gerada": texto_gerado})
    except Exception as e:
        ## [MELHORIA] Tratamento de erro aprimorado.
        # Loga o erro completo para a equipe de desenvolvimento.
        logger.error(
            f"API Processar Justificativa: Erro inesperado: {e}", exc_info=True
        )
        # Retorna uma mensagem genérica e segura para o cliente.
        return (
            jsonify({"erro": "Ocorreu um erro interno ao processar a solicitação."}),
            500,
        )


# ... (O restante do arquivo, como admin_tools, format_email_report_tool, etc., permanece o mesmo) ...
@admin_bp.route("/ferramentas", methods=["GET"])
@login_required
@admin_required
def admin_tools():
    logger.info(f"Admin '{current_user.username}' acessou o menu de ferramentas.")
    return render_template(
        "admin/ferramentas.html", title="Ferramentas Administrativas"
    )


@admin_bp.route("/ferramentas/formatar-email", methods=["GET", "POST"])
@login_required
@admin_required
def format_email_report_tool():
    form = FormatEmailReportForm()
    formatted_report = None
    if form.validate_on_submit():
        raw_report = form.raw_report.data
        include_greeting = form.include_greeting.data
        custom_greeting = (form.custom_greeting.data or '').strip()
        include_closing = form.include_closing.data
        custom_closing = (form.custom_closing.data or '').strip()
        parts = []
        if custom_greeting:
            parts.append(custom_greeting)
        elif include_greeting:
            parts.append("Prezados(as),")
        if parts:
            parts.append("")
        parts.append(raw_report)
        if raw_report.strip() and (custom_closing or include_closing):
            parts.append("")
        if custom_closing:
            parts.append(custom_closing)
        elif include_closing:
            parts.append("Atenciosamente,\nEquipe Administrativa")
        formatted_report = "\n".join(parts)
        flash("Relatório formatado para e-mail com sucesso!", "success")
    return render_template(
        "admin/formatar_email.html",
        title="Formatar Relatório para E-mail",
        form=form,
        formatted_report=formatted_report,
    )


@admin_bp.route("/ferramentas/gerador-justificativas", methods=["GET"])
@login_required
@admin_required
def gerador_justificativas_tool():
    logger.info(f"Admin '{current_user.username}' acessou o Gerador de Justificativas.")
    return render_template(
        "admin/gerador_justificativas.html", title="Gerador de Justificativas iFractal"
    )
