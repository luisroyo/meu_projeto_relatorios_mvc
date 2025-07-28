# app/blueprints/ronda/routes.py

import logging
from datetime import date, datetime, timezone, timedelta
from collections.abc import Sequence

import pytz  # Importe a biblioteca pytz
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.decorators.admin_required import admin_required
from app.forms import TestarRondasForm
from app.models import Condominio, EscalaMensal, Ronda, User
from app.services.ronda_routes_core.routes_service import RondaRoutesService
from app.services.whatsapp_processor import WhatsAppProcessor

logger = logging.getLogger(__name__)

ronda_bp = Blueprint(
    "ronda", __name__, template_folder="templates", url_prefix="/rondas"
)


@ronda_bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_ronda():
    ronda_id = request.args.get("ronda_id", type=int)
    form = TestarRondasForm()
    relatorio_processado_final = None
    title = "Editar Ronda" if ronda_id else "Registrar Nova Ronda Manual"

    try:
        condominios_db, supervisores_db = RondaRoutesService.preparar_dados_formulario()
        form.nome_condominio.choices = [
            ("", "-- Selecione --")
        ] + [(str(c.id), c.nome) for c in condominios_db] + [("Outro", "Outro")]
        form.supervisor_id.choices = [
            ("0", "-- Nenhum / Automático --")
        ] + [(str(s.id), s.username) for s in supervisores_db]
    except Exception as e:
        logger.error(
            f"Erro ao carregar dados para o formulário de ronda: {e}", exc_info=True
        )
        flash("Erro ao carregar dados. Tente novamente.", "danger")

    if ronda_id and request.method == "GET":
        ronda = Ronda.query.options(
            joinedload(Ronda.condominio), joinedload(Ronda.supervisor)
        ).get_or_404(ronda_id)

        if not (
            current_user.is_admin
            or (ronda.supervisor and current_user.id == ronda.supervisor.id)
        ):
            flash("Você não tem permissão para editar esta ronda.", "danger")
            return redirect(url_for("ronda.listar_rondas"))

        form.nome_condominio.data = str(ronda.condominio_id)
        form.data_plantao.data = ronda.data_plantao_ronda
        form.escala_plantao.data = ronda.escala_plantao
        form.supervisor_id.data = str(ronda.supervisor_id or "0")
        form.log_bruto_rondas.data = ronda.log_ronda_bruto
        relatorio_processado_final = ronda.relatorio_processado

    if form.validate_on_submit():
        # Processa arquivo WhatsApp se fornecido
        if form.arquivo_whatsapp.data:
            try:
                import tempfile
                import os
                
                # Salva arquivo temporariamente
                arquivo = form.arquivo_whatsapp.data
                temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_ronda')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, arquivo.filename)
                arquivo.save(temp_path)
                
                # Processa o arquivo WhatsApp
                processor = WhatsAppProcessor()
                data_inicio = form.data_plantao.data
                data_fim = form.data_plantao.data
                
                # Determina horário baseado na escala
                if form.escala_plantao.data == "06h às 18h":
                    data_inicio = data_inicio.replace(hour=6, minute=0, second=0, microsecond=0)
                    data_fim = data_inicio.replace(hour=17, minute=59, second=59)
                else:  # 18h às 06h
                    data_inicio = data_inicio.replace(hour=18, minute=0, second=0, microsecond=0)
                    data_fim = (data_inicio + timedelta(days=1)).replace(hour=5, minute=59, second=59)
                
                # Processa mensagens do período
                plantoes = processor.process_file(temp_path, data_inicio, data_fim)
                
                if plantoes:
                    # Formata o log para ronda
                    log_formatado = processor.format_for_ronda_log(plantoes[0])
                    form.log_bruto_rondas.data = log_formatado
                    flash(f"Log carregado automaticamente do WhatsApp! {len(plantoes[0].mensagens)} mensagens encontradas.", "success")
                else:
                    flash("Nenhuma mensagem encontrada no período selecionado.", "warning")
                
                # Remove arquivo temporário
                os.unlink(temp_path)
                
            except Exception as e:
                logger.error(f"Erro ao processar arquivo WhatsApp: {e}", exc_info=True)
                flash(f"Erro ao processar arquivo WhatsApp: {str(e)}", "danger")
        
        # Processa o registro da ronda
        relatorio_processado_final, condominio_obj, mensagem, status = RondaRoutesService.processar_registro_ronda(form, current_user)
        if status == "success":
            flash(mensagem, "info")
        else:
            flash(mensagem, "danger")

    elif request.method == "POST":
        for field, errors in form.errors.items():
            for error in errors:
                label = getattr(form, field).label.text
                flash(f"Erro no campo '{label}': {error}", "danger")

    ronda_data_to_save = {"ronda_id": ronda_id}
    print("[DEBUG] relatorio_processado_final:", repr(relatorio_processado_final))
    return render_template(
        "ronda/relatorio.html",
        title=title,
        form=form,
        relatorio_processado=relatorio_processado_final,
        ronda_data_to_save=ronda_data_to_save,
    )


@ronda_bp.route("/salvar", methods=["POST"])
@login_required
def salvar_ronda():
    if not (current_user.is_admin or current_user.is_supervisor):
        return jsonify({"success": False, "message": "Acesso negado."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados não fornecidos."}), 400

    success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(data, current_user)
    if success:
        return jsonify({"success": True, "message": message, "ronda_id": ronda_id}), status_code
    else:
        return jsonify({"success": False, "message": message}), status_code


@ronda_bp.route("/historico", methods=["GET"])
@login_required
def listar_rondas():
    page = request.args.get("page", 1, type=int)
    filter_params = {
        "condominio": request.args.get("condominio"),
        "supervisor": request.args.get("supervisor", type=int),
        "data_inicio": request.args.get("data_inicio"),
        "data_fim": request.args.get("data_fim"),
        "turno": request.args.get("turno"),
    }
    (
        rondas_pagination, total_rondas, soma_duracao, duracao_media, media_rondas_dia,
        supervisor_mais_ativo, condominios, supervisors, turnos, active_filter_params
    ) = RondaRoutesService.listar_rondas(page=page, filter_params=filter_params)
    return render_template(
        "ronda/list.html",
        title="Histórico de Rondas",
        rondas_pagination=rondas_pagination,
        filter_params=active_filter_params,
        condominios=condominios,
        supervisors=supervisors,
        turnos=turnos,
        total_rondas=total_rondas,
        duracao_media=duracao_media,
        media_rondas_dia=media_rondas_dia,
        supervisor_mais_ativo=supervisor_mais_ativo,
        **{f"selected_{k}": v for k, v in active_filter_params.items()},
    )


@ronda_bp.route("/detalhes/<int:ronda_id>")
@login_required
def detalhes_ronda(ronda_id):
    ronda = RondaRoutesService.detalhes_ronda(ronda_id)
    return render_template(
        "ronda/details.html", title=f"Detalhes da Ronda #{ronda.id}", ronda=ronda
    )


@ronda_bp.route("/excluir/<int:ronda_id>", methods=["POST"])
@login_required
@admin_required
def excluir_ronda(ronda_id):
    success, message, status_code = RondaRoutesService.excluir_ronda(ronda_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("ronda.listar_rondas"))


@ronda_bp.route("/processar-whatsapp", methods=["POST"])
@login_required
@admin_required
def processar_whatsapp():
    """Processa arquivo WhatsApp via AJAX."""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        # Valida extensão
        if not arquivo.filename.lower().endswith('.txt'):
            return jsonify({'success': False, 'message': 'Apenas arquivos .txt são permitidos'}), 400
        
        # Obtém parâmetros
        data_plantao = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        
        if not data_plantao or not escala_plantao:
            return jsonify({'success': False, 'message': 'Data e escala são obrigatórios'}), 400
        
        # Salva arquivo temporariamente
        import tempfile
        import os
        temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_ronda')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, arquivo.filename)
        arquivo.save(temp_path)
        
        try:
            # Processa o arquivo WhatsApp
            processor = WhatsAppProcessor()
            
            # Converte data
            from datetime import datetime
            data_dt = datetime.strptime(data_plantao, '%Y-%m-%d')
            
            # Determina horário baseado na escala
            if escala_plantao == "06h às 18h":
                # Plantão diurno: 06h às 18h (mesmo dia)
                data_inicio = data_dt.replace(hour=6, minute=0, second=0, microsecond=0)
                data_fim = data_dt.replace(hour=17, minute=59, second=59)
            else:  # 18h às 06h
                # Plantão noturno: 18h do dia selecionado até 06h do dia seguinte
                data_inicio = data_dt.replace(hour=18, minute=0, second=0, microsecond=0)
                data_fim = (data_dt + timedelta(days=1)).replace(hour=5, minute=59, second=59)
            
            # Processa mensagens do período
            plantoes = processor.process_file(temp_path, data_inicio, data_fim)
            
            if plantoes and plantoes[0].mensagens:
                # Formata o log para ronda
                log_formatado = processor.format_for_ronda_log(plantoes[0])
                total_mensagens = len(plantoes[0].mensagens)
                
                return jsonify({
                    'success': True,
                    'log': log_formatado,
                    'total_mensagens': total_mensagens,
                    'message': f'Log carregado com sucesso! {total_mensagens} mensagens encontradas.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Nenhuma mensagem encontrada no período selecionado.'
                }), 404
                
        finally:
            # Remove arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Erro ao processar arquivo WhatsApp: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'}), 500

