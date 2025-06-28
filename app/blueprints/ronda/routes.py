# app/blueprints/ronda/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_
from datetime import datetime, date, timezone
from app import db
from app.models import Condominio, Ronda, User, EscalaMensal, Ocorrencia, OcorrenciaTipo, OrgaoPublico
from app.forms import TestarRondasForm, OcorrenciaForm, OcorrenciaTipoForm, OrgaoPublicoForm
from app.services.ronda_logic import processar_log_de_rondas
from app.decorators.admin_required import admin_required
import logging

logger = logging.getLogger(__name__)

ronda_bp = Blueprint('ronda', __name__, template_folder='templates')

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def inferir_turno(data_plantao_obj, escala_plantao_str):
    """Infere o turno da ronda com base na data do plantão e na escala."""
    turno_ronda_base = "Indefinido"
    escala_lower = escala_plantao_str.lower() if escala_plantao_str else ""
    if "18h às 06h" in escala_lower or "noturno" in escala_lower:
        turno_ronda_base = "Noturno"
    elif "06h às 18h" in escala_lower or "diurno" in escala_lower:
        turno_ronda_base = "Diurno"
    else:
        current_hour_utc = datetime.now(timezone.utc).hour
        if 6 <= current_hour_utc < 18:
            turno_ronda_base = "Diurno"
        else:
            turno_ronda_base = "Noturno"
    
    if data_plantao_obj and turno_ronda_base != "Indefinido":
        return f"{turno_ronda_base} {'Par' if data_plantao_obj.day % 2 == 0 else 'Impar'}"
    
    return escala_plantao_str or "N/A - Turno Indefinido"


# ==============================================================================
# ROTAS DE GESTÃO DE RONDAS
# ==============================================================================

@ronda_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_ronda():
    """Exibe a página para registrar/editar uma ronda existente."""
    ronda_id = request.args.get('ronda_id', type=int)
    form = TestarRondasForm()
    relatorio_processado_final = None
    title = "Editar Ronda" if ronda_id else "Registrar Nova Ronda"
    ronda_data_to_save = {'ronda_id': ronda_id if ronda_id else None}
    
    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        form.nome_condominio.choices = [('', '-- Selecione --')] + [(str(c.id), c.nome) for c in condominios_db] + [('Outro', 'Outro')]
        supervisores_db = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        form.supervisor_id.choices = [('0', '-- Nenhum / Automático --')] + [(s.id, s.username) for s in supervisores_db]
    except Exception as e:
        logger.error(f"Erro ao carregar dados para o formulário de ronda: {e}", exc_info=True)
        flash('Erro ao carregar dados. Tente novamente.', 'danger')

    if ronda_id and request.method == 'GET':
        ronda = db.get_or_404(Ronda, ronda_id)
        if not (current_user.is_admin or (ronda.supervisor and current_user.id == ronda.supervisor.id)):
            flash("Você não tem permissão para editar esta ronda.", 'danger')
            return redirect(url_for('ronda.listar_rondas'))
        form.nome_condominio.data = str(ronda.condominio_id)
        form.data_plantao.data = ronda.data_plantao_ronda
        form.escala_plantao.data = ronda.escala_plantao
        form.supervisor_id.data = str(ronda.supervisor_id or 0)
        form.log_bruto_rondas.data = ronda.log_ronda_bruto
        relatorio_processado_final = ronda.relatorio_processado
    
    return render_template('ronda/relatorio.html',
                           title=title,
                           form=form,
                           relatorio_processado=relatorio_processado_final,
                           ronda_data_to_save=ronda_data_to_save)

@ronda_bp.route('/historico', methods=['GET'])
@login_required
def listar_rondas():
    """Exibe o histórico de rondas com filtros."""
    page = request.args.get('page', 1, type=int)
    
    filter_params = {
        'condominio': request.args.get('condominio'),
        'supervisor': request.args.get('supervisor', type=int),
        'data_inicio': request.args.get('data_inicio'),
        'data_fim': request.args.get('data_fim'),
        'turno': request.args.get('turno'),
        'status_ocorrencia': request.args.get('status_ocorrencia')
    }
    active_filter_params = {k: v for k, v in filter_params.items() if v is not None and v != ''}
    
    query = Ronda.query.options(db.joinedload(Ronda.condominio_obj), db.joinedload(Ronda.supervisor), db.joinedload(Ronda.ocorrencia))

    if active_filter_params.get('condominio'):
        query = query.join(Condominio).filter(Condominio.nome == active_filter_params['condominio'])
    if active_filter_params.get('supervisor'):
        query = query.filter(Ronda.supervisor_id == active_filter_params['supervisor'])
    if active_filter_params.get('status_ocorrencia') == 'com_ocorrencia':
        query = query.filter(Ronda.ocorrencia.has())
    elif active_filter_params.get('status_ocorrencia') == 'sem_ocorrencia':
        query = query.filter(Ronda.ocorrencia.is_(None))

    if not current_user.is_admin:
        query = query.filter(or_(Ronda.supervisor_id == current_user.id, Ronda.supervisor_id.is_(None)))
    
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
        **selected_values
    )

# --- ROTA RESTAURADA ---
@ronda_bp.route('/detalhes/<int:ronda_id>')
@login_required
def detalhes_ronda(ronda_id):
    """Exibe os detalhes de uma ronda específica."""
    ronda = db.get_or_404(Ronda, ronda_id)
    # Permissão para ver os detalhes da ronda (pode ser ajustada)
    if not (current_user.is_admin or (ronda.supervisor and current_user.id == ronda.supervisor.id) or current_user.id == ronda.user_id):
        flash("Você não tem permissão para visualizar os detalhes desta ronda.", 'danger')
        return redirect(url_for('ronda.listar_rondas'))
    return render_template('ronda/details.html', title=f'Detalhes da Ronda #{ronda.id}', ronda=ronda)


# ==============================================================================
# ROTAS DE GESTÃO DE OCORRÊNCIAS
# ==============================================================================

@ronda_bp.route('/ocorrencia/registrar_direto', methods=['GET', 'POST'])
@login_required
def registrar_ocorrencia_direto():
    """Exibe um formulário unificado para criar uma Ronda e uma Ocorrência 
    a partir do texto processado na página inicial.
    """
    form_ronda = TestarRondasForm() 
    form_ocorrencia = OcorrenciaForm()

    try:
        form_ronda.nome_condominio.choices = [('', '-- Selecione --')] + [(str(c.id), c.nome) for c in Condominio.query.order_by(Condominio.nome).all()] + [('Outro', 'Outro')]
        form_ronda.supervisor_id.choices = [('0', '-- Nenhum / Automático --')] + [(s.id, s.username) for s in User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()]
        form_ocorrencia.ocorrencia_tipo_id.choices = [(t.id, t.nome) for t in OcorrenciaTipo.query.order_by('nome').all()]
        form_ocorrencia.orgaos_acionados.choices = [(o.id, o.nome) for o in OrgaoPublico.query.order_by('nome').all()]
    except Exception as e:
        logger.error(f"Erro ao carregar dados para o formulário de ocorrência direta: {e}", exc_info=True)
        flash('Erro ao carregar dados de suporte. Tente novamente.', 'danger')

    if form_ronda.validate_on_submit() and form_ocorrencia.validate_on_submit():
        try:
            condominio_id_str = form_ronda.nome_condominio.data
            nome_condominio_outro = form_ronda.nome_condominio_outro.data.strip()
            data_plantao = form_ronda.data_plantao.data
            escala_plantao = form_ronda.escala_plantao.data
            log_bruto = request.form.get('log_bruto_hidden') 
            relatorio_processado = request.form.get('relatorio_final_hidden')
            
            condominio_obj = None
            if condominio_id_str == 'Outro':
                if not nome_condominio_outro:
                    flash('O nome do condomínio é obrigatório ao selecionar "Outro".', 'danger')
                    return redirect(url_for('ronda.registrar_ocorrencia_direto'))
                condominio_obj = Condominio.query.filter(func.lower(Condominio.nome) == func.lower(nome_condominio_outro)).first()
                if not condominio_obj:
                    condominio_obj = Condominio(nome=nome_condominio_outro)
                    db.session.add(condominio_obj)
                    db.session.flush()
            else:
                condominio_obj = db.get_or_404(Condominio, int(condominio_id_str))
            
            nova_ronda = Ronda(
                log_ronda_bruto=log_bruto, relatorio_processado=relatorio_processado,
                condominio_id=condominio_obj.id, data_plantao_ronda=data_plantao,
                escala_plantao=escala_plantao, turno_ronda=inferir_turno(data_plantao, escala_plantao),
                user_id=current_user.id
            )
            db.session.add(nova_ronda)
            db.session.flush()

            nova_ocorrencia = Ocorrencia(
                ronda_id=nova_ronda.id, relatorio_final=relatorio_processado,
                ocorrencia_tipo_id=form_ocorrencia.ocorrencia_tipo_id.data, status=form_ocorrencia.status.data,
                endereco_especifico=form_ocorrencia.endereco_especifico.data, registrado_por_user_id=current_user.id
            )
            orgaos_selecionados = OrgaoPublico.query.filter(OrgaoPublico.id.in_(form_ocorrencia.orgaos_acionados.data)).all()
            nova_ocorrencia.orgaos_acionados.extend(orgaos_selecionados)
            db.session.add(nova_ocorrencia)

            db.session.commit()
            flash('Ocorrência oficial registrada com sucesso!', 'success')
            return redirect(url_for('ronda.detalhes_ocorrencia', ocorrencia_id=nova_ocorrencia.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar ocorrência direta: {e}", exc_info=True)
            flash(f"Ocorreu um erro ao salvar: {e}", 'danger')

    return render_template('ocorrencia/form_direto.html', title="Registrar Ocorrência Oficial", form_ronda=form_ronda, form_ocorrencia=form_ocorrencia)

@ronda_bp.route('/ocorrencia/registrar/<int:ronda_id>', methods=['GET', 'POST'])
@login_required
def registrar_ocorrencia(ronda_id):
    """Registra uma nova ocorrência a partir de uma ronda JÁ EXISTENTE."""
    ronda = db.get_or_404(Ronda, ronda_id)
    if ronda.ocorrencia:
        flash('Esta ronda já possui uma ocorrência registrada.', 'warning')
        return redirect(url_for('ronda.detalhes_ocorrencia', ocorrencia_id=ronda.ocorrencia.id))

    form = OcorrenciaForm()
    form.ocorrencia_tipo_id.choices = [(t.id, t.nome) for t in OcorrenciaTipo.query.order_by('nome').all()]
    form.orgaos_acionados.choices = [(o.id, o.nome) for o in OrgaoPublico.query.order_by('nome').all()]

    if form.validate_on_submit():
        nova_ocorrencia = Ocorrencia(
            ronda_id=ronda.id, relatorio_final=form.relatorio_final.data,
            ocorrencia_tipo_id=form.ocorrencia_tipo_id.data, status=form.status.data,
            endereco_especifico=form.ocorrencia.endereco_especifico.data, registrado_por_user_id=current_user.id
        )
        orgaos_selecionados = OrgaoPublico.query.filter(OrgaoPublico.id.in_(form.orgaos_acionados.data)).all()
        nova_ocorrencia.orgaos_acionados.extend(orgaos_selecionados)
        db.session.add(nova_ocorrencia)
        db.session.commit()
        flash('Ocorrência registrada com sucesso!', 'success')
        return redirect(url_for('ronda.detalhes_ocorrencia', ocorrencia_id=nova_ocorrencia.id))
    
    elif request.method == 'GET':
        form.relatorio_final.data = ronda.relatorio_processado

    return render_template('ocorrencia/form.html', title='Registrar Ocorrência da Ronda #' + str(ronda.id), form=form, ronda=ronda)


@ronda_bp.route('/ocorrencia/detalhes/<int:ocorrencia_id>')
@login_required
def detalhes_ocorrencia(ocorrencia_id):
    """Exibe os detalhes de uma ocorrência."""
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    return render_template('ocorrencia/details.html', title=f'Detalhes da Ocorrência #{ocorrencia.id}', ocorrencia=ocorrencia)

# ==============================================================================
# ROTAS DE GERENCIAMENTO (CRUD)
# ==============================================================================
@ronda_bp.route('/gerenciamento/tipos_ocorrencia', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_tipos_ocorrencia():
    """Página para gerenciar os tipos de ocorrência."""
    form = OcorrenciaTipoForm()
    if form.validate_on_submit():
        novo_tipo = OcorrenciaTipo(nome=form.nome.data, descricao=form.descricao.data)
        db.session.add(novo_tipo)
        db.session.commit()
        flash('Novo tipo de ocorrência adicionado!', 'success')
        return redirect(url_for('ronda.gerenciar_tipos_ocorrencia'))
    
    tipos = OcorrenciaTipo.query.order_by('nome').all()
    return render_template('gerenciamento/tipos_ocorrencia.html', title="Gerenciar Tipos de Ocorrência", form=form, tipos=tipos)

@ronda_bp.route('/gerenciamento/tipos_ocorrencia/editar/<int:tipo_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_tipo_ocorrencia(tipo_id):
    """Edita um tipo de ocorrência existente."""
    tipo = db.get_or_404(OcorrenciaTipo, tipo_id)
    form = OcorrenciaTipoForm(obj=tipo)
    if form.validate_on_submit():
        tipo.nome = form.nome.data
        tipo.descricao = form.descricao.data
        db.session.commit()
        flash('Tipo de ocorrência atualizado com sucesso!', 'success')
        return redirect(url_for('ronda.gerenciar_tipos_ocorrencia'))
    return render_template('gerenciamento/editar_item.html', form=form, title=f"Editar Tipo: {tipo.nome}", cancel_url=url_for('ronda.gerenciar_tipos_ocorrencia'))

@ronda_bp.route('/gerenciamento/tipos_ocorrencia/excluir/<int:tipo_id>', methods=['POST'])
@login_required
@admin_required
def excluir_tipo_ocorrencia(tipo_id):
    """Exclui um tipo de ocorrência."""
    tipo = db.get_or_404(OcorrenciaTipo, tipo_id)
    if tipo.ocorrencias:
        flash('Não é possível excluir um tipo que já está em uso por ocorrências existentes.', 'danger')
    else:
        db.session.delete(tipo)
        db.session.commit()
        flash('Tipo de ocorrência excluído com sucesso.', 'success')
    return redirect(url_for('ronda.gerenciar_tipos_ocorrencia'))

@ronda_bp.route('/gerenciamento/orgaos_publicos', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_orgaos_publicos():
    """Página para gerenciar os órgãos públicos."""
    form = OrgaoPublicoForm()
    if form.validate_on_submit():
        novo_orgao = OrgaoPublico(nome=form.nome.data, contato=form.contato.data)
        db.session.add(novo_orgao)
        db.session.commit()
        flash('Novo órgão público adicionado!', 'success')
        return redirect(url_for('ronda.gerenciar_orgaos_publicos'))
        
    orgaos = OrgaoPublico.query.order_by('nome').all()
    return render_template('gerenciamento/orgaos_publicos.html', title="Gerenciar Órgãos Públicos", form=form, orgaos=orgaos)

@ronda_bp.route('/gerenciamento/orgaos_publicos/editar/<int:orgao_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_orgao_publico(orgao_id):
    """Edita um órgão público existente."""
    orgao = db.get_or_404(OrgaoPublico, orgao_id)
    form = OrgaoPublicoForm(obj=orgao)
    if form.validate_on_submit():
        orgao.nome = form.nome.data
        orgao.contato = form.contato.data
        db.session.commit()
        flash('Órgão público atualizado com sucesso!', 'success')
        return redirect(url_for('ronda.gerenciar_orgaos_publicos'))
    
    return render_template('gerenciamento/editar_item_orgao.html', form=form, title=f"Editar Órgão: {orgao.nome}", cancel_url=url_for('ronda.gerenciar_orgaos_publicos'))

@ronda_bp.route('/gerenciamento/orgaos_publicos/excluir/<int:orgao_id>', methods=['POST'])
@login_required
@admin_required
def excluir_orgao_publico(orgao_id):
    """Exclui um órgão público."""
    orgao = db.get_or_404(OrgaoPublico, orgao_id)
    if orgao.ocorrencias:
        flash('Não é possível excluir um órgão que já está em uso por ocorrências existentes.', 'danger')
    else:
        db.session.delete(orgao)
        db.session.commit()
        flash('Órgão público excluído com sucesso.', 'success')
    return redirect(url_for('ronda.gerenciar_orgaos_publicos'))
