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
    """Infere o turno da ronda com base na data do plantão e na escala."""
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
@login_required
def registrar_ronda():
    ronda_id_existente = request.args.get('ronda_id', type=int)
    if request.method == 'POST':
        ronda_id_from_form = request.form.get('ronda_id_input', type=int)
        if ronda_id_from_form:
            ronda_id_existente = ronda_id_from_form
            
    form = TestarRondasForm()
    relatorio_processado_final = None
    ronda_data_to_save = {}
    title = "Editar Ronda" if ronda_id_existente else "Registrar/Processar Ronda"

    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        choices_condominios = [('', '-- Selecione um Condomínio --')] + [(str(c.id), c.nome) for c in condominios_db] + [('Outro', 'Outro')]
        form.nome_condominio.choices = choices_condominios
        
        supervisores_db = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        choices_supervisores = [('0', '-- Nenhum Supervisor --')] + [(s.id, s.username) for s in supervisores_db]
        form.supervisor_id.choices = choices_supervisores
    except Exception as e:
        logger.error(f"Erro ao carregar listas de condomínios/supervisores: {e}", exc_info=True)
        flash('Erro ao carregar dados do formulário. Tente novamente mais tarde.', 'danger')
    
    if ronda_id_existente and request.method == 'GET':
        ronda_existente = Ronda.query.get_or_404(ronda_id_existente)
        if not (current_user.is_admin or current_user.is_supervisor):
            flash("Você não tem permissão para editar esta ronda.", 'danger')
            return redirect(url_for('ronda.listar_rondas'))

        form.log_bruto_rondas.data = ronda_existente.log_ronda_bruto
        form.data_plantao.data = ronda_existente.data_plantao_ronda
        form.escala_plantao.data = ronda_existente.escala_plantao
        form.nome_condominio.data = str(ronda_existente.condominio_id) if ronda_existente.condominio_id else ''
        form.supervisor_id.data = ronda_existente.supervisor_id if ronda_existente.supervisor_id else 0
        
        relatorio_processado_final = ronda_existente.relatorio_processado
        ronda_data_to_save = {
            'ronda_id': ronda_existente.id, 'log_bruto': ronda_existente.log_ronda_bruto, 
            'relatorio_processado': relatorio_processado_final, 'condominio_id': ronda_existente.condominio_id,
            'data_plantao': ronda_existente.data_plantao_ronda.isoformat() if ronda_existente.data_plantao_ronda else None,
            'escala_plantao': ronda_existente.escala_plantao, 'turno_ronda': ronda_existente.turno_ronda,
            'supervisor_id': ronda_existente.supervisor_id, 'total_rondas_no_log': ronda_existente.total_rondas_no_log,
            'primeiro_evento_log_dt': ronda_existente.primeiro_evento_log_dt.isoformat() if ronda_existente.primeiro_evento_log_dt else None,
            'ultimo_evento_log_dt': ronda_existente.ultimo_evento_log_dt.isoformat() if ronda_existente.ultimo_evento_log_dt else None,
            'duracao_total_rondas_minutos': ronda_existente.duracao_total_rondas_minutos
        }

    if request.method == 'POST' and form.validate_on_submit():
        log_bruto = form.log_bruto_rondas.data
        data_plantao_obj = form.data_plantao.data
        escala_plantao_str = form.escala_plantao.data
        condominio_id_sel = form.nome_condominio.data
        supervisor_id_sel = form.supervisor_id.data
        condominio_obj = None

        if condominio_id_sel and condominio_id_sel.isdigit():
            condominio_obj = Condominio.query.get(int(condominio_id_sel))
        elif condominio_id_sel == 'Outro':
            outro_nome = form.nome_condominio_outro.data.strip()
            if not outro_nome:
                flash('Se "Outro" é selecionado, o nome do condomínio deve ser fornecido.', 'danger')
                return render_template('relatorio_ronda.html', title=title, form=form, ronda_data_to_save=ronda_data_to_save)
            
            condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(outro_nome)).first()
            if not condominio_obj:
                try:
                    condominio_obj = Condominio(nome=outro_nome)
                    db.session.add(condominio_obj)
                    db.session.commit()
                    flash(f'Novo condomínio "{condominio_obj.nome}" adicionado.', 'info')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao adicionar novo condomínio: {e}', 'danger')
                    return render_template('relatorio_ronda.html', title=title, form=form, ronda_data_to_save=ronda_data_to_save)

        if condominio_obj and log_bruto:
            try:
                data_plantao_fmt = data_plantao_obj.strftime('%d/%m/%Y') if data_plantao_obj else None
                relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
                    log_bruto_rondas_str=log_bruto, nome_condominio_str=condominio_obj.nome,
                    data_plantao_manual_str=data_plantao_fmt, escala_plantao_str=escala_plantao_str)
                relatorio_processado_final = relatorio
                flash('Relatório de ronda processado. Verifique os dados e salve se estiver correto.', 'info')
                turno_inferido = inferir_turno(data_plantao_obj, escala_plantao_str)
                ronda_data_to_save = {
                    'ronda_id': ronda_id_existente, 'log_bruto': log_bruto, 'relatorio_processado': relatorio,
                    'condominio_id': condominio_obj.id,
                    'data_plantao': data_plantao_obj.isoformat() if data_plantao_obj else None,
                    'escala_plantao': escala_plantao_str, 'turno_ronda': turno_inferido,
                    'supervisor_id': supervisor_id_sel, 'total_rondas_no_log': total,
                    'primeiro_evento_log_dt': p_evento.isoformat() if p_evento else None,
                    'ultimo_evento_log_dt': u_evento.isoformat() if u_evento else None,
                    'duracao_total_rondas_minutos': duracao
                }
            except Exception as e:
                flash(f'Erro ao processar o log de rondas: {str(e)}', 'danger')
    elif request.method == 'POST':
        flash('Por favor, corrija os erros no formulário.', 'danger')

    return render_template('relatorio_ronda.html',
                           title=title,
                           form=form,
                           relatorio_processado=relatorio_processado_final,
                           ronda_data_to_save=ronda_data_to_save)


@ronda_bp.route('/rondas/salvar', methods=['POST'])
@login_required
def salvar_ronda():
    if not (current_user.is_admin or current_user.is_supervisor):
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos.'}), 400

    ronda_id = data.get('ronda_id')
    log_bruto = data.get('log_bruto')
    condominio_id_str = data.get('condominio_id')
    data_plantao_str = data.get('data_plantao')
    escala_plantao = data.get('escala_plantao')
    supervisor_id_str = data.get('supervisor_id')
    
    try:
        condominio_obj = Condominio.query.get(int(condominio_id_str)) if condominio_id_str and condominio_id_str.isdigit() else None
        if not all([log_bruto, condominio_obj, data_plantao_str, escala_plantao]):
            return jsonify({'success': False, 'message': 'Dados essenciais ausentes.'}), 400

        data_plantao = date.fromisoformat(data_plantao_str)
        data_plantao_fmt = data_plantao.strftime('%d/%m/%Y')
        
        relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
            log_bruto_rondas_str=log_bruto, nome_condominio_str=condominio_obj.nome,
            data_plantao_manual_str=data_plantao_fmt, escala_plantao_str=escala_plantao)
        
        turno_ronda = inferir_turno(data_plantao, escala_plantao)
        supervisor_id_para_db = int(supervisor_id_str) if supervisor_id_str and str(supervisor_id_str) != '0' else None

        if ronda_id:
            ronda = Ronda.query.get(ronda_id)
            if not ronda:
                return jsonify({'success': False, 'message': 'Ronda não encontrada.'}), 404
            
            if not current_user.is_admin and (ronda.supervisor_id is not None and ronda.supervisor_id != current_user.id):
                 return jsonify({'success': False, 'message': 'Permissão negada para alterar o supervisor desta ronda.'}), 403

            ronda.log_ronda_bruto = log_bruto
            ronda.relatorio_processado = relatorio
            ronda.condominio_id = condominio_obj.id
            ronda.data_plantao_ronda = data_plantao
            ronda.escala_plantao = escala_plantao
            ronda.turno_ronda = turno_ronda
            ronda.supervisor_id = supervisor_id_para_db
            ronda.total_rondas_no_log = total
            ronda.primeiro_evento_log_dt = p_evento
            ronda.ultimo_evento_log_dt = u_evento
            ronda.duracao_total_rondas_minutos = duracao
            if not ronda.data_hora_fim:
                ronda.data_hora_fim = datetime.now(timezone.utc)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ronda atualizada com sucesso!', 'ronda_id': ronda.id}), 200
        else:
            nova_ronda = Ronda(
                data_hora_inicio=p_evento if p_evento else datetime.now(timezone.utc),
                data_hora_fim=datetime.now(timezone.utc), log_ronda_bruto=log_bruto,
                relatorio_processado=relatorio, condominio_id=condominio_obj.id,
                escala_plantao=escala_plantao, data_plantao_ronda=data_plantao,
                turno_ronda=turno_ronda, user_id=current_user.id, supervisor_id=supervisor_id_para_db,
                total_rondas_no_log=total, primeiro_evento_log_dt=p_evento,
                ultimo_evento_log_dt=u_evento, duracao_total_rondas_minutos=duracao
            )
            db.session.add(nova_ronda)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ronda registrada com sucesso!', 'ronda_id': nova_ronda.id}), 201

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

    query = Ronda.query.options(
        db.joinedload(Ronda.condominio_obj), 
        db.joinedload(Ronda.criador), 
        db.joinedload(Ronda.supervisor)
    )
    
    if condominio_filter:
        condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(condominio_filter)).first()
        query = query.filter(Ronda.condominio_id == condominio_obj.id) if condominio_obj else query.filter(literal(False))

    if supervisor_filter_id:
        query = query.filter(Ronda.supervisor_id == supervisor_filter_id)
    
    if turno_filter:
        query = query.filter(Ronda.turno_ronda == turno_filter)

    if status_ronda_filter == 'em_andamento':
        query = query.filter(Ronda.data_hora_fim.is_(None))
    elif status_ronda_filter == 'finalizada':
        query = query.filter(Ronda.data_hora_fim.isnot(None))

    if data_inicio_filter_str:
        try:
            data_inicio = datetime.strptime(data_inicio_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio)
        except ValueError:
            flash('Formato de Data de Início inválido. Use AAAA-MM-DD.', 'danger')
    if data_fim_filter_str:
        try:
            data_fim = datetime.strptime(data_fim_filter_str, '%Y-%m-%d').date()
            query = query.filter(Ronda.data_plantao_ronda <= data_fim)
        except ValueError:
            flash('Formato de Data de Fim inválido. Use AAAA-MM-DD.', 'danger')

    if not current_user.is_admin:
        query = query.filter(
            or_(
                Ronda.supervisor_id == current_user.id,
                Ronda.supervisor_id.is_(None)
            )
        )

    rondas_pagination = query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.data_hora_inicio.desc()).paginate(page=page, per_page=10)

    all_condominios = Condominio.query.order_by(Condominio.nome).all()
    all_supervisors = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
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
    ronda = Ronda.query.options(
        db.joinedload(Ronda.criador), 
        db.joinedload(Ronda.condominio_obj),
        db.joinedload(Ronda.supervisor)
    ).get_or_404(ronda_id)
    
    if not (current_user.is_admin or current_user.is_supervisor):
        flash("Você não tem permissão para visualizar os detalhes desta ronda.", 'danger')
        return redirect(url_for('ronda.listar_rondas'))

    return render_template('ronda_details.html', title=f'Detalhes da Ronda #{ronda.id}', ronda=ronda)


@ronda_bp.route('/rondas/excluir/<int:ronda_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def excluir_ronda(ronda_id):
    ronda_to_delete = Ronda.query.get_or_404(ronda_id)

    if not current_user.is_admin:
        message = 'Você não tem permissão para excluir esta ronda.'
        if request.method == 'DELETE':
            return jsonify({'success': False, 'message': message}), 403
        else:
            flash(message, 'danger')
            return redirect(url_for('ronda.listar_rondas'))

    try:
        db.session.delete(ronda_to_delete)
        db.session.commit()
        message = f'Ronda {ronda_id} excluída com sucesso.'
        if request.method == 'DELETE':
            return jsonify({'success': True, 'message': message}), 200
        else:
            flash(message, 'success')
            return redirect(url_for('ronda.listar_rondas'))
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir ronda {ronda_id}: {e}", exc_info=True)
        message = f'Erro ao excluir ronda {ronda_id}: {str(e)}'
        if request.method == 'DELETE':
            return jsonify({'success': False, 'message': message}), 500
        else:
            flash(message, 'danger')
            return redirect(url_for('ronda.detalhes_ronda', ronda_id=ronda_id))