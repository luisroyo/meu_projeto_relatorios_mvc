# app/blueprints/main/routes.py
import logging
import os

from flask import Blueprint, flash, g, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_login import current_user, login_required

from app import db, limiter
from app.forms import AnalisadorForm  # Verifique se este import está correto
from app.models import ProcessingHistory, Ocorrencia, Ronda, OcorrenciaTipo, Condominio, Parada
from sqlalchemy import func
import json
from datetime import datetime, timedelta, timezone
import calendar
from app.services.patrimonial_report_service import PatrimonialReportService
from app.services import ocorrencia_service

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

# Token para o endpoint de uptime
UPTIME_TOKEN = os.getenv("UPTIME_TOKEN", "defaulttoken")


def _get_patrimonial_service():
    if "patrimonial_service" not in g:
        g.patrimonial_service = PatrimonialReportService()
    return g.patrimonial_service


@main_bp.route("/", methods=["GET"])
@login_required
def index():
    # Parâmetro de mês/ano da URL (formato YYYY-MM)
    mes_ano_param = request.args.get('mes_ano')
    hoje = datetime.now(timezone.utc)
    
    if mes_ano_param:
        try:
            ano_selecionado, mes_selecionado = map(int, mes_ano_param.split('-'))
            inicio_mes = hoje.replace(year=ano_selecionado, month=mes_selecionado, day=1, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            mes_ano_param = f"{hoje.year}-{hoje.month:02d}"
    else:
        inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mes_ano_param = f"{hoje.year}-{hoje.month:02d}"

    # Calcula o fim do mês
    ultimo_dia = calendar.monthrange(inicio_mes.year, inicio_mes.month)[1]
    fim_mes = inicio_mes.replace(day=ultimo_dia, hour=23, minute=59, second=59)

    # 1. Total de Ocorrências e Rondas (Mês selecionado)
    total_ocorrencias = db.session.query(func.count(Ocorrencia.id)).filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_mes,
        Ocorrencia.data_hora_ocorrencia <= fim_mes
    ).scalar()
    
    total_rondas = db.session.query(func.count(Ronda.id)).filter(
        Ronda.data_hora_inicio >= inicio_mes,
        Ronda.data_hora_inicio <= fim_mes
    ).scalar()

    total_paradas = db.session.query(func.count(Parada.id)).filter(
        Parada.data_hora_inicio >= inicio_mes,
        Parada.data_hora_inicio <= fim_mes
    ).scalar()

    # 2. Rondas por Condomínio (Volume Mês) - Top 10
    rondas_por_cond = db.session.query(
        Condominio.nome, func.count(Ronda.id).label('total')
    ).join(Ronda, Condominio.id == Ronda.condominio_id).filter(
        Ronda.data_hora_inicio >= inicio_mes,
        Ronda.data_hora_inicio <= fim_mes
    ).group_by(Condominio.nome).order_by(db.desc('total')).limit(10).all()
    
    rondas_labels = [r[0] for r in rondas_por_cond]
    rondas_data = [r[1] for r in rondas_por_cond]

    # 3. Ocorrências por Tipo (Mês Selecionado)
    oc_por_tipo = db.session.query(
        OcorrenciaTipo.nome, func.count(Ocorrencia.id)
    ).join(Ocorrencia, OcorrenciaTipo.id == Ocorrencia.ocorrencia_tipo_id).filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_mes,
        Ocorrencia.data_hora_ocorrencia <= fim_mes
    ).group_by(OcorrenciaTipo.nome).all()

    tipo_labels = [r[0] for r in oc_por_tipo]
    tipo_data = [r[1] for r in oc_por_tipo]
    
    # Formata nome do mes para exibição (ex: Junho de 2026)
    meses_ptbr = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    nome_mes_exibicao = f"{meses_ptbr[inicio_mes.month - 1]} de {inicio_mes.year}"

    return render_template(
        "dashboard.html",
        title="Dashboard Executivo",
        total_ocorrencias=total_ocorrencias,
        total_rondas=total_rondas,
        total_paradas=total_paradas,
        rondas_labels=json.dumps(rondas_labels),
        rondas_data=json.dumps(rondas_data),
        tipo_labels=json.dumps(tipo_labels),
        tipo_data=json.dumps(tipo_data),
        mes_ano_param=mes_ano_param,
        nome_mes_exibicao=nome_mes_exibicao
    )

@main_bp.route("/analisador", methods=["GET", "POST"])
@limiter.limit("200 per hour")
@login_required
def analisador():
    form = AnalisadorForm()
    relatorio_corrigido = None

    if form.validate_on_submit():
        relatorio_bruto = form.relatorio_bruto.data
        processing_success = False
        processing_error_message = None

        try:
            logger.info(f"Iniciando processamento para '{current_user.username}'.")
            patrimonial_service = _get_patrimonial_service()
            relatorio_corrigido = patrimonial_service.gerar_relatorio_seguranca(
                relatorio_bruto
            )
            flash("Relatório processado com sucesso!", "success")
            processing_success = True

        except Exception as e:
            logger.error(f"Erro ao processar relatório: {e}", exc_info=True)
            processing_error_message = f"Falha no serviço de IA: {str(e)}"
            flash(f"Ocorreu um erro ao processar o relatório.", "danger")

        # Salva o histórico (mesma lógica de antes)
        try:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type="patrimonial_report",
                success=processing_success,
                error_message=processing_error_message,
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e_history:
            db.session.rollback()
            logger.error(
                f"CRÍTICO: Falha ao salvar histórico: {e_history}", exc_info=True
            )
            flash("Erro grave ao registrar a operação.", "danger")

        # Ao final do POST, re-renderiza a página com o formulário e o resultado
        return render_template(
            "analisador.html",
            title="Resultado da Análise",
            form=form,
            relatorio_corrigido=relatorio_corrigido,
        )

    # Para requisições GET, renderiza a página com o formulário vazio
    # --- PONTO DA CORREÇÃO ---
    # A variável 'form' agora é passada também no GET inicial.
    
    # Verificar ocorrências pendentes para alerta
    ocorrencias_pendentes_count = ocorrencia_service.contar_ocorrencias_pendentes()
    
    return render_template(
        "analisador.html",
        title="Analisador de Relatórios IA",
        form=form,
        relatorio_corrigido=relatorio_corrigido,
        ocorrencias_pendentes_count=ocorrencias_pendentes_count,
    )


@main_bp.route("/uptime")
def uptime():
    """Endpoint de monitoramento para UptimeRobot e ferramentas similares."""
    token = request.args.get('token')
    
    if not token or token != UPTIME_TOKEN:
        return jsonify({"error": "unauthorized"}), 403
    
    return jsonify({"status": "ok"}), 200


@main_bp.route("/processar_relatorio", methods=["POST"])
@login_required
def processar_relatorio_redirect():
    """
    Rota para processar relatórios diretamente, mantendo compatibilidade com o frontend.
    Usa a autenticação da sessão Flask-Login em vez de JWT.
    """
    from app.utils.classificador import classificar_ocorrencia
    from app.services.patrimonial_report_service import PatrimonialReportService
    
    try:
        # Obter dados do formulário
        data = request.get_json()
        if not data or not data.get('relatorio_bruto'):
            return jsonify({'error': 'Relatório bruto é obrigatório'}), 400
        
        relatorio_bruto = data['relatorio_bruto']
        
        # Classificar ocorrência
        classificacao = classificar_ocorrencia(relatorio_bruto)
        
        # Processar relatório patrimonial
        patrimonial_service = PatrimonialReportService()
        relatorio_processado = patrimonial_service.gerar_relatorio_seguranca(relatorio_bruto)
        
        # Salvar histórico
        history = ProcessingHistory(
            user_id=current_user.id,
            processing_type="patrimonial_report",
            success=True,
            error_message=None
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'classificacao': classificacao,
            'relatorio_processado': relatorio_processado
        }), 200
        
    except Exception as e:
        # Salvar histórico de erro
        try:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type="patrimonial_report",
                success=False,
                error_message=str(e)
            )
            db.session.add(history)
            db.session.commit()
        except Exception as history_error:
            logger.error(f"Erro ao salvar histórico: {history_error}")
        
        logger.error(f"Erro ao processar relatório: {e}")
        return jsonify({'error': 'Erro ao processar relatório'}), 500


# ======================================================================
# ROTA PARA FAVICON
# ======================================================================
@main_bp.route('/favicon.ico')
def favicon():
    """Serve o favicon para evitar erros 404."""
    import os
    from flask import current_app
    return send_from_directory(
        os.path.join(current_app.root_path, '..', 'frontend', 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# ======================================================================
# ROTA DE TESTE ISOLADO PARA A API DO GEMINI - ADICIONAR NO FINAL DO ARQUIVO DE ROTAS
# ======================================================================
import google.generativeai as genai

@main_bp.route('/test-gemini')
def test_gemini_route():
    """
    Esta rota executa um teste limpo e direto da biblioteca google-generativeai
    para verificar qual versão da API ela está realmente usando no ambiente.
    """
    logger = logging.getLogger('gemini_test')
    logger.setLevel(logging.INFO)
    
    test_api_key = os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY_2")
    
    if not test_api_key:
        return "ERRO: GOOGLE_API_KEY_1 ou GOOGLE_API_KEY_2 não está configurada no ambiente.", 500

    try:
        logger.info("--- INICIANDO TESTE GEMINI ISOLADO ---")
        
        # Passo 1: Criar cliente com nova API
        client = genai.Client(api_key=test_api_key)
        logger.info("Cliente genai.Client() criado com sucesso.")
        
        # Passo 2: Gerar conteúdo com nova API
        logger.info("Enviando prompt 'Qual a capital do Brasil?' para o modelo...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Qual a capital do Brasil?"
        )
        logger.info("Chamada para generate_content() retornou sem erro.")
        
        logger.info("--- TESTE GEMINI ISOLADO CONCLUÍDO COM SUCESSO ---")
        return f"SUCESSO! Resposta da API: {response.text}", 200

    except Exception as e:
        logger.error(f"--- ERRO NO TESTE GEMINI ISOLADO ---")
        logger.error(f"O teste falhou com a seguinte exceção: {e}", exc_info=True)
        # Retornamos o traceback completo na resposta para facilitar o debug
        import traceback
        return f"FALHA NO TESTE: {e}\n\nTraceback:\n{traceback.format_exc()}", 500

@main_bp.route('/list-models')
def list_gemini_models():
    """
    Lista todos os modelos Gemini disponíveis na conta.
    Útil para descobrir quais modelos estão realmente acessíveis.
    """
    logger = logging.getLogger('gemini_models_list')
    logger.setLevel(logging.INFO)
    
    test_api_key = os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY_2")
    
    if not test_api_key:
        return "ERRO: GOOGLE_API_KEY_1 ou GOOGLE_API_KEY_2 não está configurada no ambiente.", 500

    try:
        logger.info("--- LISTANDO MODELOS GEMINI DISPONÍVEIS ---")
        
        # Cria cliente com nova API
        client = genai.Client(api_key=test_api_key)
        logger.info("Cliente genai.Client() criado com sucesso.")
        
        # Lista todos os modelos disponíveis
        logger.info("Buscando lista de modelos disponíveis...")
        models = client.models.list()
        
        available_models = []
        for model in models:
            model_name = model.name
            available_models.append(model_name)
            logger.info(f"Modelo encontrado: {model_name}")
        
        logger.info(f"--- TOTAL: {len(available_models)} modelos encontrados ---")
        
        # Formata resposta para exibição
        response_html = f"""
        <h2>🤖 Modelos Gemini Disponíveis ({len(available_models)})</h2>
        <ul>
        """
        
        for model in available_models:
            response_html += f"<li><strong>{model}</strong></li>\n"
        
        response_html += """
        </ul>
        <hr>
        <p><em>Esta lista mostra todos os modelos que sua conta tem acesso.</em></p>
        """
        
        return response_html, 200

    except Exception as e:
        logger.error(f"--- ERRO AO LISTAR MODELOS GEMINI ---")
        logger.error(f"Erro: {e}", exc_info=True)
        import traceback
        return f"ERRO AO LISTAR MODELOS: {e}\n\nTraceback:\n{traceback.format_exc()}", 500

# ======================================================================
# ROTA PARA SERVIR REACT APP (DASHBOARD NOVO)
# ======================================================================
@main_bp.route('/app', defaults={'path': ''})
@main_bp.route('/app/<path:path>')
def serve_react_app(path):
    """
    Serve a aplicação React (Dashboard Novo) para qualquer rota iniciada com /app.
    Se o arquivo solicitado existir em static/react, serve ele.
    Caso contrário, serve o index.html do React para o router do frontend lidar.
    """
    from flask import current_app
    
    # Caminho onde o Vite gera o build (configurado no vite.config.ts)
    # project_root/frontend/static/react
    react_dist_dir = os.path.join(current_app.root_path, '..', '..', 'frontend', 'static', 'react')
    
    full_path = os.path.join(react_dist_dir, path)
    
    if path != "" and os.path.exists(full_path):
        return send_from_directory(react_dist_dir, path)
    else:
        return send_from_directory(react_dist_dir, 'index.html')