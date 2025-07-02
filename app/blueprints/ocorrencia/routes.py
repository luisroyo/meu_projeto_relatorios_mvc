# app/blueprints/ocorrencia/routes.py

import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
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

def populate_ocorrencia_form_choices(form):
    form.condominio_id.choices = [(0, '-- Selecione um Condomínio --')] + [(c.id, c.nome) for c in Condominio.query.order_by('nome').all()]
    form.ocorrencia_tipo_id.choices = [(0, '-- Selecione um Tipo --')] + [(t.id, t.nome) for t in OcorrenciaTipo.query.order_by('nome').all()]
    form.orgaos_acionados.choices = [(o.id, o.nome) for o in OrgaoPublico.query.order_by('nome').all()]
    form.colaboradores_envolvidos.choices = [(col.id, col.nome_completo) for col in Colaborador.query.filter_by(status='Ativo').order_by('nome_completo').all()]

    # NOVO: adiciona lista de supervisores no campo supervisor_id do form
    supervisores = User.query.filter_by(is_supervisor=True).order_by(User.username).all()
    form.supervisor_id.choices = [(0, '-- Selecione um Supervisor --')] + [(s.id, s.username) for s in supervisores]

@ocorrencia_bp.route('/historico')
@login_required
def listar_ocorrencias():
    page = request.args.get('page', 1, type=int)
    query = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.tipo),
        db.joinedload(Ocorrencia.registrado_por),
        db.joinedload(Ocorrencia.condominio),
        db.joinedload(Ocorrencia.supervisor)
    ).order_by(Ocorrencia.data_ocorrencia.desc())
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
    populate_ocorrencia_form_choices(form)

    relatorio_get = request.args.get('relatorio_final')
    if relatorio_get and request.method == 'GET':
        form.relatorio_final.data = relatorio_get

    if form.validate_on_submit():
        try:
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter_by(nome=form.novo_tipo_ocorrencia.data.strip()).first()
                if tipo_existente:
                    tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(nome=form.novo_tipo_ocorrencia.data.strip())
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            else:
                tipo_ocorrencia_id = form.ocorrencia_tipo_id.data

            # pega o supervisor_id do form, se for zero, trata como None
            supervisor_id = form.supervisor_id.data
            if supervisor_id == 0:
                supervisor_id = None

            nova_ocorrencia = Ocorrencia(
                condominio_id=form.condominio_id.data,
                data_ocorrencia=form.data_plantao.data,
                turno=form.turno.data,
                relatorio_final=form.relatorio_final.data,
                status=form.status.data,
                ocorrencia_tipo_id=tipo_ocorrencia_id,
                registrado_por_user_id=current_user.id,
                supervisor_id=supervisor_id
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
    ocorrencia = db.session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('ocorrencia.listar_ocorrencias'))
    return render_template('ocorrencia/details.html', title=f'Detalhes da Ocorrência #{ocorrencia.id}', ocorrencia=ocorrencia)


@ocorrencia_bp.route('/editar/<int:ocorrencia_id>', methods=['GET', 'POST'])
@login_required
def editar_ocorrencia(ocorrencia_id):
    ocorrencia = db.session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('ocorrencia.listar_ocorrencias'))

    if not (current_user.is_admin or current_user.id == ocorrencia.registrado_por_user_id):
        flash('Você não tem permissão para editar esta ocorrência.', 'danger')
        return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=ocorrencia_id))

    form = OcorrenciaForm(obj=ocorrencia)
    populate_ocorrencia_form_choices(form)

    if form.validate_on_submit():
        try:
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter_by(nome=form.novo_tipo_ocorrencia.data.strip()).first()
                if tipo_existente:
                    tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(nome=form.novo_tipo_ocorrencia.data.strip())
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            else:
                tipo_ocorrencia_id = form.ocorrencia_tipo_id.data

            ocorrencia.condominio_id = form.condominio_id.data
            ocorrencia.data_plantao = form.data_plantao.data
            ocorrencia.turno = form.turno.data
            ocorrencia.relatorio_final = form.relatorio_final.data
            ocorrencia.status = form.status.data
            ocorrencia.ocorrencia_tipo_id = tipo_ocorrencia_id

            # atualiza supervisor
            supervisor_id = form.supervisor_id.data
            if supervisor_id == 0:
                supervisor_id = None
            ocorrencia.supervisor_id = supervisor_id

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

    elif request.method == 'GET':
        form.orgaos_acionados.data = [o.id for o in ocorrencia.orgaos_acionados]
        form.colaboradores_envolvidos.data = [c.id for c in ocorrencia.colaboradores_envolvidos]
        form.supervisor_id.data = ocorrencia.supervisor_id or 0  # Preenche o supervisor no form na edição

    return render_template('ocorrencia/form_direto.html', title=f'Editar Ocorrência #{ocorrencia.id}', form=form)


# --- NOVAS ROTAS PARA OS MODAIS ---

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
