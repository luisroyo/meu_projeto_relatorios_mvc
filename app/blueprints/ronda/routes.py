# app/blueprints/ronda/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_, literal
from datetime import datetime, date, time, timedelta, timezone
from app import db
from app.models import Condominio, Ronda, User
from app.forms import TestarRondasForm
from app.services.ronda_logic import processar_log_de_rondas
from app.decorators.admin_required import admin_required 
import logging

logger = logging.getLogger(__name__)

ronda_bp = Blueprint('ronda', __name__, template_folder='templates')

def inferir_turno(data_plantao_obj, escala_plantao_str):
    turno_ronda_base = "Indefinido"
    escala_lower = escala_plantao_str.lower() if escala_plantao_str else ""

    if "18h às 06h" in escala_lower or "18h as 6h" in escala_lower or "noturno" in escala_lower or "noite" in escala_lower:
        turno_ronda_base = "Noturno"
    elif "06h às 18h" in escala_lower or "6h as 18h" in escala_lower or "diurno" in escala_lower or "dia" in escala_lower:
        turno_ronda_base = "Diurno"
    else:
        current_hour_utc = datetime.now(timezone.utc).hour
        if 6 <= current_hour_utc < 18:
            turno_ronda_base = "Diurno"
        else:
            turno_ronda_base = "Noturno"

    if data_plantao_obj and turno_ronda_base != "Indefinido":
        if data_plantao_obj.day % 2 == 0:
            return f"{turno_ronda_base} Par"
        else:
            return f"{turno_ronda_base} Impar"
    
    return escala_plantao_str if escala_plantao_str else "N/A - Turno Indefinido"


@ronda_bp.route('/registrar', methods=['GET', 'POST'])
@login_required # <-- Acesso para todos os usuários logados
def registrar_ronda():
    form = TestarRondasForm()
    relatorio_processado_final = None
    ronda_data_to_save = {}
    ronda_id_existente = request.args.get('ronda_id', type=int)

    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        choices_list = [('', '-- Selecione um Condomínio --')] + \
                       [(str(c.id), c.nome) for c in condominios_db] + \
                       [('Outro', 'Outro')]
        form.nome_condominio.choices = choices_list
    except Exception as e:
        logger.error(f"Erro ao carregar lista de condomínios: {e}", exc_info=True)
        flash('Erro ao carregar lista de condomínios. Tente novamente mais tarde.', 'danger')

    if ronda_id_existente:
        ronda_existente = Ronda.query.get(ronda_id_existente)
        if ronda_existente and (ronda_existente.user_id == current_user.id or current_user.is_admin):
            if ronda_existente.data_hora_fim and not current_user.is_admin:
                flash("Esta ronda já foi finalizada e não pode ser editada.", 'warning')
                return redirect(url_for('ronda.detalhes_ronda', ronda_id=ronda_id_existente))

            form.log_bruto_rondas.data = ronda_existente.log_ronda_bruto
            form.data_plantao.data = ronda_existente.data_plantao_ronda
            form.escala_plantao.data = ronda_existente.escala_plantao
            if ronda_existente.condominio_id:
                form.nome_condominio.data = str(ronda_existente.condominio_id)
            
            try:
                condominio_nome_para_processador = ronda_existente.condominio_obj.nome if ronda_existente.condominio_obj else None
                data_plantao_str_formatada = ronda_existente.data_plantao_ronda.strftime('%d/%m/%Y') if ronda_existente.data_plantao_ronda else None

                relatorio, total_rondas, p_evento, u_evento, soma_minutos = processar_log_de_rondas(
                    log_bruto_rondas_str=ronda_existente.log_ronda_bruto,
                    nome_condominio_str=condominio_nome_para_processador,
                    data_plantao_manual_str=data_plantao_str_formatada,
                    escala_plantao_str=ronda_existente.escala_plantao
                )
                relatorio_processado_final = relatorio
                
                ronda_data_to_save = {
                    'ronda_id': ronda_id_existente,
                    'log_bruto': ronda_existente.log_ronda_bruto,
                    'relatorio_processado': relatorio,
                    'condominio_id': ronda_existente.condominio_id,
                    'data_plantao': ronda_existente.data_plantao_ronda.isoformat() if ronda_existente.data_plantao_ronda else None,
                    'escala_plantao': ronda_existente.escala_plantao,
                    'turno_ronda': ronda_existente.turno_ronda,
                    'total_rondas_no_log': total_rondas,
                    'primeiro_evento_log_dt': p_evento.isoformat() if p_evento else None,
                    'ultimo_evento_log_dt': u_evento.isoformat() if u_evento else None,
                    'duracao_total_rondas_minutos': soma_minutos
                }
            except Exception as e:
                logger.error(f"Erro ao re-processar ronda existente {ronda_id_existente}: {e}", exc_info=True)
                flash(f"Erro ao carregar dados da ronda existente: {str(e)}", 'danger')
        else:
            flash("Ronda não encontrada ou você não tem permissão para editá-la.", 'danger')
            return redirect(url_for('ronda.listar_rondas'))

    if request.method == 'POST':
        if form.validate_on_submit():
            condominio_id_selecionado = form.nome_condominio.data
            log_bruto = form.log_bruto_rondas.data
            data_plantao_obj = form.data_plantao.data
            escala_plantao_str = form.escala_plantao.data
            condominio_obj = None

            if condominio_id_selecionado and condominio_id_selecionado.isdigit():
                condominio_obj = Condominio.query.get(int(condominio_id_selecionado))
            elif condominio_id_selecionado == 'Outro':
                outro_nome_raw = form.nome_condominio_outro.data.strip()
                if not outro_nome_raw:
                    flash('Se "Outro" é selecionado, o nome do condomínio deve ser fornecido.', 'danger')
                    return render_template('relatorio_ronda.html', title='Registrar/Processar Ronda', form=form, relatorio_processado=None, ronda_data_to_save=ronda_data_to_save)
                
                condominio_existente = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(outro_nome_raw)).first()
                if not condominio_existente:
                    try:
                        condominio_obj = Condominio(nome=outro_nome_raw)
                        db.session.add(condominio_obj)
                        db.session.commit()
                        flash(f'Novo condomínio "{condominio_obj.nome}" adicionado.', 'info')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao adicionar o novo condomínio "{outro_nome_raw}".', 'danger')
                        return render_template('relatorio_ronda.html', title='Registrar/Processar Ronda', form=form, relatorio_processado=None, ronda_data_to_save=ronda_data_to_save)
                else:
                    condominio_obj = condominio_existente
            
            if condominio_obj:
                condominio_final_id = condominio_obj.id
                condominio_final_nome = condominio_obj.nome
                
                if log_bruto:
                    try:
                        data_plantao_str_formatada = data_plantao_obj.strftime('%d/%m/%Y') if data_plantao_obj else None
                        
                        relatorio, total_rondas, p_evento, u_evento, soma_minutos = processar_log_de_rondas(
                            log_bruto_rondas_str=log_bruto,
                            nome_condominio_str=condominio_final_nome,
                            data_plantao_manual_str=data_plantao_str_formatada,
                            escala_plantao_str=escala_plantao_str
                        )
                        relatorio_processado_final = relatorio
                        
                        flash('Relatório de ronda processado. Se for administrador, você pode salvar.', 'info')
                        
                        turno_ronda_inferido = inferir_turno(data_plantao_obj, escala_plantao_str)
                        ronda_data_to_save = {
                            'ronda_id': ronda_id_existente,
                            'log_bruto': log_bruto,
                            'relatorio_processado': relatorio,
                            'condominio_id': condominio_final_id,
                            'data_plantao': data_plantao_obj.isoformat() if data_plantao_obj else None,
                            'escala_plantao': escala_plantao_str,
                            'turno_ronda': turno_ronda_inferido,
                            'total_rondas_no_log': total_rondas,
                            'primeiro_evento_log_dt': p_evento.isoformat() if p_evento else None,
                            'ultimo_evento_log_dt': u_evento.isoformat() if u_evento else None,
                            'duracao_total_rondas_minutos': soma_minutos
                        }
                    except Exception as e:
                        flash(f'Erro ao processar com lógica personalizada: {str(e)}', 'danger')
                        relatorio_processado_final = None
                else:
                    flash('O campo "Log Bruto das Rondas" é obrigatório para processamento.', 'warning')
            else:
                flash('Por favor, selecione ou adicione um condomínio válido.', 'danger')
        else:
            flash('Por favor, corrija os erros no formulário.', 'danger')

    return render_template('relatorio_ronda.html',
                           title='Registrar/Processar Ronda',
                           form=form,
                           relatorio_processado=relatorio_processado_final,
                           ronda_data_to_save=ronda_data_to_save)


@ronda_bp.route('/rondas/salvar', methods=['POST'])
@login_required
@admin_required # <-- Apenas admins podem salvar
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
    total_rondas_no_log = data.get('total_rondas_no_log')
    primeiro_evento_log_dt_str = data.get('primeiro_evento_log_dt')
    ultimo_evento_log_dt_str = data.get('ultimo_evento_log_dt')
    duracao_total_rondas_minutos = data.get('duracao_total_rondas_minutos')

    try:
        data_plantao = date.fromisoformat(data_plantao_str) if data_plantao_str else None
        primeiro_evento_log_dt = datetime.fromisoformat(primeiro_evento_log_dt_str) if primeiro_evento_log_dt_str else None
        ultimo_evento_log_dt = datetime.fromisoformat(ultimo_evento_log_dt_str) if ultimo_evento_log_dt_str else None

        query_duplicidade = Ronda.query.filter(
            Ronda.condominio_id == condominio_id,
            Ronda.data_plantao_ronda == data_plantao,
            Ronda.turno_ronda == turno_ronda
        )
        
        if ronda_id:
            ronda_duplicada_existente = query_duplicidade.filter(Ronda.id != ronda_id).first()
            if ronda_duplicada_existente:
                return jsonify({'success': False, 'message': f'A atualização resultaria em uma ronda duplicada.'}), 409

            ronda = Ronda.query.get(ronda_id)
            if not ronda:
                return jsonify({'success': False, 'message': 'Ronda não encontrada.'}), 404
            
            ronda.log_ronda_bruto = log_bruto
            ronda.relatorio_processado = relatorio_processado
            ronda.condominio_id = condominio_id
            ronda.data_plantao_ronda = data_plantao
            ronda.escala_plantao = escala_plantao
            ronda.turno_ronda = turno_ronda
            ronda.total_rondas_no_log = total_rondas_no_log
            ronda.primeiro_evento_log_dt = primeiro_evento_log_dt
            ronda.ultimo_evento_log_dt = ultimo_evento_log_dt
            ronda.duracao_total_rondas_minutos = duracao_total_rondas_minutos
            
            if not ronda.data_hora_inicio:
                ronda.data_hora_inicio = primeiro_evento_log_dt
            ronda.data_hora_fim = ultimo_evento_log_dt
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ronda atualizada e finalizada!', 'ronda_id': ronda.id}), 200
        else:
            ronda_duplicada_existente = query_duplicidade.first()
            if ronda_duplicada_existente:
                return jsonify({'success': False, 'message': f'Já existe uma ronda para este condomínio no turno.'}), 409

            if not all([log_bruto, condominio_id, data_plantao, turno_ronda]):
                return jsonify({'success': False, 'message': 'Dados essenciais ausentes.'}), 400
            
            nova_ronda = Ronda(
                data_hora_inicio=primeiro_evento_log_dt,
                data_hora_fim=ultimo_evento_log_dt,
                log_ronda_bruto=log_bruto,
                relatorio_processado=relatorio_processado,
                condominio_id=condominio_id,
                escala_plantao=escala_plantao,
                data_plantao_ronda=data_plantao,
                turno_ronda=turno_ronda,
                user_id=current_user.id,
                total_rondas_no_log=total_rondas_no_log,
                primeiro_evento_log_dt=primeiro_evento_log_dt,
                ultimo_evento_log_dt=ultimo_evento_log_dt,
                duracao_total_rondas_minutos=duracao_total_rondas_minutos
            )
            db.session.add(nova_ronda)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ronda salva e finalizada!', 'ronda_id': nova_ronda.id}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar/finalizar ronda: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro interno ao salvar ronda: {str(e)}'}), 500


@ronda_bp.route('/rondas/historico', methods=['GET'])
@login_required
def listar_rondas():
    page = request.args.get('page', 1, type=int)
    
    condominio_filter = request.args.get('condominio')
    supervisor_filter_id = request.args.get('supervisor', type=int)
    data_inicio_filter_str = request.args.get('data_inicio')
    data_fim_filter_str = request.args.get('data_fim')
    turno_filter = request.args.get('turno')
    status_ronda_filter = request.args.get('status')

    query = Ronda.query.options(db.joinedload(Ronda.condominio_obj), db.joinedload(Ronda.criador))
    
    if condominio_filter:
        condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condominio_filter)).first()
        if condominio_obj:
            query = query.filter(Ronda.condominio_id == condominio_obj.id)
        else:
            query = query.filter(literal(False))

    if supervisor_filter_id:
        query = query.filter(Ronda.user_id == supervisor_filter_id)
    
    if turno_filter:
        query = query.filter(Ronda.turno_ronda == turno_filter)

    if status_ronda_filter == 'em_andamento':
        query = query.filter(Ronda.data_hora_fim.is_(None))
    elif status_ronda_filter == 'finalizada':
        query = query.filter(Ronda.data_hora_fim.isnot(None))

    if data_inicio_filter_str:
        try:
            data_inicio_filter = datetime.strptime(data_inicio_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio_filter)
        except ValueError:
            flash('Formato de Data de Início inválido. Use AAAA-MM-DD.', 'danger')
    if data_fim_filter_str:
        try:
            data_fim_filter = datetime.strptime(data_fim_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda <= data_fim_filter)
        except ValueError:
            flash('Formato de Data de Fim inválido. Use AAAA-MM-DD.', 'danger')

    if not current_user.is_admin:
        query = query.filter(Ronda.user_id == current_user.id)

    rondas_pagination = query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.data_hora_inicio.desc()).paginate(page=page, per_page=10)

    all_condominios = Condominio.query.order_by(Condominio.nome).all()
    all_supervisors = User.query.filter(User.is_approved == True).order_by(User.username).all()

    all_turnos = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    all_statuses = [
        {'value': '', 'label': '-- Todos --'},
        {'value': 'em_andamento', 'label': 'Em Andamento'},
        {'value': 'finalizada', 'label': 'Finalizada'}
    ]
    
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
                           selected_status=status_ronda_filter)


@ronda_bp.route('/rondas/detalhes/<int:ronda_id>')
@login_required
def detalhes_ronda(ronda_id):
    ronda = Ronda.query.options(db.joinedload(Ronda.criador), db.joinedload(Ronda.condominio_obj)).get_or_404(ronda_id)
    
    if not current_user.is_admin and ronda.user_id != current_user.id:
        flash("Você não tem permissão para visualizar esta ronda.", 'danger')
        return redirect(url_for('ronda.listar_rondas'))

    return render_template('ronda_details.html', title=f'Detalhes da Ronda #{ronda.id}', ronda=ronda)


@ronda_bp.route('/rondas/excluir/<int:ronda_id>', methods=['POST', 'DELETE'])
@login_required
def excluir_ronda(ronda_id):
    ronda_to_delete = Ronda.query.get_or_404(ronda_id)

    if not current_user.is_admin and ronda_to_delete.user_id != current_user.id:
        if request.method == 'DELETE':
            return jsonify({'success': False, 'message': 'Você não tem permissão para excluir esta ronda.'}), 403
        else:
            flash('Você não tem permissão para excluir esta ronda.', 'danger')
            return redirect(url_for('ronda.listar_rondas'))

    try:
        db.session.delete(ronda_to_delete)
        db.session.commit()
        if request.method == 'DELETE':
            return jsonify({'success': True, 'message': f'Ronda {ronda_id} excluída com sucesso.'}), 200
        else:
            flash(f'Ronda {ronda_id} excluída com sucesso.', 'success')
            return redirect(url_for('ronda.listar_rondas'))
            
    except Exception as e:
        db.session.rollback()
        if request.method == 'DELETE':
            return jsonify({'success': False, 'message': f'Erro ao excluir ronda {ronda_id}: {str(e)}'}), 500
        else:
            flash(f'Erro ao excluir ronda {ronda_id}: {str(e)}', 'danger')
            return redirect(url_for('ronda.detalhes_ronda', ronda_id=ronda_id))