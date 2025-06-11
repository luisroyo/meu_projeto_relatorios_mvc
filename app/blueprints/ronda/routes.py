# app/blueprints/ronda/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_, literal # Importa literal!
from datetime import datetime, date, time, timedelta, timezone # Importa time e timedelta
from app import db
from app.models import Condominio, Ronda, User
from app.forms import TestarRondasForm
from app.services.ronda_logic import processar_log_de_rondas
import logging

logger = logging.getLogger(__name__)

ronda_bp = Blueprint('ronda', __name__, template_folder='templates')

@ronda_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_ronda():
    form = TestarRondasForm()
    relatorio_processado_final = None  # Armazena o resultado do processamento
    ronda_data_to_save = {} # Dicionário para armazenar dados da ronda a serem salvos
    ronda_id_existente = request.args.get('ronda_id', type=int) # Para edições/salvamentos parciais

    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        choices_list = [('', '-- Selecione um Condomínio --')] + \
                       [(str(c.id), c.nome) for c in condominios_db] + \
                       [('Outro', 'Outro')]
        form.nome_condominio.choices = choices_list
    except Exception as e:
        logger.error(f"Erro ao carregar lista de condomínios: {e}", exc_info=True)
        flash('Erro ao carregar lista de condomínios. Tente novamente mais tarde.', 'danger')
        form.nome_condominio.choices = [('', '-- Erro ao Carregar --'), ('Outro', 'Outro')]

    # Se estamos editando uma ronda existente
    if ronda_id_existente:
        ronda_existente = Ronda.query.get(ronda_id_existente)
        if ronda_existente and ronda_existente.user_id == current_user.id:
            # Preenche o formulário com dados da ronda existente
            form.log_bruto_rondas.data = ronda_existente.log_ronda_bruto
            form.data_plantao.data = ronda_existente.data_plantao_ronda
            form.escala_plantao.data = ronda_existente.escala_plantao
            # Preenche o condomínio selecionado
            if ronda_existente.condominio_id:
                form.nome_condominio.data = str(ronda_existente.condominio_id)
            # Re-processa o relatório para exibição imediata
            try:
                relatorio_processado_final = processar_log_de_rondas(
                    log_bruto_rondas_str=ronda_existente.log_ronda_bruto,
                    nome_condominio_str=ronda_existente.condominio_obj.nome if ronda_existente.condominio_obj else None,
                    data_plantao_manual_str=ronda_existente.data_plantao_ronda.strftime('%d/%m/%Y') if ronda_existente.data_plantao_ronda else None,
                    escala_plantao_str=ronda_existente.escala_plantao
                )
                ronda_data_to_save = {
                    'ronda_id': ronda_id_existente,
                    'log_bruto': ronda_existente.log_ronda_bruto,
                    'relatorio_processado': relatorio_processado_final,
                    'condominio_id': ronda_existente.condominio_id,
                    'data_plantao': ronda_existente.data_plantao_ronda.isoformat() if ronda_existente.data_plantao_ronda else None,
                    'escala_plantao': ronda_existente.escala_plantao,
                    'turno_ronda': ronda_existente.turno_ronda,
                    'data_hora_inicio': ronda_existente.data_hora_inicio.isoformat() if ronda_existente.data_hora_inicio else None,
                    'data_hora_fim': ronda_existente.data_hora_fim.isoformat() if ronda_existente.data_hora_fim else None
                }
            except Exception as e:
                logger.error(f"Erro ao re-processar ronda existente {ronda_id_existente}: {e}", exc_info=True)
                flash(f"Erro ao carregar dados da ronda existente: {str(e)}", 'danger')
        else:
            flash("Ronda não encontrada ou você não tem permissão para editá-la.", 'danger')
            return redirect(url_for('ronda.listar_rondas'))

    if form.validate_on_submit():
        condominio_id_selecionado = form.nome_condominio.data
        log_bruto = form.log_bruto_rondas.data
        data_plantao_obj = form.data_plantao.data
        escala_plantao_str = form.escala_plantao.data

        condominio_obj = None
        if condominio_id_selecionado and condominio_id_selecionado.isdigit():
            condominio_obj = Condominio.query.get(int(condominio_id_selecionado))
        elif condominio_id_selecionado == 'Outro':
            outro_nome_raw = form.nome_condominio_outro.data.strip() if form.nome_condominio_outro.data else ''
            if not outro_nome_raw:
                flash('Se "Outro" é selecionado, o nome do condomínio deve ser fornecido.', 'danger')
                return render_template('relatorio_ronda.html',
                                       title='Registrar/Processar Ronda',
                                       form=form,
                                       relatorio_processado=None)
            else:
                condominio_existente = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(outro_nome_raw)).first()
                if not condominio_existente:
                    try:
                        condominio_obj = Condominio(nome=outro_nome_raw)
                        db.session.add(condominio_obj)
                        db.session.commit()
                        flash(f'Novo condomínio "{condominio_obj.nome}" adicionado.', 'info')
                    except Exception as e_add_cond:
                        db.session.rollback()
                        logger.error(f"Erro ao adicionar novo condomínio '{outro_nome_raw}': {e_add_cond}", exc_info=True)
                        flash(f'Erro ao adicionar o novo condomínio "{outro_nome_raw}".', 'danger')
                        return render_template('relatorio_ronda.html',
                                               title='Registrar/Processar Ronda',
                                               form=form,
                                               relatorio_processado=None)
                else:
                    condominio_obj = condominio_existente
        
        condominio_final_id = condominio_obj.id if condominio_obj else None
        condominio_final_nome = condominio_obj.nome if condominio_obj else None

        turno_ronda_inferido = None
        if data_plantao_obj:
            # Pega a hora atual do servidor para inferir o turno
            now_hour = datetime.now(timezone.utc).hour
            
            # --- LÓGICA DE INFERÊNCIA DE TURNO AJUSTADA (REPETIDA AQUI PARA CLAREZA) ---
            if now_hour >= 6 and now_hour < 18:
                turno_ronda_base = "Diurno"
            else: # now_hour >= 18 ou now_hour < 6
                turno_ronda_base = "Noturno"

            if data_plantao_obj.day % 2 == 0: # Dia par
                turno_ronda_inferido = f"{turno_ronda_base} Par"
            else: # Dia ímpar
                turno_ronda_inferido = f"{turno_ronda_base} Impar"
        # FIM DA LÓGICA DE INFERÊNCIA DE TURNO

        if condominio_final_id and log_bruto:
            try:
                data_plantao_str_formatada = data_plantao_obj.strftime('%d/%m/%Y') if data_plantao_obj else None

                logger.info(f"Chamando processar_log_de_rondas com: "
                            f"Condomínio='{condominio_final_nome}', "
                            f"Data='{data_plantao_str_formatada}', "
                            f"Escala='{escala_plantao_str}'")

                relatorio_processado_final = processar_log_de_rondas(
                    log_bruto_rondas_str=log_bruto,
                    nome_condominio_str=condominio_final_nome,
                    data_plantao_manual_str=data_plantao_str_formatada,
                    escala_plantao_str=escala_plantao_str
                )

                if relatorio_processado_final:
                    flash('Relatório de ronda processado. Salve para registrar!', 'info')
                else:
                    flash('Sua lógica processou, mas retornou um resultado vazio.', 'warning')
                    logger.warning("processar_log_de_rondas retornou None ou string vazia.")
                
                # Prepara os dados para serem salvos (passa para o frontend)
                ronda_data_to_save = {
                    'ronda_id': ronda_id_existente, # Se for uma edição, o ID já existe
                    'log_bruto': log_bruto,
                    'relatorio_processado': relatorio_processado_final,
                    'condominio_id': condominio_final_id,
                    'data_plantao': data_plantao_obj.isoformat() if data_plantao_obj else None, # Formato ISO para JS
                    'escala_plantao': escala_plantao_str,
                    'turno_ronda': turno_ronda_inferido,
                    'data_hora_inicio': datetime.now(timezone.utc).isoformat() if not ronda_id_existente else None, # Apenas se for nova ronda
                    'data_hora_fim': None # Inicia como None, pode ser atualizado ao finalizar
                }

            except Exception as e_custom_logic:
                logger.exception("Erro ao processar com lógica customizada:")
                flash(f'Erro ao processar com lógica personalizada: {str(e_custom_logic)}', 'danger')
                relatorio_processado_final = None
        elif not log_bruto:
            flash('O campo "Log Bruto das Rondas" é obrigatório para processamento.', 'warning')
        else:
            flash('Por favor, forneça um log bruto e selecione ou adicione um condomínio válido.', 'danger')

    logger.debug(f"[DEBUG] Valor de relatorio_processado_final antes de renderizar: {relatorio_processado_final}")
    
    return render_template('relatorio_ronda.html',
                           title='Registrar/Processar Ronda',
                           form=form,
                           relatorio_processado=relatorio_processado_final,
                           ronda_data_to_save=ronda_data_to_save # Passa os dados para o frontend
                           )

# --- NOVA ROTA: Salvar (Criar ou Atualizar) Ronda ---
@ronda_bp.route('/rondas/salvar', methods=['POST'])
@login_required
def salvar_ronda():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos.'}), 400

    ronda_id = data.get('ronda_id')
    log_bruto = data.get('log_bruto')
    relatorio_processado = data.get('relatorio_processado')
    condominio_id = data.get('condominio_id')
    data_plantao_str = data.get('data_plantao')
    escala_plantao = data.get('escala_plantao')
    turno_ronda = data.get('turno_ronda')
    data_hora_inicio_str = data.get('data_hora_inicio')
    finalizar_ronda = data.get('finalizar_ronda', False) # Flag para indicar se a ronda deve ser finalizada

    try:
        data_plantao = date.fromisoformat(data_plantao_str) if data_plantao_str else None
        data_hora_inicio = datetime.fromisoformat(data_hora_inicio_str) if data_hora_inicio_str else None

        if ronda_id:
            # Atualizar ronda existente (salvamento parcial)
            ronda = Ronda.query.get(ronda_id)
            if not ronda or ronda.user_id != current_user.id:
                return jsonify({'success': False, 'message': 'Ronda não encontrada ou sem permissão.'}), 403
            
            ronda.log_ronda_bruto = log_bruto
            ronda.relatorio_processado = relatorio_processado
            ronda.condominio_id = condominio_id
            ronda.data_plantao_ronda = data_plantao
            ronda.escala_plantao = escala_plantao
            ronda.turno_ronda = turno_ronda
            # Se for finalizar, define a data_hora_fim
            if finalizar_ronda:
                ronda.data_hora_fim = datetime.now(timezone.utc)
            
            db.session.commit()
            logger.info(f"Ronda ID {ronda.id} atualizada com sucesso por {current_user.username}. Finalizada: {finalizar_ronda}")
            return jsonify({'success': True, 'message': 'Ronda atualizada com sucesso!', 'ronda_id': ronda.id}), 200
        else:
            # Criar nova ronda
            if not all([log_bruto, condominio_id, data_plantao, turno_ronda, data_hora_inicio]):
                return jsonify({'success': False, 'message': 'Dados mínimos para criar a ronda ausentes.'}), 400

            nova_ronda = Ronda(
                data_hora_inicio=data_hora_inicio,
                log_ronda_bruto=log_bruto,
                relatorio_processado=relatorio_processado,
                condominio_id=condominio_id,
                escala_plantao=escala_plantao,
                data_plantao_ronda=data_plantao,
                turno_ronda=turno_ronda,
                user_id=current_user.id,
                data_hora_fim=datetime.now(timezone.utc) if finalizar_ronda else None # Define fim se for finalizar já na criação
            )
            db.session.add(nova_ronda)
            db.session.commit()
            logger.info(f"Nova ronda criada por {current_user.username}. ID: {nova_ronda.id}. Finalizada: {finalizar_ronda}")
            return jsonify({'success': True, 'message': 'Ronda salva com sucesso!', 'ronda_id': nova_ronda.id}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar/atualizar ronda para {current_user.username}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao salvar ronda: {str(e)}'}), 500


# --- CONTINUAÇÃO: Listagem de Rondas ---
@ronda_bp.route('/rondas/historico', methods=['GET'])
@login_required
def listar_rondas():
    page = request.args.get('page', 1, type=int)
    
    # --- FILTROS ---
    condominio_filter = request.args.get('condominio', type=str)
    supervisor_filter_id = request.args.get('supervisor', type=int) # supervisor é o user_id
    data_inicio_filter_str = request.args.get('data_inicio', type=str)
    data_fim_filter_str = request.args.get('data_fim', type=str)
    turno_filter = request.args.get('turno', type=str)
    
    # Adicionar filtro de status (se a ronda está em andamento ou finalizada)
    status_ronda_filter = request.args.get('status', type=str)

    query = Ronda.query.join(User).outerjoin(Condominio) # Join com User e Condominio para filtros/exibição
    
    # Filtro por Condomínio
    if condominio_filter:
        condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condominio_filter)).first()
        if condominio_obj:
            query = query.filter(Ronda.condominio_id == condominio_obj.id)
        else:
            query = query.filter(literal(False)) # Retorna um conjunto vazio

    # Filtro por Supervisor (o criador da ronda)
    if supervisor_filter_id:
        query = query.filter(Ronda.user_id == supervisor_filter_id)
    
    # Filtro por Turno
    if turno_filter:
        query = query.filter(Ronda.turno_ronda == turno_filter)

    # Filtro por Status da Ronda
    if status_ronda_filter == 'em_andamento':
        query = query.filter(Ronda.data_hora_fim.is_(None))
    elif status_ronda_filter == 'finalizada':
        query = query.filter(Ronda.data_hora_fim.isnot(None))

    # Filtro por Período de Data de Plantão
    if data_inicio_filter_str:
        try:
            data_inicio_filter = datetime.strptime(data_inicio_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio_filter)
        except ValueError:
            flash('Formato de Data de Início inválido. Use AAAA-MM-DD.', 'danger')
            logger.warning(f"Formato de data de início inválido: {data_inicio_filter_str}")
    if data_fim_filter_str:
        try:
            data_fim_filter = datetime.strptime(data_fim_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda <= data_fim_filter)
        except ValueError:
            flash('Formato de Data de Fim inválido. Use AAAA-MM-DD.', 'danger')
            logger.warning(f"Formato de data de fim inválido: {data_fim_filter_str}")

    # Apenas o usuário logado pode ver suas rondas, a menos que seja admin
    if not current_user.is_admin:
        query = query.filter(Ronda.user_id == current_user.id)

    rondas_pagination = query.order_by(Ronda.data_hora_inicio.desc()).paginate(page=page, per_page=10)

    all_condominios = Condominio.query.order_by(Condominio.nome).all()
    # Pega apenas os usuários que realmente criaram rondas ou todos os admins
    users_with_rondas = db.session.query(User).join(Ronda).distinct(User.id).order_by(User.username).all()
    # Ou, se preferir todos os usuários que podem ser supervisores:
    # all_supervisors = User.query.filter(or_(User.is_admin==True, User.is_approved==True)).order_by(User.username).all()
    all_supervisors = User.query.filter(User.is_approved == True).order_by(User.username).all()

    all_turnos = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    all_statuses = [
        {'value': '', 'label': '-- Todos --'},
        {'value': 'em_andamento', 'label': 'Em Andamento'},
        {'value': 'finalizada', 'label': 'Finalizada'}
    ]

    logger.info(f"Usuário '{current_user.username}' acessou o histórico de rondas. Filtros: Cond: {condominio_filter}, Sup: {supervisor_filter_id}, Data Início: {data_inicio_filter_str}, Data Fim: {data_fim_filter_str}, Turno: {turno_filter}, Status: {status_ronda_filter}")
    
    return render_template('ronda_list.html',
                           title='Histórico de Rondas',
                           rondas_pagination=rondas_pagination,
                           condominios=all_condominios,
                           supervisors=all_supervisors,
                           turnos=all_turnos,
                           statuses=all_statuses,
                           selected_condominio=condominio_filter,
                           selected_supervisor=supervisor_filter_id,
                           selected_data_inicio=data_inicio_filter_str,
                           selected_data_fim=data_fim_filter_str,
                           selected_turno=turno_filter,
                           selected_status=status_ronda_filter
                           )

# --- DETALHES DA RONDA ---
@ronda_bp.route('/rondas/detalhes/<int:ronda_id>')
@login_required
def detalhes_ronda(ronda_id):
    ronda = Ronda.query.options(db.joinedload(Ronda.criador), db.joinedload(Ronda.condominio_obj)).get_or_404(ronda_id)
    
    # Garante que apenas o criador ou um admin possa ver os detalhes
    if not current_user.is_admin and ronda.user_id != current_user.id:
        flash("Você não tem permissão para visualizar esta ronda.", 'danger')
        return redirect(url_for('ronda.listar_rondas'))

    logger.info(f"Usuário '{current_user.username}' acessou detalhes da ronda ID: {ronda_id}")
    return render_template('ronda_details.html',
                           title=f'Detalhes da Ronda #{ronda.id}',
                           ronda=ronda)

# --- EXCLUIR RONDA ---
@ronda_bp.route('/rondas/excluir/<int:ronda_id>', methods=['POST'])
@login_required
def excluir_ronda(ronda_id):
    ronda_to_delete = Ronda.query.get_or_404(ronda_id)

    # Apenas o criador da ronda ou um admin pode excluir
    if not current_user.is_admin and ronda_to_delete.user_id != current_user.id:
        flash("Você não tem permissão para excluir esta ronda.", 'danger')
        return redirect(url_for('ronda.listar_rondas'))

    try:
        db.session.delete(ronda_to_delete)
        db.session.commit()
        flash(f'Ronda {ronda_id} excluída com sucesso.', 'success')
        logger.info(f"Usuário '{current_user.username}' excluiu a ronda ID {ronda_id}.")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir ronda {ronda_id}: {str(e)}', 'danger')
        logger.error(f"Erro ao excluir ronda ID {ronda_id} por {current_user.username}: {e}", exc_info=True)
    
    return redirect(url_for('ronda.listar_rondas'))