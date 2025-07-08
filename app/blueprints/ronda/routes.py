import logging
from datetime import datetime, date, timezone, timedelta # Adicionado timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload
from app import db
from app.models import Condominio, Ronda, User, EscalaMensal
from app.forms import TestarRondasForm
from app.services.ronda_logic import processar_log_de_rondas
from app.decorators.admin_required import admin_required

logger = logging.getLogger(__name__)

ronda_bp = Blueprint(
    'ronda',
    __name__,
    template_folder='templates',
    url_prefix='/rondas'
)

def inferir_turno(data_plantao_obj, escala_plantao_str):
    turno_ronda_base = "Indefinido"
    escala_lower = escala_plantao_str.lower() if escala_plantao_str else ""
    if "18h às 06h" in escala_lower or "noturno" in escala_lower:
        turno_ronda_base = "Noturno"
    elif "06h às 18h" in escala_lower or "diurno" in escala_lower:
        turno_ronda_base = "Diurno"
    else:
        current_hour_utc = datetime.now(timezone.utc).hour
        turno_ronda_base = "Diurno" if 6 <= current_hour_utc < 18 else "Noturno"
    
    if data_plantao_obj and turno_ronda_base != "Indefinido":
        return f"{turno_ronda_base} {'Par' if data_plantao_obj.day % 2 == 0 else 'Impar'}"
    
    return escala_plantao_str or "N/A - Turno Indefinido"

@ronda_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_ronda():
    ronda_id = request.args.get('ronda_id', type=int)
    form = TestarRondasForm()
    relatorio_processado_final = None
    title = "Editar Ronda" if ronda_id else "Registrar Nova Ronda Manual"
    
    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        form.nome_condominio.choices = [('', '-- Selecione --')] + [(str(c.id), c.nome) for c in condominios_db] + [('Outro', 'Outro')]
        supervisores_db = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        form.supervisor_id.choices = [('0', '-- Nenhum / Automático --')] + [(str(s.id), s.username) for s in supervisores_db]
    except Exception as e:
        logger.error(f"Erro ao carregar dados para o formulário de ronda: {e}", exc_info=True)
        flash('Erro ao carregar dados. Tente novamente.', 'danger')

    if ronda_id and request.method == 'GET':
        ronda = Ronda.query.options(joinedload(Ronda.condominio), joinedload(Ronda.supervisor)).get_or_404(ronda_id)
        
        if not (current_user.is_admin or (ronda.supervisor and current_user.id == ronda.supervisor.id)):
            flash("Você não tem permissão para editar esta ronda.", 'danger')
            return redirect(url_for('ronda.listar_rondas'))
            
        form.nome_condominio.data = str(ronda.condominio_id)
        form.data_plantao.data = ronda.data_plantao_ronda
        form.escala_plantao.data = ronda.escala_plantao
        form.supervisor_id.data = str(ronda.supervisor_id or '0')
        form.log_bruto_rondas.data = ronda.log_ronda_bruto
        relatorio_processado_final = ronda.relatorio_processado

    if form.validate_on_submit():
        log_bruto = form.log_bruto_rondas.data
        data_plantao_obj = form.data_plantao.data
        escala_plantao_str = form.escala_plantao.data
        condominio_id_sel = form.nome_condominio.data
        nome_condominio_outro_str = form.nome_condominio_outro.data
        
        try:
            nome_condo_para_processar = nome_condominio_outro_str if condominio_id_sel == 'Outro' else dict(form.nome_condominio.choices).get(condominio_id_sel)
            data_plantao_fmt = data_plantao_obj.strftime('%d/%m/%Y') if data_plantao_obj else None

            relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
                log_bruto_rondas_str=log_bruto,
                nome_condominio_str=nome_condo_para_processar,
                data_plantao_manual_str=data_plantao_fmt,
                escala_plantao_str=escala_plantao_str
            )
            relatorio_processado_final = relatorio
            flash('Relatório de ronda processado. Verifique os dados e salve se estiver correto.', 'info')
        except Exception as e:
            flash(f'Erro ao processar o log de rondas: {str(e)}', 'danger')
    
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                label = getattr(form, field).label.text
                flash(f"Erro no campo '{label}': {error}", 'danger')
    
    ronda_data_to_save = {'ronda_id': ronda_id}
    return render_template('ronda/relatorio.html',
                           title=title,
                           form=form,
                           relatorio_processado=relatorio_processado_final,
                           ronda_data_to_save=ronda_data_to_save)

@ronda_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_ronda():
    if not (current_user.is_admin or current_user.is_supervisor):
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos.'}), 400

    try:
        ronda_id_raw = data.get('ronda_id')
        ronda_id = int(ronda_id_raw) if ronda_id_raw and str(ronda_id_raw).isdigit() and int(ronda_id_raw) > 0 else None
        
        log_bruto = data.get('log_bruto')
        condominio_id_str = data.get('condominio_id')
        nome_condominio_outro = data.get('nome_condominio_outro', '').strip()
        data_plantao_str = data.get('data_plantao')
        escala_plantao = data.get('escala_plantao')
        supervisor_id_manual_str = data.get('supervisor_id')
        
        condominio_obj = None
        if condominio_id_str == 'Outro':
            if not nome_condominio_outro:
                return jsonify({'success': False, 'message': 'O nome do condomínio é obrigatório.'}), 400
            condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(nome_condominio_outro)).first()
            if not condominio_obj:
                condominio_obj = Condominio(nome=nome_condominio_outro)
                db.session.add(condominio_obj)
                db.session.flush()
        elif condominio_id_str and condominio_id_str.isdigit():
            condominio_obj = db.get_or_404(Condominio, int(condominio_id_str))
        
        if not all([log_bruto, condominio_obj, data_plantao_str, escala_plantao]):
            return jsonify({'success': False, 'message': 'Dados essenciais ausentes.'}), 400

        data_plantao = date.fromisoformat(data_plantao_str)
        
        relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
            log_bruto_rondas_str=log_bruto, nome_condominio_str=condominio_obj.nome,
            data_plantao_manual_str=data_plantao.strftime('%d/%m/%Y'), escala_plantao_str=escala_plantao)
        
        if total == 0:
            return jsonify({'success': False, 'message': 'Não foi possível salvar: Nenhum evento de ronda válido foi encontrado no log fornecido.'}), 400

        turno_ronda = inferir_turno(data_plantao, escala_plantao)
        
        supervisor_id_para_db = int(supervisor_id_manual_str) if supervisor_id_manual_str and supervisor_id_manual_str != '0' else None
        if not supervisor_id_para_db:
            escala = EscalaMensal.query.filter_by(ano=data_plantao.year, mes=data_plantao.month, nome_turno=turno_ronda).first()
            if escala:
                supervisor_id_para_db = escala.supervisor_id

        if ronda_id:
            ronda = db.get_or_404(Ronda, ronda_id)
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
            mensagem_sucesso = 'Ronda atualizada com sucesso!'
        else:
            ronda_existente = Ronda.query.filter_by(condominio_id=condominio_obj.id, data_plantao_ronda=data_plantao, turno_ronda=turno_ronda).first()
            if ronda_existente:
                return jsonify({'success': False, 'message': f'Já existe uma ronda para este condomínio, data e turno (ID: {ronda_existente.id}).'}), 409
            
            ronda = Ronda(
                log_ronda_bruto=log_bruto,
                relatorio_processado=relatorio,
                condominio_id=condominio_obj.id,
                escala_plantao=escala_plantao,
                data_plantao_ronda=data_plantao,
                turno_ronda=turno_ronda,
                user_id=current_user.id,
                supervisor_id=supervisor_id_para_db,
                total_rondas_no_log=total,
                primeiro_evento_log_dt=p_evento,
                ultimo_evento_log_dt=u_evento,
                duracao_total_rondas_minutos=duracao,
                data_hora_inicio=datetime.now(timezone.utc)
            )
            db.session.add(ronda)
            mensagem_sucesso = 'Ronda registrada com sucesso!'
            
        db.session.commit()
        return jsonify({'success': True, 'message': mensagem_sucesso, 'ronda_id': ronda.id}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar/finalizar ronda: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro interno ao salvar ronda: {str(e)}'}), 500

@ronda_bp.route('/historico', methods=['GET'])
@login_required
def listar_rondas():
    page = request.args.get('page', 1, type=int)
    
    filter_params = {
        'condominio': request.args.get('condominio'),
        'supervisor': request.args.get('supervisor', type=int),
        'data_inicio': request.args.get('data_inicio'),
        'data_fim': request.args.get('data_fim'),
        'turno': request.args.get('turno'),
    }
    active_filter_params = {k: v for k, v in filter_params.items() if v not in [None, '']}
    
    query = Ronda.query.options(joinedload(Ronda.condominio), joinedload(Ronda.supervisor))

    if active_filter_params.get('condominio'):
        query = query.join(Condominio).filter(Condominio.nome == active_filter_params['condominio'])
    if active_filter_params.get('supervisor'):
        query = query.filter(Ronda.supervisor_id == active_filter_params['supervisor'])

    # --- CORREÇÃO E MELHORIA NOS FILTROS ---
    if active_filter_params.get('turno'):
        query = query.filter(Ronda.turno_ronda == active_filter_params['turno'])
        
    data_inicio_obj, data_fim_obj = None, None
    if active_filter_params.get('data_inicio'):
        try:
            data_inicio_obj = date.fromisoformat(active_filter_params['data_inicio'])
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio_obj)
        except (ValueError, TypeError):
            flash('Formato de data de início inválido.', 'warning')
    
    if active_filter_params.get('data_fim'):
        try:
            data_fim_obj = date.fromisoformat(active_filter_params['data_fim'])
            query = query.filter(Ronda.data_plantao_ronda <= data_fim_obj)
        except (ValueError, TypeError):
            flash('Formato de data de fim inválido.', 'warning')
    
    # --- INÍCIO DO CÁLCULO DE KPIs ---
    total_rondas = query.with_entities(func.sum(Ronda.total_rondas_no_log)).scalar() or 0
    soma_duracao = query.with_entities(func.sum(Ronda.duracao_total_rondas_minutos)).scalar() or 0
    
    duracao_media = round(soma_duracao / total_rondas, 2) if total_rondas > 0 else 0
    
    media_rondas_dia = "N/A"
    if data_inicio_obj and data_fim_obj:
        num_dias = (data_fim_obj - data_inicio_obj).days + 1
        if num_dias > 0:
            media_rondas_dia = round(total_rondas / num_dias, 1)

    top_supervisor_q = query.join(User, Ronda.supervisor_id == User.id).group_by(User.username).with_entities(User.username, func.sum(Ronda.total_rondas_no_log)).order_by(func.sum(Ronda.total_rondas_no_log).desc()).first()
    supervisor_mais_ativo = top_supervisor_q[0] if top_supervisor_q else "N/A"
    # --- FIM DO CÁLCULO DE KPIs ---

    rondas_pagination = query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.id.desc()).paginate(page=page, per_page=10)
    
    selected_values = {f"selected_{key}": val for key, val in active_filter_params.items()}

    return render_template(
        'ronda/list.html', 
        title='Histórico de Rondas', 
        rondas_pagination=rondas_pagination,
        filter_params=active_filter_params,
        condominios=Condominio.query.order_by(Condominio.nome).all(),
        supervisors=User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all(),
        turnos=['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar'],
        total_rondas=total_rondas,
        duracao_media=duracao_media,
        media_rondas_dia=media_rondas_dia,
        supervisor_mais_ativo=supervisor_mais_ativo,
        **selected_values
    )

@ronda_bp.route('/detalhes/<int:ronda_id>')
@login_required
def detalhes_ronda(ronda_id):
    ronda = Ronda.query.options(joinedload(Ronda.condominio), joinedload(Ronda.supervisor)).get_or_404(ronda_id)
    return render_template('ronda/details.html', title=f'Detalhes da Ronda #{ronda.id}', ronda=ronda)

@ronda_bp.route('/excluir/<int:ronda_id>', methods=['POST'])
@login_required
@admin_required
def excluir_ronda(ronda_id):
    ronda = db.get_or_404(Ronda, ronda_id)
    try:
        db.session.delete(ronda)
        db.session.commit()
        flash(f'Ronda #{ronda.id} excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir ronda {ronda_id}: {e}", exc_info=True)
        flash(f'Erro ao excluir ronda: {str(e)}', 'danger')
    return redirect(url_for('ronda.listar_rondas'))