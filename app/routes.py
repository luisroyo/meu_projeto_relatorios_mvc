from flask import render_template, request, jsonify
from app import app # Importa a instância 'app' de app/__init__.py
from app.services.report_service import ReportService

report_service_instance = None
try:
    report_service_instance = ReportService()
except (ValueError, RuntimeError) as e:
    # Log já acontece no __init__ do ReportService ou no app/__init__
    # Aqui apenas registramos que o serviço não está disponível para as rotas.
    app.logger.critical(f"Falha catastrófica na inicialização do ReportService. O serviço estará indisponível. Erro: {e}", exc_info=True)
    # Deixar report_service_instance como None será tratado nas rotas.

@app.route('/')
def index():
    """Renderiza a página inicial (View)."""
    return render_template('index.html', title='Processador de Relatórios')

@app.route('/processar_relatorio', methods=['POST'])
def processar_relatorio_route():
    """Recebe dados do relatório, processa usando o serviço e retorna JSON."""
    if report_service_instance is None:
        app.logger.error(f"Tentativa de acesso a /processar_relatorio enquanto ReportService está indisponível. IP: {request.remote_addr}")
        return jsonify({"erro": "Serviço de processamento indisponível devido a erro de configuração interna. Contate o administrador."}), 503

    if not request.is_json:
        app.logger.warning(f"Requisição não JSON para /processar_relatorio. IP: {request.remote_addr}")
        return jsonify({"erro": "Requisição inválida: corpo deve ser JSON."}), 400

    data = request.get_json()
    if not data:
         app.logger.warning(f"Corpo JSON vazio recebido em /processar_relatorio. IP: {request.remote_addr}")
         return jsonify({"erro": "Requisição inválida: corpo JSON vazio."}), 400

    relatorio_bruto = data.get('relatorio_bruto')

    if relatorio_bruto is None:
         app.logger.warning(f"Campo 'relatorio_bruto' não encontrado no JSON. IP: {request.remote_addr}")
         return jsonify({"erro": "Campo 'relatorio_bruto' não encontrado no corpo JSON."}), 400
    if not isinstance(relatorio_bruto, str):
         app.logger.warning(f"Campo 'relatorio_bruto' não é uma string. IP: {request.remote_addr}")
         return jsonify({"erro": "Campo 'relatorio_bruto' deve ser uma string."}), 400
    
    # Validação de tamanho (Refinamento 4)
    MAX_INPUT_LENGTH_SERVER = 12000 
    if not relatorio_bruto.strip():
        app.logger.warning(f"Tentativa de processar relatório bruto vazio. IP: {request.remote_addr}")
        return jsonify({"erro": "Campo 'relatorio_bruto' não pode estar vazio."}), 400
    
    if len(relatorio_bruto) > MAX_INPUT_LENGTH_SERVER:
        app.logger.warning(f"Tentativa de processar relatório muito longo. IP: {request.remote_addr}. Tamanho: {len(relatorio_bruto)}")
        return jsonify({"erro": f"Relatório muito longo. O tamanho máximo permitido é de {MAX_INPUT_LENGTH_SERVER} caracteres."}), 413

    try:
        relatorio_processado = report_service_instance.processar_relatorio_com_ia(relatorio_bruto)
        app.logger.info(f"Relatório processado com sucesso. IP: {request.remote_addr}. Tamanho entrada: {len(relatorio_bruto)}, Tamanho saída: {len(relatorio_processado)}")
        return jsonify({'relatorio_processado': relatorio_processado})
    except ValueError as ve: # Erros de validação do nosso serviço (ex: input vazio para IA)
        app.logger.warning(f"Erro de valor (ValueError) no processamento do relatório: {ve}. IP: {request.remote_addr}")
        return jsonify({'erro': str(ve)}), 400 # Bad Request
    except RuntimeError as rte: # Erros levantados pelo nosso ReportService (ex: API errors, prompt bloqueado)
        app.logger.error(f"Erro de execução (RuntimeError) no processamento: {rte}. IP: {request.remote_addr}", exc_info=False) # exc_info=False pois o ReportService já logou com exc_info
        return jsonify({'erro': str(rte)}), 500 # Internal Server Error ou um código mais específico se rte tiver essa info
    except Exception as e: # Outras exceções inesperadas
        app.logger.error(f"Exceção genérica não tratada em processar_relatorio_route: {e.__class__.__name__}: {e}. IP: {request.remote_addr}", exc_info=True)
        return jsonify({'erro': 'Ocorreu um erro interno inesperado no servidor. Por favor, tente novamente mais tarde.'}), 500