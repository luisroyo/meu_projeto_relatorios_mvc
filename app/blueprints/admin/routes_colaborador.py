# app/blueprints/admin/routes_colaborador.py
import logging
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, g
)
from flask_login import login_required, current_user
from sqlalchemy import func, and_, cast, Float
from datetime import datetime, timedelta, timezone

from . import admin_bp
from app import db
from app.models import User, LoginHistory, Ronda, Colaborador, ProcessingHistory, Condominio, EscalaMensal
from app.decorators.admin_required import admin_required
from app.forms import FormatEmailReportForm, ColaboradorForm
from app.services.justificativa_service import JustificativaAtestadoService
from app.services.justificativa_troca_plantao_service import JustificativaTrocaPlantaoService

logger = logging.getLogger(__name__)

@admin_bp.route('/colaboradores', methods=['GET'])
@login_required
@admin_required
def listar_colaboradores():
    page = request.args.get('page', 1, type=int)
    colaboradores_pagination = Colaborador.query.order_by(Colaborador.nome_completo).paginate(page=page, per_page=10)
    return render_template('admin/listar_colaboradores.html',
                           title='Gerenciar Colaboradores',
                           colaboradores_pagination=colaboradores_pagination)


@admin_bp.route('/api/colaboradores/search', methods=['GET'])
@login_required
@admin_required
def api_search_colaboradores():
    search_term = request.args.get('term', '').strip()
    if not search_term or len(search_term) < 2:
        return jsonify([])
    colaboradores = Colaborador.query.filter(
        Colaborador.status == 'Ativo',
        func.lower(Colaborador.nome_completo).contains(func.lower(search_term))
    ).order_by(Colaborador.nome_completo).limit(10).all()
    return jsonify([{'id': c.id, 'nome_completo': c.nome_completo, 'cargo': c.cargo} for c in colaboradores])


@admin_bp.route('/api/colaborador/<int:colaborador_id>/details', methods=['GET'])
@login_required
@admin_required
def api_get_colaborador_details(colaborador_id):
    colaborador = Colaborador.query.get(colaborador_id)
    if colaborador and colaborador.status == 'Ativo':
        return jsonify({
            'id': colaborador.id,
            'nome_completo': colaborador.nome_completo,
            'cargo': colaborador.cargo,
            'matricula': colaborador.matricula
        })
    return jsonify({'erro': 'Colaborador não encontrado ou inativo'}), 404


@admin_bp.route('/colaboradores/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_colaborador():
    form = ColaboradorForm()
    if form.validate_on_submit():
        try:
            novo_colaborador = Colaborador(
                nome_completo=form.nome_completo.data,
                cargo=form.cargo.data,
                matricula=form.matricula.data or None,
                data_admissao=form.data_admissao.data,
                status=form.status.data
            )
            db.session.add(novo_colaborador)
            db.session.commit()
            flash(f'Colaborador "{novo_colaborador.nome_completo}" adicionado.', 'success')
            return redirect(url_for('admin.listar_colaboradores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar colaborador: {str(e)}', 'danger')
    return render_template('admin/colaborador_form.html', title='Adicionar Colaborador', form=form)


@admin_bp.route('/colaboradores/editar/<int:colaborador_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    form = ColaboradorForm(obj=colaborador)
    if form.validate_on_submit():
        try:
            form.populate_obj(colaborador)
            db.session.commit()
            flash(f'Colaborador "{colaborador.nome_completo}" atualizado.', 'success')
            return redirect(url_for('admin.listar_colaboradores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar colaborador: {str(e)}', 'danger')
    return render_template('admin/colaborador_form.html', title='Editar Colaborador', form=form, colaborador=colaborador)


@admin_bp.route('/colaboradores/deletar/<int:colaborador_id>', methods=['POST'])
@login_required
@admin_required
def deletar_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    try:
        db.session.delete(colaborador)
        db.session.commit()
        flash(f'Colaborador "{colaborador.nome_completo}" deletado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar: {str(e)}', 'danger')
    return redirect(url_for('admin.listar_colaboradores'))