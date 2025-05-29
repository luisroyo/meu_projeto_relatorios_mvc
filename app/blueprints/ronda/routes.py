# app/blueprints/ronda/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db 
from app.models import Condominio
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

    try:
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        choices_list = [('', '-- Selecione um Condomínio --')] + \
                       [(c.nome, c.nome) for c in condominios_db] + \
                       [('Outro', 'Outro')]
        form.nome_condominio.choices = choices_list
    except Exception as e:
        logger.error(f"Erro ao carregar lista de condomínios: {e}", exc_info=True)
        flash('Erro ao carregar lista de condomínios. Tente novamente mais tarde.', 'danger')
        form.nome_condominio.choices = [('', '-- Erro ao Carregar --'), ('Outro', 'Outro')]

    if form.validate_on_submit():
        nome_condominio_selecionado = form.nome_condominio.data
        log_bruto = form.log_bruto_rondas.data
        data_plantao_obj = form.data_plantao.data
        escala_plantao_str = form.escala_plantao.data

        nome_condominio_final = None

        # Lógica para selecionar ou criar novo condomínio
        if nome_condominio_selecionado == 'Outro':
            outro_nome_raw = form.nome_condominio_outro.data.strip() if form.nome_condominio_outro.data else ''

            if not outro_nome_raw:
                flash('Se "Outro" é selecionado, o nome do condomínio deve ser fornecido.', 'danger')
            else:
                condominio_existente = Condominio.query.filter(Condominio.nome.ilike(outro_nome_raw)).first()

                if not condominio_existente:
                    try:
                        novo_condominio_obj = Condominio(nome=outro_nome_raw)
                        db.session.add(novo_condominio_obj)
                        db.session.commit()
                        nome_condominio_final = novo_condominio_obj.nome
                        flash(f'Novo condomínio "{novo_condominio_obj.nome}" adicionado.', 'info')
                    except Exception as e_add_cond:
                        db.session.rollback()
                        logger.error(f"Erro ao adicionar novo condomínio '{outro_nome_raw}': {e_add_cond}", exc_info=True)
                        flash(f'Erro ao adicionar o novo condomínio "{outro_nome_raw}".', 'danger')
                        return render_template('relatorio_ronda.html',
                                               title='Registrar/Processar Ronda',
                                               form=form,
                                               relatorio_processado=None)
                else:
                    nome_condominio_final = condominio_existente.nome
        else:
            nome_condominio_final = nome_condominio_selecionado

        # Processa somente se tiver os campos obrigatórios
        if nome_condominio_final and log_bruto:
            try:
                data_plantao_str_formatada = data_plantao_obj.strftime('%d/%m/%Y') if data_plantao_obj else None

                logger.info(f"Chamando processar_log_de_rondas com: "
                            f"Condomínio='{nome_condominio_final}', "
                            f"Data='{data_plantao_str_formatada}', "
                            f"Escala='{escala_plantao_str}'")

                # Chama a sua lógica personalizada
                relatorio_processado_final = processar_log_de_rondas(
                    log_bruto_rondas_str=log_bruto,
                    nome_condominio_str=nome_condominio_final,
                    data_plantao_manual_str=data_plantao_str_formatada,
                    escala_plantao_str=escala_plantao_str
                )

                if relatorio_processado_final:
                    flash('Relatório de ronda processado com sucesso!', 'success')
                else:
                    flash('Sua lógica processou, mas retornou um resultado vazio.', 'warning')
                    logger.warning("processar_log_de_rondas retornou None ou string vazia.")
            except Exception as e_custom_logic:
                logger.exception("Erro ao processar com lógica customizada:")
                flash(f'Erro ao processar com lógica personalizada: {str(e_custom_logic)}', 'danger')
                relatorio_processado_final = None
        elif not log_bruto:
            flash('O campo "Log Bruto das Rondas" é obrigatório para processamento.', 'warning')

    # Renderiza o template sempre, com ou sem relatório
    logger.debug(f"[DEBUG] Valor de relatorio_processado_final antes de renderizar: {relatorio_processado_final}")
    
    return render_template('relatorio_ronda.html',
                           title='Registrar/Processar Ronda',
                           form=form,
                           relatorio_processado=relatorio_processado_final)