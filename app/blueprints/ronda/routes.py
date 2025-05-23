from flask import Blueprint, render_template, request, jsonify, flash, current_app
from flask_login import login_required, current_user
from app.forms import TestarRondasForm
from app.services.rondaservice import processar_log_de_rondas
from app.services.report_service import ReportService

ronda_bp = Blueprint('ronda', __name__)

report_service = ReportService()

@ronda_bp.route('/relatorio_ronda', methods=['GET', 'POST'])
@login_required
def relatorio_ronda():
    form = TestarRondasForm()
    resultado = None
    log = None

    if form.validate_on_submit():
        log = form.log_bruto_rondas.data
        nome = form.nome_condominio.data
        if nome == 'Outro':
            nome = form.nome_condominio_outro.data
        data = form.data_plantao.data.strftime('%d/%m/%Y')
        escala = form.escala_plantao.data

        try:
            resultado = processar_log_de_rondas(log, nome, data, escala)
            flash('Relatório processado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao processar: {e}', 'danger')
            resultado = f"Erro: {e}"

    elif request.method == 'POST':
        log = form.log_bruto_rondas.data

    return render_template('relatorio_ronda.html', title='Relatório de Ronda', form=form, resultado=resultado, log_enviado=log)

@ronda_bp.route('/processar_relatorio', methods=['POST'])
@login_required
def processar_relatorio():
    if not request.is_json:
        return jsonify({'erro': 'Formato inválido. Envie JSON.'}), 400

    data = request.get_json()
    bruto = data.get('relatorio_bruto')

    if not isinstance(bruto, str) or not bruto.strip():
        return jsonify({'erro': 'relatorio_bruto inválido.'}), 400

    if len(bruto) > 12000:
        return jsonify({'erro': 'Relatório muito longo (máx 12000 caracteres).'}), 413

    try:
        resultado = report_service.processar_relatorio_com_ia(bruto)
        return jsonify({'relatorio_processado': resultado})
    except ValueError as ve:
        return jsonify({'erro': str(ve)}), 400
    except RuntimeError as rte:
        return jsonify({'erro': str(rte)}), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({'erro': 'Erro interno. Tente novamente.'}), 500