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

from app import db, csrf
from app.decorators.admin_required import admin_required
from app.forms import TestarRondasForm
from app.models import Condominio, EscalaMensal, Ronda, User, WhatsAppMessage
from app.services.ronda_routes_core.routes_service import RondaRoutesService
from app.services.whatsapp_processor import WhatsAppProcessor
from app.services.ronda_utils import get_system_user, infer_condominio_from_filename # Importa funções específicas

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
                    # Novo arquivo enviado - salva na sessão e processa sempre
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
                    # MODIFICAÇÃO: Só processa o arquivo fixo se NÃO houver texto no log manual
                    # Isso permite que o usuário edite o texto e re-processe sem perder as alterações
                    if form.log_bruto_rondas.data and form.log_bruto_rondas.data.strip():
                        print("[DEBUG] Texto manual detectado. Ignorando re-processamento do arquivo fixo.")
                        file_path = None # Pula o processamento do arquivo
                    else:
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
                

                
                if file_path:
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
                    
                    # Converter as datas de filtro (que representam horário de Brasília) para UTC para buscar no arquivo e banco de modo igual se o parse for UTC
                    from app.utils.date_utils import get_local_tz
                    import pytz
                    local_tz = get_local_tz()
                    
                    data_inicio_utc = local_tz.localize(data_inicio).astimezone(pytz.utc)
                    data_fim_utc = local_tz.localize(data_fim).astimezone(pytz.utc)
                    
                    print(f"[DEBUG] Processando arquivo: {file_path}")
                    print(f"[DEBUG] Período: {data_inicio_utc} até {data_fim_utc}")
                    
                    # Processa mensagens do período usando as datas em UTC para serem justas com o format do BD
                    plantoes = processor.process_file(file_path, data_inicio_utc, data_fim_utc)
                    
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
            
        # Converter as datas de filtro (que representam horário de Brasília) para UTC para buscar no banco
        from app.utils.date_utils import get_local_tz
        import pytz
        local_tz = get_local_tz()
        
        # Localiza o datetime ingênuo e depois converte a mesma representação de tempo para a escala UTC
        data_inicio_utc = local_tz.localize(data_inicio).astimezone(pytz.utc)
        data_fim_utc = local_tz.localize(data_fim).astimezone(pytz.utc)
        
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

@ronda_bp.route("/processar-whatsapp-bd-ajax", methods=["POST"])
@csrf.exempt
@login_required
@admin_required
def processar_whatsapp_bd_ajax():
    """Busca mensagens do WhatsApp no banco (sem arquivo) e processa via AJAX."""
    try:
        condominio_id = request.form.get('condominio_id')
        data_plantao = request.form.get('data_plantao')
        escala_plantao = request.form.get('escala_plantao')
        
        # O campo nome_condominio do formulário envia o ID do condomínio.
        if not all([condominio_id, data_plantao, escala_plantao]):
            return jsonify({'success': False, 'message': 'Condomínio, Data e Escala são obrigatórios'}), 400
            
        condominio = Condominio.query.get(condominio_id)
        if not condominio:
            return jsonify({'success': False, 'message': 'Condomínio não encontrado'}), 404
            
        from datetime import datetime, timedelta
        data_dt = datetime.strptime(data_plantao, '%Y-%m-%d')
        
        # Determina horário baseado na escala
        if escala_plantao == "06h às 18h":
            data_inicio = data_dt.replace(hour=6, minute=0, second=0)
            data_fim = data_dt.replace(hour=17, minute=59, second=59)
        else:  # 18h às 06h
            data_inicio = data_dt.replace(hour=18, minute=0, second=0)
            data_fim = (data_dt + timedelta(days=1)).replace(hour=5, minute=59, second=59)
            
        # Converter as datas de filtro (que representam horário de Brasília) para UTC para buscar no banco
        from app.utils.date_utils import get_local_tz
        import pytz
        local_tz = get_local_tz()
        
        # Localiza o datetime ingênuo e depois converte a mesma representação de tempo para a escala UTC
        data_inicio_utc = local_tz.localize(data_inicio).astimezone(pytz.utc)
        data_fim_utc = local_tz.localize(data_fim).astimezone(pytz.utc)
        
        # Opcional (se tiver auto-sync ativado)...
        if condominio.whatsapp_group_id:
            try:
                import requests as req_lib
                import os
                NODE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3001') + '/api/whatsapp/messages'
                sync_resp = req_lib.get(
                    f"{NODE_URL}/{condominio.whatsapp_group_id}?count=200",
                    timeout=3
                )
                if sync_resp.status_code == 200:
                    sync_data = sync_resp.json()
                    msgs_to_save = sync_data.get('messages', [])
                    for msg_data in msgs_to_save:
                        ts = msg_data.get('timestamp')
                        from datetime import timezone
                        try:
                            if isinstance(ts, dict) and 'low' in ts:
                                ts = ts['low']
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
                        except Exception:
                            dt = datetime.now(timezone.utc)
                        exists = WhatsAppMessage.query.filter_by(message_id=msg_data.get('message_id')).first()
                        if not exists:
                            db.session.add(WhatsAppMessage(
                                message_id=msg_data.get('message_id'),
                                condominio_id=condominio.id,
                                remote_jid=msg_data.get('group_id'),
                                participant_jid=msg_data.get('participant_id', 'unknown'),
                                push_name=msg_data.get('push_name', ''),
                                content=msg_data.get('content', ''),
                                timestamp=dt
                            ))
                    db.session.commit()
            except Exception as sync_err:
                logger.warning(f"Sync do Node falhou (não fatal): {sync_err}")
        # --- Fim do Auto-Sync ---
            
        # Buscar mensagens na tabela WhatsAppMessage usando UTC
        messages = WhatsAppMessage.query.filter(
            WhatsAppMessage.condominio_id == condominio_id,
            WhatsAppMessage.timestamp >= data_inicio_utc,
            WhatsAppMessage.timestamp <= data_fim_utc
        ).order_by(WhatsAppMessage.timestamp.asc()).all()
        
        if not messages:
            return jsonify({
                'success': False,
                'message': f'Nenhuma mensagem encontrada no banco para {condominio.nome} no período selecionado. Verifique se o grupo está mapeado e o robô está conectado.'
            }), 404
            
        # Formatar mensagens como Log de texto
        log_lines = []
        
        from app.utils.date_utils import get_local_tz
        local_tz = get_local_tz()
        
        for msg in messages:
            # Converter de UTC para o timezone local
            local_dt = msg.timestamp
            if local_dt.tzinfo:
                local_dt = local_dt.astimezone(local_tz)
            else:
                import pytz
                local_dt = pytz.utc.localize(local_dt).astimezone(local_tz)

            time_str = local_dt.strftime('%H:%M')
            date_str = local_dt.strftime('%d/%m/%Y')
            author = msg.push_name or msg.participant_jid
            content = msg.content.replace('\n', ' ')
            log_lines.append(f"[{time_str}, {date_str}] {author}: {content}")
            
        log_bruto = "\n".join(log_lines)
        
        from app.services.ronda_logic.processor import processar_log_de_rondas
        relatorio_final, rondas_completas_count, primeiro_dt, ultimo_dt, soma_minutos = processar_log_de_rondas(
            log_bruto_rondas_str=log_bruto,
            nome_condominio_str=condominio.nome,
            data_plantao_manual_str="", 
            escala_plantao_str=""
        )
        
        return jsonify({
            'success': True,
            'log_formatado': log_bruto,
            'relatorio_processado': relatorio_final,
            'total_mensagens': len(messages),
            'message': f'Log carregado do Banco! {len(messages)} mensagens encontradas.'
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar do BD via AJAX: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao processar: {str(e)}'}), 500


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


@ronda_bp.route("/upload-process-ronda", methods=["GET", "POST"])
@login_required
@admin_required # Apenas administradores podem usar esta funcionalidade
def upload_process_ronda():
    """
    Rota para upload e processamento manual de arquivos de ronda do WhatsApp.
    Permite selecionar mês e ano para filtragem.
    Suporta arquivo .txt ou texto bruto colado.
    """
    if request.method == "GET":
        condominios = Condominio.query.order_by(Condominio.nome).all()
        return render_template(
            "ronda/upload_process_ronda.html", 
            title="Upload e Processamento de Rondas",
            condominios=condominios
        )
    
    elif request.method == "POST":
        month = request.form.get('month', type=int)
        year = request.form.get('year', type=int)
        
        # Variáveis para processamento
        condominio = None
        temp_filepath = None
        input_type = "unknown"
        log_content_completo = ""

        try:
            # 1. Verificar se é upload de Arquivo
            if 'whatsapp_file' in request.files and request.files['whatsapp_file'].filename != '':
                input_type = "file"
                whatsapp_file = request.files['whatsapp_file']
                
                if not whatsapp_file.filename.lower().endswith('.txt'):
                    return jsonify({"success": False, "message": "Apenas arquivos .txt são permitidos."}), 400

                # Salvar arquivo temporariamente
                temp_dir = tempfile.gettempdir()
                temp_filepath = os.path.join(temp_dir, whatsapp_file.filename)
                whatsapp_file.save(temp_filepath)
                
                # Identifica condomínio
                condominio = infer_condominio_from_filename(whatsapp_file.filename)
                if not condominio:
                    if os.path.exists(temp_filepath): os.remove(temp_filepath)
                    return jsonify({"success": False, "message": f"Não foi possível identificar o condomínio pelo nome do arquivo '{whatsapp_file.filename}'."}), 400
                
                # Ler conteúdo do arquivo
                try:
                    with open(temp_filepath, 'r', encoding='utf-8') as f:
                        log_content_completo = f.read()
                except UnicodeDecodeError:
                    with open(temp_filepath, 'r', encoding='latin-1') as f:
                        log_content_completo = f.read()
                
                # Limpeza do arquivo será feita no finally ou após processamento

            # 2. Verificar se é Texto Bruto
            elif 'raw_text' in request.form and request.form['raw_text'].strip():
                input_type = "text"
                log_content_completo = request.form['raw_text']
                condominio_id = request.form.get('condominio_id')
                
                if not condominio_id:
                    return jsonify({"success": False, "message": "Condomínio é obrigatório para entrada de texto."}), 400
                
                condominio = Condominio.query.get(condominio_id)
                if not condominio:
                    return jsonify({"success": False, "message": "Condomínio selecionado não encontrado."}), 404

            else:
                return jsonify({"success": False, "message": "Nenhum arquivo ou texto enviado."}), 400

            # 3. Processamento usando ronda_logic
            from app.services.ronda_logic.processor import extrair_plantoes_do_log
            
            plantoes_encontrados = extrair_plantoes_do_log(log_content_completo)

            if not plantoes_encontrados:
                if temp_filepath and os.path.exists(temp_filepath): os.remove(temp_filepath)
                return jsonify({"success": False, "message": "Nenhuma mensagem de plantão válida encontrada."}), 404

            # 4. Filtros de Mês/Ano e Salvamento
            system_user = get_system_user()
            total_rondas_salvas = 0
            messages = []
            
            for plantao_dict in plantoes_encontrados:
                data_plantao_str = plantao_dict['data_plantao']
                escala = plantao_dict['escala']
                log_bruto = plantao_dict['log_bruto']
                
                # Parse da data para filtros
                try:
                    dt_plantao = datetime.strptime(data_plantao_str, "%d/%m/%Y")
                except ValueError:
                    continue # Pula se data inválida (improvável dado o parser)

                # Filtros
                if month and dt_plantao.month != month:
                    continue
                if year and dt_plantao.year != year:
                    continue
                
                try:
                    ronda_data = {
                        "condominio_id": str(condominio.id),
                        "data_plantao": dt_plantao.strftime("%Y-%m-%d"),
                        "escala_plantao": escala,
                        "log_bruto": log_bruto,
                        "ronda_id": None,
                        "supervisor_id": None,
                    }
                    
                    success, message, status_code, ronda_id = RondaRoutesService.salvar_ronda(ronda_data, system_user)
                    
                    if success:
                        total_rondas_salvas += 1
                        messages.append(f"✅ Ronda para {condominio.nome} em {data_plantao_str} ({escala}) registrada! ID: {ronda_id}")
                    else:
                        messages.append(f"❌ Falha ao registrar ronda para {condominio.nome} em {data_plantao_str} ({escala}): {message}")
                
                except Exception as e:
                    error_msg = f"Erro ao processar plantão {data_plantao_str}: {str(e)}"
                    messages.append(f"❌ {error_msg}")
                    logger.error(error_msg, exc_info=True)

            # Limpeza
            if temp_filepath and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            
            # Retorno
            if total_rondas_salvas > 0:
                return jsonify({
                    "success": True,
                    "message": f"🎉 Processamento concluído! {total_rondas_salvas} ronda(s) salva(s).<br><br><strong>Detalhes:</strong><br>" + "<br>".join(messages)
                }), 200
            elif not messages:
                 return jsonify({"success": False, "message": "Nenhum plantão corresponde aos filtros de mês/ano selecionados."}), 404
            else:
                return jsonify({
                    "success": False,
                    "message": "⚠️ Nenhuma ronda foi salva.<br><br><strong>Detalhes:</strong><br>" + "<br>".join(messages)
                }), 500

        except Exception as e:
            logger.error(f"Erro geral no upload e processamento de ronda: {e}", exc_info=True)
            if 'temp_filepath' in locals() and temp_filepath and os.path.exists(temp_filepath):
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

