# app/blueprints/ronda/routes.py

import logging
from datetime import date, datetime, timezone, timedelta
from collections.abc import Sequence
import os
import tempfile

import pytz
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for, session, abort)
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.decorators.admin_required import admin_required
from app.forms import TestarRondasForm
from app.models import Condominio, EscalaMensal, Ronda, User
from app.services.ronda_routes_core.routes_service import RondaRoutesService
from app.services.ronda_utils import get_system_user # Importa funções específicas
from app.services.excel_processor import ExcelProcessor
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

    # A função salvar_ronda em RondaRoutesService agora espera um objeto User
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
        supervisor_mais_ativo, condominios, supervisores, turnos, active_filter_params
    ) = RondaRoutesService.listar_rondas(page=page, filter_params=filter_params)
    return render_template(
        "ronda/list.html",
        title="Histórico de Rondas",
        rondas_pagination=rondas_pagination,
        filter_params=active_filter_params,
        condominios=condominios,
        supervisors=supervisores,
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
def processar_whatsapp_ajax():
    """Processa arquivo WhatsApp ou Excel via AJAX."""
    try:
        # Verifica se há arquivo, arquivo fixo ou arquivo do Google Drive
        arquivo_whatsapp = request.files.get('arquivo_whatsapp')
        arquivo_fixo_path = session.get('whatsapp_file_path')
        google_file_id = request.form.get('google_file_id')
        google_access_token = request.form.get('google_access_token')
        google_file_name = request.form.get('google_file_name', 'google_drive_file.txt')
        
        print(f"[DEBUG AJAX] arquivo_whatsapp: {arquivo_whatsapp}")
        print(f"[DEBUG AJAX] arquivo_fixo_path: {arquivo_fixo_path}")
        print(f"[DEBUG AJAX] google_file_id: {google_file_id}")
        
        if not arquivo_whatsapp and not arquivo_fixo_path and not google_file_id:
            return jsonify({'success': False, 'message': 'Nenhum arquivo fornecido'}), 400
        
        # Obtém parâmetros
        data_plantao = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        condominio_nome = request.form.get('condominio_nome', '').strip()
        condominio_id = request.form.get('condominio_id', '').strip()
        
        import tempfile
        import os
        
        if google_file_id and google_access_token:
            try:
                import requests
                headers = {"Authorization": f"Bearer {google_access_token}"}
                download_url = f"https://www.googleapis.com/drive/v3/files/{google_file_id}?alt=media"
                response = requests.get(download_url, headers=headers)
                if response.status_code != 200:
                    return jsonify({"success": False, "message": f"Erro ao baixar do Google Drive (Status {response.status_code}): {response.text}"}), 400
                
                temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_ronda')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, google_file_name)
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                session['whatsapp_file_path'] = temp_path
                session['whatsapp_file_name'] = google_file_name
                file_path = temp_path
                print(f"[DEBUG AJAX] Arquivo do Google Drive salvo: {file_path}")
            except Exception as e:
                logger.error(f"Erro ao baixar do Google Drive no AJAX: {e}", exc_info=True)
                return jsonify({"success": False, "message": f"Erro ao acessar Google Drive: {str(e)}"}), 500
        elif arquivo_whatsapp:
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
            if not file_path or not os.path.exists(file_path):
                session.pop('whatsapp_file_path', None)
                session.pop('whatsapp_file_name', None)
                return jsonify({'success': False, 'message': 'Arquivo fixo não encontrado'}), 400
        
        is_excel = file_path.lower().endswith('.xlsx')
        
        if not is_excel:
            return jsonify({'success': False, 'message': 'Apenas arquivos Excel (.xlsx) são suportados.'}), 400
            
        # Processamento de Excel (.xlsx)
        parsed_data = ExcelProcessor.parse_excel_file(file_path)
        if not parsed_data.get("success"):
            return jsonify({'success': False, 'message': parsed_data.get("message")}), 400
        
        # Tenta buscar o nome do condomínio da form ou de outro campo
        nome_para_buscar = condominio_nome
        if not nome_para_buscar or nome_para_buscar == "-- Selecione --" or nome_para_buscar == "Outro":
            nome_para_buscar = request.form.get('nome_condominio_outro', '').strip()
        
        log_formatado = ""
        msg = ""
        
        if nome_para_buscar:
            log_formatado = ExcelProcessor.generate_simulated_whatsapp_log(parsed_data, nome_para_buscar)
            
        condos_disponiveis = list(parsed_data.get("condominios", {}).keys())
        
        if nome_para_buscar and log_formatado:
            total_rondas = len(parsed_data["condominios"].get(nome_para_buscar, []))
            msg = f"Rondas do condomínio {nome_para_buscar} carregadas com sucesso! ({total_rondas} rondas encontradas)."
        else:
            if nome_para_buscar:
                msg = f"Condomínio '{nome_para_buscar}' não encontrado no Excel. Disponíveis na planilha: {', '.join(condos_disponiveis)}"
            else:
                msg = f"Arquivo Excel carregado! Selecione um condomínio para visualizar as rondas. Disponíveis na planilha: {', '.join(condos_disponiveis)}"
        
        # Tenta identificar o ID do supervisor pelo nome no cabeçalho do Excel (busca flexível)
        supervisor_id_db = "0"
        if parsed_data.get("supervisor"):
            sup_name = parsed_data["supervisor"].strip().lower()
            supervisors = User.query.filter_by(is_supervisor=True).all()
            for s in supervisors:
                username_lower = s.username.lower()
                if sup_name in username_lower or username_lower in sup_name:
                    supervisor_id_db = str(s.id)
                    break
        
        return jsonify({
            'success': True,
            'log_formatado': log_formatado,
            'data_plantao': parsed_data.get('data_iso'),
            'escala_plantao': parsed_data.get('escala_plantao'),
            'supervisor_id': supervisor_id_db,
            'total_mensagens': len(log_formatado.split('\n')) if log_formatado else 0,
            'message': msg
        })
            
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

@ronda_bp.route("/registrar-excel-lote-ajax", methods=["POST"])
@login_required
@admin_required
def registrar_excel_lote_ajax():
    """Registra todas as rondas de um arquivo Excel em sessão de uma só vez."""
    try:
        file_path = session.get('whatsapp_file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Nenhum arquivo Excel ativo na sessão.'}), 400
            
        if not file_path.lower().endswith('.xlsx'):
            return jsonify({'success': False, 'message': 'O arquivo ativo não é um Excel (.xlsx).'}), 400
            
        # Processamento
        parsed_data = ExcelProcessor.parse_excel_file(file_path)
        if not parsed_data.get("success"):
            return jsonify({'success': False, 'message': parsed_data.get("message")}), 400
            
        system_user = get_system_user()
        if not system_user:
            return jsonify({"success": False, "message": "Nenhum administrador encontrado para o sistema."}), 500
            
        # Supervisor (busca flexível)
        supervisor_id_db = None
        if parsed_data.get("supervisor"):
            sup_name = parsed_data["supervisor"].strip().lower()
            supervisors = User.query.filter_by(is_supervisor=True).all()
            for s in supervisors:
                username_lower = s.username.lower()
                if sup_name in username_lower or username_lower in sup_name:
                    supervisor_id_db = str(s.id)
                    break
                    
        total_rondas_salvas = 0
        messages = []
        
        for condo_name, rounds in parsed_data.get("condominios", {}).items():
            if not rounds:
                continue
                
            try:
                # Busca condomínio ou cria se não existir
                condominio = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condo_name)).first()
                if not condominio:
                    condominio = Condominio(nome=condo_name)
                    db.session.add(condominio)
                    db.session.flush()
                    logger.info(f"Condomínio '{condo_name}' criado automaticamente via AJAX lote.")
                    
                log_bruto = ExcelProcessor.generate_simulated_whatsapp_log(parsed_data, condo_name)
                if not log_bruto:
                    continue
                    
                ronda_data = {
                    "condominio_id": str(condominio.id),
                    "data_plantao": parsed_data.get("data_iso"),
                    "escala_plantao": parsed_data.get("escala_plantao"),
                    "log_bruto": log_bruto,
                    "ronda_id": None,
                    "supervisor_id": supervisor_id_db,
                }
                
                success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(ronda_data, system_user)
                
                if success:
                    total_rondas_salvas += 1
                    messages.append(f"✅ <strong>{condo_name}</strong>: Ronda registrada com sucesso! ID: {ronda_id}")
                else:
                    messages.append(f"❌ <strong>{condo_name}</strong>: Falha ao registrar. Detalhes: {message}")
            except Exception as e:
                error_msg = f"Erro ao processar condomínio {condo_name}: {str(e)}"
                messages.append(f"❌ <strong>{condo_name}</strong>: {error_msg}")
                logger.error(error_msg, exc_info=True)
                
        if total_rondas_salvas > 0:
            return jsonify({
                "success": True,
                "message": f"🎉 Importação concluída! <strong>{total_rondas_salvas}</strong> ronda(s) registrada(s) com sucesso.<br><br><strong>Histórico do Processamento:</strong><br>" + "<br>".join(messages)
            })
        else:
            return jsonify({
                "success": False,
                "message": "⚠️ Nenhuma ronda pôde ser registrada do arquivo Excel.<br><br><strong>Histórico do Processamento:</strong><br>" + "<br>".join(messages)
            })
            
    except Exception as e:
        logger.error(f"Erro ao registrar lote de Excel via AJAX: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@ronda_bp.route("/upload-process-ronda", methods=["GET", "POST"])
@login_required
@admin_required # Apenas administradores podem usar esta funcionalidade
def upload_process_ronda():
    """
    Rota para upload e processamento manual de arquivos de ronda (WhatsApp .txt ou Excel .xlsx).
    Permite selecionar mês e ano para filtragem (apenas para arquivos .txt).
    """
    if request.method == "GET":
        return render_template("ronda/upload_process_ronda.html", title="Upload e Processamento de Rondas")
    
    elif request.method == "POST":
        google_file_id = request.form.get('google_file_id')
        google_access_token = request.form.get('google_access_token')
        google_file_name = request.form.get('google_file_name', 'google_drive_file.txt')

        month = request.form.get('month', type=int)
        year = request.form.get('year', type=int)

        temp_filepath = None
        if google_file_id and google_access_token:
            try:
                import requests
                headers = {"Authorization": f"Bearer {google_access_token}"}
                download_url = f"https://www.googleapis.com/drive/v3/files/{google_file_id}?alt=media"
                response = requests.get(download_url, headers=headers)
                if response.status_code != 200:
                    return jsonify({"success": False, "message": f"Erro ao baixar do Google Drive (Status {response.status_code}): {response.text}"}), 400
                
                temp_dir = tempfile.gettempdir()
                temp_filepath = os.path.join(temp_dir, google_file_name)
                with open(temp_filepath, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Arquivo do Google Drive salvo temporariamente em: {temp_filepath}")
                filename_lower = google_file_name.lower()
                filename_to_use = google_file_name
            except Exception as e:
                logger.error(f"Erro ao baixar do Google Drive: {e}", exc_info=True)
                return jsonify({"success": False, "message": f"Erro ao acessar Google Drive: {str(e)}"}), 500
        else:
            if 'whatsapp_file' not in request.files:
                return jsonify({"success": False, "message": "Nenhum arquivo enviado."}), 400
            
            whatsapp_file = request.files['whatsapp_file']
            if whatsapp_file.filename == '':
                return jsonify({"success": False, "message": "Nenhum arquivo selecionado."}), 400
            
            filename_lower = whatsapp_file.filename.lower()
            if not filename_lower.endswith('.xlsx'):
                return jsonify({"success": False, "message": "Apenas arquivos .xlsx são permitidos."}), 400
            
            try:
                # Salvar o arquivo temporariamente para processamento
                temp_dir = tempfile.gettempdir()
                temp_filepath = os.path.join(temp_dir, whatsapp_file.filename)
                whatsapp_file.save(temp_filepath)
                logger.info(f"Arquivo temporário salvo em: {temp_filepath}")
            except Exception as e:
                logger.error(f"Erro ao salvar arquivo temporário: {e}", exc_info=True)
                return jsonify({"success": False, "message": "Erro ao salvar arquivo temporário no servidor."}), 500

        try:
            # Processamento de Excel (.xlsx)
            parsed_data = ExcelProcessor.parse_excel_file(temp_filepath)
            if not parsed_data.get("success"):
                os.remove(temp_filepath)
                return jsonify({"success": False, "message": parsed_data.get("message")}), 400
            
            system_user = get_system_user()
            if not system_user:
                os.remove(temp_filepath)
                return jsonify({"success": False, "message": "Nenhum administrador encontrado para o sistema."}), 500
            
            # Supervisor (busca flexível)
            supervisor_id_db = None
            if parsed_data.get("supervisor"):
                sup_name = parsed_data["supervisor"].strip().lower()
                supervisors = User.query.filter_by(is_supervisor=True).all()
                for s in supervisors:
                    username_lower = s.username.lower()
                    if sup_name in username_lower or username_lower in sup_name:
                        supervisor_id_db = str(s.id)
                        break
            
            total_rondas_salvas = 0
            messages = []
            
            for condo_name, rounds in parsed_data.get("condominios", {}).items():
                if not rounds:
                    continue
                
                try:
                    # Busca condomínio ou cria se não existir
                    condominio = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condo_name)).first()
                    if not condominio:
                        condominio = Condominio(nome=condo_name)
                        db.session.add(condominio)
                        db.session.flush()
                        logger.info(f"Condomínio '{condo_name}' criado automaticamente.")
                    
                    log_bruto = ExcelProcessor.generate_simulated_whatsapp_log(parsed_data, condo_name)
                    if not log_bruto:
                        continue
                    
                    ronda_data = {
                        "condominio_id": str(condominio.id),
                        "data_plantao": parsed_data.get("data_iso"),
                        "escala_plantao": parsed_data.get("escala_plantao"),
                        "log_bruto": log_bruto,
                        "ronda_id": None,
                        "supervisor_id": supervisor_id_db,
                    }
                    
                    success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(ronda_data, system_user)
                    
                    if success:
                        total_rondas_salvas += 1
                        messages.append(f"✅ Ronda para {condo_name} em {parsed_data.get('data_plantao')} registrada! ID: {ronda_id}")
                    else:
                        messages.append(f"❌ Falha ao registrar ronda para {condo_name}: {message}")
                        logger.error(f"Erro ao salvar ronda via upload Excel: {message}")
                except Exception as e:
                    error_msg = f"Erro ao processar condomínio {condo_name}: {str(e)}"
                    messages.append(f"❌ {error_msg}")
                    logger.error(error_msg, exc_info=True)
            
            os.remove(temp_filepath)
            
            if total_rondas_salvas > 0:
                return jsonify({
                    "success": True,
                    "message": f"🎉 Processamento do Excel concluído! {total_rondas_salvas} ronda(s) salva(s).<br><br><strong>Detalhes:</strong><br>" + "<br>".join(messages)
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "⚠️ Nenhuma ronda foi salva do arquivo Excel.<br><br><strong>Detalhes:</strong><br>" + "<br>".join(messages)
                }), 500

        except Exception as e:
            logger.error(f"Erro geral no upload e processamento de ronda: {e}", exc_info=True)
            if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({"success": False, "message": f"❌ Erro interno do servidor: {str(e)}"}), 500


@ronda_bp.route('/tempo-real')
@login_required
def ronda_tempo_real():
    """Interface para sistema de rondas em tempo real."""
    import os
    show_rondas_tempo_real = os.environ.get('FLASK_ENV') == 'development'
    if not show_rondas_tempo_real:
        return abort(404)
    # Carrega condomínios para o template, assim como no registro de ocorrências
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        logger.info(f"Carregando {len(condominios)} condomínios para o template")
        
        # Filtra condomínios válidos (com nome não nulo)
        condominios_validos = [c for c in condominios if c and c.nome is not None]
        logger.info(f"Condomínios válidos: {len(condominios_validos)}")
        
        for c in condominios_validos[:5]:  # Log apenas os primeiros 5
            logger.info(f"Condomínio: {c.id} - {c.nome}")
            
        return render_template('ronda_tempo_real.html', condominios=condominios_validos, show_rondas_tempo_real=show_rondas_tempo_real)
    except Exception as e:
        logger.error(f"Erro ao carregar condomínios: {e}", exc_info=True)
        return render_template('ronda_tempo_real.html', condominios=[], show_rondas_tempo_real=show_rondas_tempo_real)

