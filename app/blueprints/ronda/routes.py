# app/blueprints/ronda/routes.py

import logging
from datetime import date, datetime, timezone, timedelta
from collections.abc import Sequence

import pytz  # Importe a biblioteca pytz
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for, session)
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
    """Registra uma nova ronda."""
    title = "Registrar Ronda"
    ronda_id = request.args.get("ronda_id", type=int)
    form = TestarRondasForm()
    relatorio_processado_final = None

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

        title = "Editar Ronda"
        form.nome_condominio.data = str(ronda.condominio_id)
        form.data_plantao.data = ronda.data_plantao_ronda
        form.escala_plantao.data = ronda.escala_plantao
        form.supervisor_id.data = str(ronda.supervisor_id or "0")
        form.log_bruto_rondas.data = ronda.log_ronda_bruto
        relatorio_processado_final = ronda.relatorio_processado

    if form.validate_on_submit():
        # Processa arquivo WhatsApp se fornecido OU se há arquivo fixo na sessão
        arquivo_whatsapp = form.arquivo_whatsapp.data
        arquivo_fixo_path = session.get('whatsapp_file_path')
        
        print(f"[DEBUG] arquivo_whatsapp: {arquivo_whatsapp}")
        print(f"[DEBUG] arquivo_fixo_path: {arquivo_fixo_path}")
        
        if arquivo_whatsapp or arquivo_fixo_path:
            try:
                import tempfile
                import os
                
                if arquivo_whatsapp:
                    # Novo arquivo enviado - salva na sessão
                    temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_ronda')
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, arquivo_whatsapp.filename)
                    arquivo_whatsapp.save(temp_path)
                    
                    # Salva o caminho do arquivo na sessão para reutilização
                    session['whatsapp_file_path'] = temp_path
                    session['whatsapp_file_name'] = arquivo_whatsapp.filename
                    file_path = temp_path
                    print(f"[DEBUG] Novo arquivo salvo: {file_path}")
                else:
                    # Usa arquivo fixo da sessão
                    file_path = arquivo_fixo_path
                    print(f"[DEBUG] Usando arquivo fixo: {file_path}")
                    if not os.path.exists(file_path):
                        session.pop('whatsapp_file_path', None)
                        session.pop('whatsapp_file_name', None)
                        flash("Arquivo fixo não encontrado. Faça upload novamente.", "warning")
                        return render_template(
                            "ronda/relatorio.html",
                            title=title,
                            form=form,
                            relatorio_processado=relatorio_processado_final,
                            ronda_data_to_save=ronda_data_to_save,
                        )
                
                # Processa o arquivo WhatsApp
                processor = WhatsAppProcessor()
                data_inicio = form.data_plantao.data
                data_fim = form.data_plantao.data
                
                # Converte date para datetime
                from datetime import datetime
                data_inicio = datetime.combine(data_inicio, datetime.min.time())
                data_fim = datetime.combine(data_fim, datetime.min.time())
                
                print(f"[DEBUG] Data início: {data_inicio}")
                print(f"[DEBUG] Escala: {form.escala_plantao.data}")
                
                # Determina horário baseado na escala
                if form.escala_plantao.data == "06h às 18h":
                    data_inicio = data_inicio.replace(hour=6, minute=0, second=0)
                    data_fim = data_inicio.replace(hour=17, minute=59, second=59)
                else:  # 18h às 06h
                    data_inicio = data_inicio.replace(hour=18, minute=0, second=0)
                    data_fim = (data_inicio + timedelta(days=1)).replace(hour=5, minute=59, second=59)
                
                print(f"[DEBUG] Processando arquivo: {file_path}")
                print(f"[DEBUG] Período: {data_inicio} até {data_fim}")
                
                # Processa mensagens do período
                plantoes = processor.process_file(file_path, data_inicio, data_fim)
                
                print(f"[DEBUG] Plantões encontrados: {len(plantoes) if plantoes else 0}")
                
                if plantoes:
                    # Formata o log para ronda
                    log_formatado = processor.format_for_ronda_log(plantoes[0])
                    form.log_bruto_rondas.data = log_formatado
                    
                    print(f"[DEBUG] Log formatado: {len(log_formatado)} caracteres")
                    
                    if arquivo_whatsapp:
                        flash(f"Log carregado automaticamente do WhatsApp! {len(plantoes[0].mensagens)} mensagens encontradas.", "success")
                    else:
                        flash(f"Log carregado do arquivo fixo! {len(plantoes[0].mensagens)} mensagens encontradas.", "success")
                else:
                    flash("Nenhuma mensagem encontrada no período selecionado.", "warning")
                
            except Exception as e:
                logger.error(f"Erro ao processar arquivo WhatsApp: {e}", exc_info=True)
                flash(f"Erro ao processar arquivo WhatsApp: {str(e)}", "danger")
                print(f"[DEBUG] Erro ao processar: {e}")
        
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


@ronda_bp.route("/processar-whatsapp-ajax", methods=["POST"])
@login_required
@admin_required
def processar_whatsapp_ajax():
    """Processa arquivo WhatsApp via AJAX."""
    try:
        # Verifica se há arquivo ou arquivo fixo
        arquivo_whatsapp = request.files.get('arquivo_whatsapp')
        arquivo_fixo_path = session.get('whatsapp_file_path')
        
        print(f"[DEBUG AJAX] arquivo_whatsapp: {arquivo_whatsapp}")
        print(f"[DEBUG AJAX] arquivo_fixo_path: {arquivo_fixo_path}")
        
        if not arquivo_whatsapp and not arquivo_fixo_path:
            return jsonify({'success': False, 'message': 'Nenhum arquivo fornecido'}), 400
        
        # Obtém parâmetros
        data_plantao = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        
        if not data_plantao or not escala_plantao:
            return jsonify({'success': False, 'message': 'Data e escala são obrigatórios'}), 400
        
        import tempfile
        import os
        
        if arquivo_whatsapp:
            # Novo arquivo enviado - salva na sessão
            temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_ronda')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, arquivo_whatsapp.filename)
            arquivo_whatsapp.save(temp_path)
            
            # Salva o caminho do arquivo na sessão para reutilização
            session['whatsapp_file_path'] = temp_path
            session['whatsapp_file_name'] = arquivo_whatsapp.filename
            file_path = temp_path
            print(f"[DEBUG AJAX] Novo arquivo salvo: {file_path}")
        else:
            # Usa arquivo fixo da sessão
            file_path = arquivo_fixo_path
            print(f"[DEBUG AJAX] Usando arquivo fixo: {file_path}")
            if not os.path.exists(file_path):
                session.pop('whatsapp_file_path', None)
                session.pop('whatsapp_file_name', None)
                return jsonify({'success': False, 'message': 'Arquivo fixo não encontrado'}), 400
        
        # Processa o arquivo WhatsApp
        processor = WhatsAppProcessor()
        
        # Converte data
        from datetime import datetime
        data_dt = datetime.strptime(data_plantao, '%Y-%m-%d')
        
        print(f"[DEBUG AJAX] Data início: {data_dt}")
        print(f"[DEBUG AJAX] Escala: {escala_plantao}")
        
        # Determina horário baseado na escala
        if escala_plantao == "06h às 18h":
            data_inicio = data_dt.replace(hour=6, minute=0, second=0)
            data_fim = data_dt.replace(hour=17, minute=59, second=59)
        else:  # 18h às 06h
            data_inicio = data_dt.replace(hour=18, minute=0, second=0)
            data_fim = (data_dt + timedelta(days=1)).replace(hour=5, minute=59, second=59)
        
        print(f"[DEBUG AJAX] Processando arquivo: {file_path}")
        print(f"[DEBUG AJAX] Período: {data_inicio} até {data_fim}")
        
        # Processa mensagens do período
        plantoes = processor.process_file(file_path, data_inicio, data_fim)
        
        print(f"[DEBUG AJAX] Plantões encontrados: {len(plantoes) if plantoes else 0}")
        
        if plantoes:
            # Formata o log para ronda
            log_formatado = processor.format_for_ronda_log(plantoes[0])
            
            print(f"[DEBUG AJAX] Log formatado: {len(log_formatado)} caracteres")
            
            return jsonify({
                'success': True,
                'log_formatado': log_formatado,
                'total_mensagens': len(plantoes[0].mensagens),
                'message': f'Log carregado com sucesso! {len(plantoes[0].mensagens)} mensagens encontradas.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhuma mensagem encontrada no período selecionado.'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao processar arquivo WhatsApp via AJAX: {e}", exc_info=True)
        print(f"[DEBUG AJAX] Erro ao processar: {e}")
        return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'}), 500


@ronda_bp.route("/limpar-arquivo-fixo", methods=["POST"])
@login_required
@admin_required
def limpar_arquivo_fixo():
    """Remove o arquivo WhatsApp fixo da sessão."""
    try:
        # Remove arquivo temporário se existir
        if 'whatsapp_file_path' in session:
            import os
            file_path = session['whatsapp_file_path']
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        # Limpa a sessão
        session.pop('whatsapp_file_path', None)
        session.pop('whatsapp_file_name', None)
        
        return jsonify({"success": True, "message": "Arquivo WhatsApp fixo removido."})
        
    except Exception as e:
        logger.error(f"Erro ao limpar arquivo fixo: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Erro ao limpar arquivo: {str(e)}"}), 500


@ronda_bp.route("/status-arquivo-fixo")
@login_required
@admin_required
def status_arquivo_fixo():
    """Retorna o status do arquivo WhatsApp fixo."""
    try:
        if 'whatsapp_file_path' in session and session['whatsapp_file_path']:
            import os
            file_path = session['whatsapp_file_path']
            file_name = session.get('whatsapp_file_name', 'Arquivo WhatsApp')
            
            if os.path.exists(file_path):
                return jsonify({
                    "success": True,
                    "has_file": True,
                    "file_name": file_name,
                    "file_path": file_path
                })
            else:
                # Remove da sessão se não existir mais
                session.pop('whatsapp_file_path', None)
                session.pop('whatsapp_file_name', None)
                return jsonify({"success": True, "has_file": False})
        else:
            return jsonify({"success": True, "has_file": False})
            
    except Exception as e:
        logger.error(f"Erro ao verificar status do arquivo fixo: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Erro ao verificar status: {str(e)}"}), 500

