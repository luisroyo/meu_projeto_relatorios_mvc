# app/blueprints/ocorrencia/routes.py

import logging
# CORREÇÃO: Adicionado imports de timezone e timedelta
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Ocorrencia, OcorrenciaTipo, Colaborador, OrgaoPublico, Condominio, User
from app.forms import OcorrenciaForm

logger = logging.getLogger(__name__)

ocorrencia_bp = Blueprint(
    'ocorrencia',
    __name__,
    template_folder='templates',
    url_prefix='/ocorrencias'
)

# Coerce customizado para aceitar '' como None
def optional_int_coerce(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def populate_ocorrencia_form_choices(form):
    """Preenche as opções dos campos de seleção do formulário de ocorrência."""
    form.condominio_id.choices = [('', '-- Selecione um Condomínio --')] + [(str(c.id), c.nome) for c in Condominio.query.order_by('nome').all()]
    form.ocorrencia_tipo_id.choices = [('', '-- Selecione um Tipo --')] + [(str(t.id), t.nome) for t in OcorrenciaTipo.query.order_by('nome').all()]
    form.orgaos_acionados.choices = [(str(o.id), o.nome) for o in OrgaoPublico.query.order_by('nome').all()]
    form.colaboradores_envolvidos.choices = [(str(col.id), col.nome_completo) for col in Colaborador.query.filter_by(status='Ativo').order_by('nome_completo').all()]
    form.supervisor_id.choices = [('', '-- Selecione um Supervisor --')] + [(str(s.id), s.username) for s in User.query.filter_by(is_supervisor=True, is_approved=True).order_by('username').all()]

# Decorador para controle de permissão de edição da ocorrência
def pode_editar_ocorrencia(f):
    @wraps(f)
    def decorated_function(ocorrencia_id, *args, **kwargs):
        ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
        if not (current_user.is_admin or current_user.id == ocorrencia.registrado_por_user_id):
            flash('Você não tem permissão para editar esta ocorrência.', 'danger')
            return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=ocorrencia.id))
        return f(ocorrencia_id, *args, **kwargs)
    return decorated_function


@ocorrencia_bp.route('/historico')
@login_required
def listar_ocorrencias():
    page = request.args.get('page', 1, type=int)
    query = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.tipo),
        db.joinedload(Ocorrencia.registrado_por),
        db.joinedload(Ocorrencia.condominio),
        db.joinedload(Ocorrencia.supervisor)
    ).order_by(Ocorrencia.data_hora_ocorrencia.desc())

    ocorrencias_pagination = query.paginate(page=page, per_page=15, error_out=False)
    return render_template(
        'ocorrencia/list.html',
        title='Histórico de Ocorrências',
        ocorrencias_pagination=ocorrencias_pagination
    )


@ocorrencia_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_ocorrencia():
    form = OcorrenciaForm()

    form.condominio_id.coerce = optional_int_coerce
    form.ocorrencia_tipo_id.coerce = optional_int_coerce
    form.supervisor_id.coerce = optional_int_coerce
    form.orgaos_acionados.coerce = optional_int_coerce
    form.colaboradores_envolvidos.coerce = optional_int_coerce

    populate_ocorrencia_form_choices(form)

    if request.method == 'GET':
        relatorio_get = request.args.get('relatorio_final')
        if relatorio_get:
            form.relatorio_final.data = relatorio_get
        form.data_hora_ocorrencia.data = datetime.now()

    if form.validate_on_submit():
        try:
            tipo_ocorrencia_id = None
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter(OcorrenciaTipo.nome.ilike(form.novo_tipo_ocorrencia.data.strip())).first()
                if tipo_existente:
                    tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(nome=form.novo_tipo_ocorrencia.data.strip())
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            else:
                tipo_ocorrencia_id = form.ocorrencia_tipo_id.data

            # CORREÇÃO DE FUSO HORÁRIO: Converte a data/hora local do formulário para UTC
            naive_datetime = form.data_hora_ocorrencia.data
            local_timezone = timezone(timedelta(hours=-3)) # Fuso de Brasília (BRT)
            aware_local_datetime = naive_datetime.replace(tzinfo=local_timezone)
            utc_datetime = aware_local_datetime.astimezone(timezone.utc)

            nova_ocorrencia = Ocorrencia(
                condominio_id=form.condominio_id.data,
                data_hora_ocorrencia=utc_datetime, # Salva a data/hora em UTC
                turno=form.turno.data,
                relatorio_final=form.relatorio_final.data,
                status=form.status.data,
                endereco_especifico=form.endereco_especifico.data,
                ocorrencia_tipo_id=tipo_ocorrencia_id,
                registrado_por_user_id=current_user.id,
                supervisor_id=form.supervisor_id.data
            )

            if form.orgaos_acionados.data:
                orgaos = OrgaoPublico.query.filter(OrgaoPublico.id.in_(form.orgaos_acionados.data)).all()
                nova_ocorrencia.orgaos_acionados.extend(orgaos)

            if form.colaboradores_envolvidos.data:
                colaboradores = Colaborador.query.filter(Colaborador.id.in_(form.colaboradores_envolvidos.data)).all()
                nova_ocorrencia.colaboradores_envolvidos.extend(colaboradores)

            db.session.add(nova_ocorrencia)
            db.session.commit()

            flash('Ocorrência registrada com sucesso!', 'success')
            return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=nova_ocorrencia.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar a ocorrência: {e}', 'danger')
            logger.error(f"Erro ao salvar nova ocorrência: {e}", exc_info=True)

    return render_template('ocorrencia/form_direto.html', title='Registrar Nova Ocorrência', form=form)


@ocorrencia_bp.route('/detalhes/<int:ocorrencia_id>')
@login_required
def detalhes_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    return render_template('ocorrencia/details.html', title=f'Detalhes da Ocorrência #{ocorrencia.id}', ocorrencia=ocorrencia)


@ocorrencia_bp.route('/editar/<int:ocorrencia_id>', methods=['GET', 'POST'])
@login_required
@pode_editar_ocorrencia
def editar_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    form = OcorrenciaForm(obj=ocorrencia)

    form.condominio_id.coerce = optional_int_coerce
    form.ocorrencia_tipo_id.coerce = optional_int_coerce
    form.supervisor_id.coerce = optional_int_coerce
    form.orgaos_acionados.coerce = optional_int_coerce
    form.colaboradores_envolvidos.coerce = optional_int_coerce

    populate_ocorrencia_form_choices(form)

    if form.validate_on_submit():
        try:
            tipo_ocorrencia_id = None
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter(OcorrenciaTipo.nome.ilike(form.novo_tipo_ocorrencia.data.strip())).first()
                if tipo_existente:
                    tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(nome=form.novo_tipo_ocorrencia.data.strip())
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            else:
                tipo_ocorrencia_id = form.ocorrencia_tipo_id.data

            # CORREÇÃO DE FUSO HORÁRIO: Converte a data/hora local do formulário para UTC
            naive_datetime = form.data_hora_ocorrencia.data
            local_timezone = timezone(timedelta(hours=-3)) # Fuso de Brasília (BRT)
            aware_local_datetime = naive_datetime.replace(tzinfo=local_timezone)
            utc_datetime = aware_local_datetime.astimezone(timezone.utc)

            ocorrencia.condominio_id = form.condominio_id.data
            ocorrencia.data_hora_ocorrencia = utc_datetime # Salva a data/hora em UTC
            ocorrencia.turno = form.turno.data
            ocorrencia.relatorio_final = form.relatorio_final.data
            ocorrencia.status = form.status.data
            ocorrencia.endereco_especifico = form.endereco_especifico.data
            ocorrencia.ocorrencia_tipo_id = tipo_ocorrencia_id
            ocorrencia.supervisor_id = form.supervisor_id.data

            ocorrencia.orgaos_acionados.clear()
            ocorrencia.colaboradores_envolvidos.clear()

            if form.orgaos_acionados.data:
                orgaos = OrgaoPublico.query.filter(OrgaoPublico.id.in_(form.orgaos_acionados.data)).all()
                ocorrencia.orgaos_acionados.extend(orgaos)

            if form.colaboradores_envolvidos.data:
                colaboradores = Colaborador.query.filter(Colaborador.id.in_(form.colaboradores_envolvidos.data)).all()
                ocorrencia.colaboradores_envolvidos.extend(colaboradores)

            db.session.commit()
            flash('Ocorrência atualizada com sucesso!', 'success')
            return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=ocorrencia.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a ocorrência: {e}', 'danger')
            logger.error(f"Erro ao editar ocorrência {ocorrencia_id}: {e}", exc_info=True)

    if request.method == 'GET':
        form.orgaos_acionados.data = [str(o.id) for o in ocorrencia.orgaos_acionados]
        form.colaboradores_envolvidos.data = [str(c.id) for c in ocorrencia.colaboradores_envolvidos]

    return render_template('ocorrencia/form_direto.html', title=f'Editar Ocorrência #{ocorrencia.id}', form=form, ocorrencia_id=ocorrencia.id)


@ocorrencia_bp.route('/orgao/add', methods=['POST'])
@login_required
def add_orgao_publico():
    data = request.get_json()
    if not data or not data.get('nome'):
        return jsonify({'success': False, 'message': 'O nome do órgão é obrigatório.'}), 400

    nome_orgao = data['nome'].strip()
    existente = OrgaoPublico.query.filter_by(nome=nome_orgao).first()
    if existente:
        return jsonify({'success': False, 'message': 'Este órgão público já existe.'}), 409

    try:
        novo_orgao = OrgaoPublico(nome=nome_orgao)
        db.session.add(novo_orgao)
        db.session.commit()
        return jsonify({
            'success': True,
            'id': novo_orgao.id,
            'nome': novo_orgao.nome
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar novo órgão: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Erro interno ao salvar o órgão.'}), 500


@ocorrencia_bp.route('/colaborador/add', methods=['POST'])
@login_required
def add_colaborador():
    data = request.get_json()
    if not data or not data.get('nome_completo'):
        return jsonify({'success': False, 'message': 'O nome do colaborador é obrigatório.'}), 400

    nome_colaborador = data['nome_completo'].strip()
    existente = Colaborador.query.filter_by(nome_completo=nome_colaborador).first()
    if existente:
        return jsonify({'success': False, 'message': 'Este colaborador já existe.'}), 409

    try:
        novo_colaborador = Colaborador(nome_completo=nome_colaborador, status='Ativo')
        db.session.add(novo_colaborador)
        db.session.commit()
        return jsonify({
            'success': True,
            'id': novo_colaborador.id,
            'nome_completo': novo_colaborador.nome_completo
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar novo colaborador: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Erro interno ao salvar o colaborador.'}), 500
