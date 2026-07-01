# app/blueprints/parada/routes.py

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
from app.forms import TestarParadasForm
from app.models import Condominio, EscalaMensal, Parada, User
from app.services.parada_routes_core.routes_service import ParadaRoutesService
from app.services.parada_utils import get_system_user
from app.services.excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)

parada_bp = Blueprint(
    "parada", __name__, template_folder="templates", url_prefix="/paradas"
)


@parada_bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_parada():
    """Registra uma nova parada."""
    title = "Registrar Parada"
    parada_id = request.args.get("parada_id", type=int)
    form = TestarParadasForm()
    relatorio_processado_final = None

    try:
        condominios_db, supervisores_db = ParadaRoutesService.preparar_dados_formulario()
        form.nome_condominio.choices = [
            ("", "-- Selecione --")
        ] + [(str(c.id), c.nome) for c in condominios_db] + [("Outro", "Outro")]
        form.supervisor_id.choices = [
            ("0", "-- Nenhum / Automático --")
        ] + [(str(s.id), s.username) for s in supervisores_db]
    except Exception as e:
        logger.error(
            f"Erro ao carregar dados para o formulário de parada: {e}", exc_info=True
        )
        flash("Erro ao carregar dados. Tente novamente.", "danger")

    if parada_id and request.method == "GET":
        parada = Parada.query.options(
            joinedload(Parada.condominio), joinedload(Parada.supervisor)
        ).get_or_404(parada_id)

        if not (
            current_user.is_admin
            or (parada.supervisor and current_user.id == parada.supervisor.id)
        ):
            flash("Você não tem permissão para editar esta parada.", "danger")
            return redirect(url_for("parada.listar_paradas"))

        title = "Editar Parada"
        form.nome_condominio.data = str(parada.condominio_id)
        form.data_plantao.data = parada.data_plantao_parada
        form.escala_plantao.data = parada.escala_plantao
        form.supervisor_id.data = str(parada.supervisor_id or "0")
        form.log_bruto_paradas.data = parada.log_parada_bruto
        relatorio_processado_final = parada.relatorio_processado

    if form.validate_on_submit():
        # Processar registro de parada
        relatorio, condominio_obj, mensagem, status = (
            ParadaRoutesService.processar_registro_parada(form, current_user)
        )
        flash(mensagem, status)
        if status == "success":
            relatorio_processado_final = relatorio

    # Verifica se há arquivo fixo para o template
    is_excel = False
    arquivo_fixo_name = session.get('parada_file_name')
    if session.get('parada_file_path'):
        is_excel = session.get('parada_file_path').lower().endswith('.xlsx')

    parada_data_to_save = {"parada_id": parada_id}

    return render_template(
        "parada/relatorio.html",
        form=form,
        title=title,
        parada_id=parada_id,
        relatorio_processado=relatorio_processado_final,
        is_excel=is_excel,
        parada_data_to_save=parada_data_to_save
    )


@parada_bp.route("/salvar", methods=["POST"])
@login_required
def salvar_parada():
    """Salva a parada processada no banco de dados."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Nenhum dado fornecido."}), 400

    success, message, status_code, parada_id = ParadaRoutesService.salvar_parada(data, current_user)
    return jsonify({"success": success, "message": message, "parada_id": parada_id}), status_code


@parada_bp.route("/historico", methods=["GET"])
@login_required
def listar_paradas():
    """Exibe o histórico de paradas com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    
    filter_params = {
        "condominio": request.args.get("condominio"),
        "supervisor": request.args.get("supervisor"),
        "turno": request.args.get("turno"),
        "data_inicio": request.args.get("data_inicio"),
        "data_fim": request.args.get("data_fim"),
    }

    try:
        (
            paradas_pagination,
            total_paradas,
            soma_duracao,
            duracao_media,
            _,
            supervisor_mais_ativo,
            condominios,
            supervisores,
            turnos,
            active_filter_params,
        ) = ParadaRoutesService.listar_paradas(page=page, filter_params=filter_params)
    except Exception as e:
        logger.error(f"Erro ao listar paradas: {e}", exc_info=True)
        flash("Erro ao carregar histórico de paradas. Tente novamente.", "danger")
        return redirect(url_for("main.index"))

    # Dias lançados por supervisor no período selecionado ou mês atual
    from app.models import Ronda
    import calendar
    from datetime import datetime
    
    str_data_inicio = active_filter_params.get("data_inicio")
    str_data_fim = active_filter_params.get("data_fim")

    hoje = datetime.now()
    inicio_periodo = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if str_data_inicio:
        inicio_periodo = datetime.strptime(str_data_inicio, "%Y-%m-%d")
        
    ultimo_dia = calendar.monthrange(inicio_periodo.year, inicio_periodo.month)[1]
    fim_periodo = inicio_periodo.replace(day=ultimo_dia, hour=23, minute=59, second=59)

    if str_data_fim:
        fim_periodo = datetime.strptime(str_data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    rondas_dias_raw = db.session.query(User.username, Ronda.data_plantao_ronda).join(
        Ronda, User.id == Ronda.supervisor_id
    ).filter(
        Ronda.data_hora_inicio >= inicio_periodo, Ronda.data_hora_inicio <= fim_periodo, Ronda.data_plantao_ronda.isnot(None)
    ).distinct().all()

    paradas_dias_raw = db.session.query(User.username, Parada.data_plantao_parada).join(
        Parada, User.id == Parada.supervisor_id
    ).filter(
        Parada.data_hora_inicio >= inicio_periodo, Parada.data_hora_inicio <= fim_periodo, Parada.data_plantao_parada.isnot(None)
    ).distinct().all()

    rondas_por_supervisor = {}
    for username, data_plantao in rondas_dias_raw:
        rondas_por_supervisor.setdefault(username, set()).add(data_plantao.day)
        
    paradas_por_supervisor = {}
    for username, data_plantao in paradas_dias_raw:
        paradas_por_supervisor.setdefault(username, set()).add(data_plantao.day)

    rondas_formatado = {u: ', '.join(str(d) for d in sorted(list(ds))) for u, ds in rondas_por_supervisor.items()}
    paradas_formatado = {u: ', '.join(str(d) for d in sorted(list(ds))) for u, ds in paradas_por_supervisor.items()}
    
    supervisores_db_ativos = User.query.filter_by(is_supervisor=True).all()
    todos_supervisores = sorted([s.username for s in supervisores_db_ativos])
    
    if str_data_inicio and str_data_fim and str_data_inicio != str_data_fim:
        nome_mes_atual = f"{inicio_periodo.strftime('%d/%m/%Y')} a {fim_periodo.strftime('%d/%m/%Y')}"
    else:
        meses_ptbr = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        nome_mes_atual = f"{meses_ptbr[inicio_periodo.month - 1]} de {inicio_periodo.year}"

    return render_template(
        "parada/list.html",
        paradas=paradas_pagination.items,
        pagination=paradas_pagination,
        total_paradas=total_paradas,
        soma_duracao=soma_duracao,
        duracao_media=duracao_media,
        supervisor_mais_ativo=supervisor_mais_ativo,
        condominios=condominios,
        supervisores=supervisores,
        turnos=turnos,
        active_filter_params=active_filter_params,
        todos_supervisores=todos_supervisores,
        rondas_formatado=rondas_formatado,
        paradas_formatado=paradas_formatado,
        nome_mes_atual=nome_mes_atual,
    )


@parada_bp.route("/detalhes/<int:parada_id>")
@login_required
def obter_detalhes_parada(parada_id):
    """Exibe detalhes de uma parada específica."""
    parada = Parada.query.options(
        joinedload(Parada.condominio), joinedload(Parada.supervisor)
    ).get_or_404(parada_id)
    return render_template("parada/details.html", parada=parada)


@parada_bp.route("/excluir/<int:parada_id>", methods=["POST"])
@login_required
@admin_required
def excluir_parada(parada_id):
    """Exclui uma parada."""
    success, message, status_code = ParadaRoutesService.excluir_parada(parada_id, current_user)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("parada.listar_paradas"))


@parada_bp.route("/processar-whatsapp-ajax", methods=["POST"])
@login_required
def processar_whatsapp_ajax():
    """Processa arquivo WhatsApp ou Excel via AJAX para Paradas."""
    try:
        arquivo_whatsapp = request.files.get('arquivo_whatsapp')
        arquivo_fixo_path = session.get('parada_file_path')
        google_file_id = request.form.get('google_file_id')
        google_access_token = request.form.get('google_access_token')
        google_file_name = request.form.get('google_file_name', 'google_drive_file.xlsx')
        
        print(f"[DEBUG PARADAS AJAX] arquivo_whatsapp: {arquivo_whatsapp}")
        print(f"[DEBUG PARADAS AJAX] arquivo_fixo_path: {arquivo_fixo_path}")
        print(f"[DEBUG PARADAS AJAX] google_file_id: {google_file_id}")
        
        if not arquivo_whatsapp and not arquivo_fixo_path and not google_file_id:
            return jsonify({'success': False, 'message': 'Nenhum arquivo fornecido'}), 400
        
        data_plantao = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        condominio_nome = request.form.get('condominio_nome', '').strip()
        
        if google_file_id and google_access_token:
            try:
                import requests
                headers = {"Authorization": f"Bearer {google_access_token}"}
                download_url = f"https://www.googleapis.com/drive/v3/files/{google_file_id}?alt=media"
                response = requests.get(download_url, headers=headers)
                if response.status_code != 200:
                    return jsonify({"success": False, "message": f"Erro ao baixar do Google Drive (Status {response.status_code}): {response.text}"}), 400
                
                temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_parada')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, google_file_name)
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                session['parada_file_path'] = temp_path
                session['parada_file_name'] = google_file_name
                file_path = temp_path
                print(f"[DEBUG PARADAS AJAX] Arquivo do Google Drive salvo: {file_path}")
            except Exception as e:
                logger.error(f"Erro ao baixar do Google Drive no AJAX de paradas: {e}", exc_info=True)
                return jsonify({"success": False, "message": f"Erro ao acessar Google Drive: {str(e)}"}), 500
        elif arquivo_whatsapp:
            temp_dir = os.path.join(tempfile.gettempdir(), 'whatsapp_parada')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, arquivo_whatsapp.filename)
            arquivo_whatsapp.save(temp_path)
            
            session['parada_file_path'] = temp_path
            session['parada_file_name'] = arquivo_whatsapp.filename
            file_path = temp_path
            print(f"[DEBUG PARADAS AJAX] Novo arquivo salvo: {file_path}")
        else:
            file_path = arquivo_fixo_path
            print(f"[DEBUG PARADAS AJAX] Usando arquivo fixo: {file_path}")
            if not os.path.exists(file_path):
                session.pop('parada_file_path', None)
                session.pop('parada_file_name', None)
                return jsonify({'success': False, 'message': 'Arquivo fixo não encontrado'}), 400
        
        is_excel = file_path.lower().endswith('.xlsx')
        if not is_excel:
            return jsonify({'success': False, 'message': 'Apenas arquivos Excel (.xlsx) são suportados.'}), 400
            
        parsed_data = ExcelProcessor.parse_excel_file_paradas(file_path)
        if not parsed_data.get("success"):
            return jsonify({'success': False, 'message': parsed_data.get("message")}), 400
        
        nome_para_buscar = condominio_nome
        if not nome_para_buscar or nome_para_buscar == "-- Selecione --" or nome_para_buscar == "Outro":
            nome_para_buscar = request.form.get('nome_condominio_outro', '').strip()
        
        log_formatado = ""
        msg = ""
        
        if nome_para_buscar:
            log_formatado = ExcelProcessor.generate_simulated_whatsapp_log_parada(parsed_data, nome_para_buscar)
            
        condos_disponiveis = list(parsed_data.get("condominios", {}).keys())
        
        if nome_para_buscar and log_formatado:
            total_paradas = len(parsed_data["condominios"].get(nome_para_buscar, []))
            msg = f"Paradas do condomínio {nome_para_buscar} carregadas com sucesso! ({total_paradas} paradas encontradas)."
        else:
            if nome_para_buscar:
                msg = f"Condomínio '{nome_para_buscar}' não encontrado na aba de Paradas do Excel. Disponíveis na planilha: {', '.join(condos_disponiveis)}"
            else:
                msg = f"Arquivo Excel carregado! Selecione um condomínio para visualizar as paradas. Disponíveis na planilha: {', '.join(condos_disponiveis)}"
        
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
        logger.error(f"Erro ao processar arquivo WhatsApp/Excel via AJAX para Paradas: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'}), 500


@parada_bp.route("/limpar-arquivo-fixo", methods=["POST"])
@login_required
@admin_required
def limpar_arquivo_fixo():
    """Remove o arquivo em cache da sessão."""
    session.pop('parada_file_path', None)
    session.pop('parada_file_name', None)
    return jsonify({'success': True, 'message': 'Cache limpo com sucesso!'})


@parada_bp.route("/status-arquivo-fixo")
@login_required
@admin_required
def status_arquivo_fixo():
    """Retorna o status do arquivo fixo em sessão."""
    try:
        file_path = session.get('parada_file_path')
        file_name = session.get('parada_file_name')
        
        if file_path and os.path.exists(file_path):
            return jsonify({
                "success": True,
                "file_name": file_name,
                "is_excel": file_path.lower().endswith('.xlsx')
            })
        else:
            session.pop('parada_file_path', None)
            session.pop('parada_file_name', None)
            return jsonify({"success": False, "message": "Nenhum arquivo ativo."})
    except Exception as e:
        logger.error(f"Erro ao verificar status do arquivo fixo: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Erro ao verificar status: {str(e)}"}), 500


@parada_bp.route("/registrar-excel-lote-ajax", methods=["POST"])
@login_required
@admin_required
def registrar_excel_lote_ajax():
    """Registra todas as paradas de um arquivo Excel em sessão de uma só vez."""
    try:
        file_path = session.get('parada_file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Nenhum arquivo Excel ativo na sessão.'}), 400
            
        if not file_path.lower().endswith('.xlsx'):
            return jsonify({'success': False, 'message': 'O arquivo ativo não é um Excel (.xlsx).'}), 400
            
        parsed_data = ExcelProcessor.parse_excel_file_paradas(file_path)
        if not parsed_data.get("success"):
            return jsonify({'success': False, 'message': parsed_data.get("message")}), 400
            
        system_user = get_system_user()
        if not system_user:
            return jsonify({"success": False, "message": "Nenhum administrador encontrado para o sistema."}), 500
            
        supervisor_id_db = None
        if parsed_data.get("supervisor"):
            sup_name = parsed_data["supervisor"].strip().lower()
            supervisors = User.query.filter_by(is_supervisor=True).all()
            for s in supervisors:
                username_lower = s.username.lower()
                if sup_name in username_lower or username_lower in sup_name:
                    supervisor_id_db = str(s.id)
                    break
                    
        total_paradas_salvas = 0
        messages = []
        
        for condo_name, rounds in parsed_data.get("condominios", {}).items():
            if not rounds:
                continue
                
            try:
                condominio = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condo_name)).first()
                if not condominio:
                    condominio = Condominio(nome=condo_name)
                    db.session.add(condominio)
                    db.session.flush()
                    logger.info(f"Condomínio '{condo_name}' criado automaticamente via AJAX lote paradas.")
                    
                log_bruto = ExcelProcessor.generate_simulated_whatsapp_log_parada(parsed_data, condo_name)
                if not log_bruto:
                    continue
                    
                parada_data = {
                    "condominio_id": str(condominio.id),
                    "data_plantao": parsed_data.get("data_iso"),
                    "escala_plantao": parsed_data.get("escala_plantao"),
                    "log_bruto": log_bruto,
                    "parada_id": None,
                    "supervisor_id": supervisor_id_db,
                }
                
                success, message, status_code, parada_id = ParadaRoutesService.salvar_parada(parada_data, system_user)
                
                if success:
                    total_paradas_salvas += 1
                    messages.append(f"✅ <strong>{condo_name}</strong>: Parada registrada com sucesso! ID: {parada_id}")
                else:
                    messages.append(f"❌ <strong>{condo_name}</strong>: Falha ao registrar. Detalhes: {message}")
            except Exception as e:
                error_msg = f"Erro ao processar condomínio {condo_name}: {str(e)}"
                messages.append(f"❌ <strong>{condo_name}</strong>: {error_msg}")
                logger.error(error_msg, exc_info=True)
                
        if total_paradas_salvas > 0:
            return jsonify({
                "success": True,
                "message": f"🎉 Importação concluída! <strong>{total_paradas_salvas}</strong> parada(s) registrada(s) com sucesso.<br><br><strong>Histórico do Processamento:</strong><br>" + "<br>".join(messages)
            })
        else:
            return jsonify({
                "success": False,
                "message": "⚠️ Nenhuma parada pôde ser registrada do arquivo Excel.<br><br><strong>Histórico do Processamento:</strong><br>" + "<br>".join(messages)
            })
            
    except Exception as e:
        logger.error(f"Erro ao registrar lote de Excel via AJAX para Paradas: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao registrar em lote: {str(e)}'}), 500


@parada_bp.route("/upload-process-parada", methods=["GET", "POST"])
@login_required
@admin_required
def upload_process_parada():
    """Página específica para upload e processamento de paradas via Excel."""
    if request.method == "POST":
        google_file_id = request.form.get('google_file_id')
        google_access_token = request.form.get('google_access_token')
        google_file_name = request.form.get('google_file_name', 'google_drive_file.xlsx')
        
        is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                   google_file_id is not None)

        if google_file_id and google_access_token:
            try:
                import requests
                headers = {"Authorization": f"Bearer {google_access_token}"}
                download_url = f"https://www.googleapis.com/drive/v3/files/{google_file_id}?alt=media"
                response = requests.get(download_url, headers=headers)
                if response.status_code != 200:
                    msg = f"Erro ao baixar do Google Drive (Status {response.status_code}): {response.text}"
                    if is_ajax:
                        return jsonify({"success": False, "message": msg}), 400
                    flash(msg, "danger")
                    return redirect(url_for("parada.upload_process_parada"))
                
                temp_dir = os.path.join(tempfile.gettempdir(), "whatsapp_parada")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, google_file_name)
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                session['parada_file_path'] = temp_path
                session['parada_file_name'] = google_file_name
                
                if is_ajax:
                    return jsonify({"success": True, "message": "Planilha carregada do Google Drive com sucesso!", "redirect_url": url_for("parada.registrar_parada")}), 200
                flash("Planilha de paradas carregada do Google Drive com sucesso!", "success")
                return redirect(url_for("parada.registrar_parada"))
            except Exception as e:
                logger.error(f"Erro ao baixar planilha do Google Drive: {e}", exc_info=True)
                msg = f"Erro ao acessar Google Drive: {str(e)}"
                if is_ajax:
                    return jsonify({"success": False, "message": msg}), 500
                flash(msg, "danger")
                return redirect(url_for("parada.upload_process_parada"))
        else:
            file = request.files.get("file")
            if not file or file.filename == "":
                flash("Nenhum arquivo selecionado.", "danger")
                return redirect(request.url)
                
            if not file.filename.lower().endswith(".xlsx"):
                flash("Apenas arquivos Excel (.xlsx) são suportados nesta página.", "danger")
                return redirect(request.url)
                
            try:
                temp_dir = os.path.join(tempfile.gettempdir(), "whatsapp_parada")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, file.filename)
                file.save(temp_path)
                
                session['parada_file_path'] = temp_path
                session['parada_file_name'] = file.filename
                
                flash("Planilha de paradas carregada com sucesso! Prossiga com o registro.", "success")
                return redirect(url_for("parada.registrar_parada"))
            except Exception as e:
                logger.error(f"Erro ao salvar arquivo de upload de paradas: {e}", exc_info=True)
                flash(f"Erro ao carregar arquivo: {str(e)}", "danger")
                return redirect(url_for("parada.upload_process_parada"))
            
    return render_template("parada/upload_process_parada.html")
