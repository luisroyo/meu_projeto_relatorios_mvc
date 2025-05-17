from flask import render_template, request, jsonify
from app import app  # Importa a instância 'app' de __init__.py
from app.services.report_service import ReportService

# Instancia o serviço UMA VEZ quando o módulo é carregado.
# Isso é geralmente bom para serviços que não mantêm estado específico da requisição
# ou que são caros para instanciar repetidamente.
try:
    report_service = ReportService()
except ValueError as e: # Captura erro se a API Key não for encontrada na inicialização do serviço
    print(f"ERRO CRÍTICO ao inicializar ReportService: {e}")
    # Em um app real, você poderia desabilitar funcionalidades ou mostrar um erro global.
    # Por agora, vamos permitir que o app continue, mas as chamadas ao serviço falharão.
    report_service = None 

@app.route('/')
def index():
    """Renderiza a página inicial (View)."""
    return render_template('index.html', title='Processador de Relatórios')

@app.route('/processar_relatorio', methods=['POST'])
def processar_relatorio_route():
    """Recebe dados do relatório, processa usando o serviço e retorna JSON."""
    if report_service is None:
        print("ERRO: Tentativa de usar ReportService, mas ele não foi inicializado corretamente (provavelmente API key faltando).")
        return jsonify({"erro": "Serviço de processamento indisponível devido a erro de configuração."}), 503 # Service Unavailable

    if not request.is_json:
        return jsonify({"erro": "Requisição inválida: corpo deve ser JSON."}), 400

    data = request.get_json()
    if not data: # Checa se o JSON é nulo ou vazio
         return jsonify({"erro": "Requisição inválida: corpo JSON vazio."}), 400

    relatorio_bruto = data.get('relatorio_bruto')

    if relatorio_bruto is None: # Checa se a chave 'relatorio_bruto' existe
         return jsonify({"erro": "Campo 'relatorio_bruto' não encontrado no corpo JSON."}), 400
    if not isinstance(relatorio_bruto, str): # Checa se é uma string
         return jsonify({"erro": "Campo 'relatorio_bruto' deve ser uma string."}), 400
    if not relatorio_bruto.strip(): # Checa se a string (após remover espaços) está vazia
         return jsonify({"erro": "Campo 'relatorio_bruto' não pode estar vazio."}), 400


    try:
        # Chama o método (ainda simulado) do nosso serviço
        relatorio_processado = report_service.processar_relatorio_com_ia(relatorio_bruto)
        return jsonify({'relatorio_processado': relatorio_processado})
    except ValueError as ve: # Erros de validação específicos do nosso serviço
        print(f"DEBUG: Erro de valor no processamento: {ve}")
        return jsonify({'erro': str(ve)}), 400 # Bad Request
    except Exception as e:
        # Em produção, logar 'e' de forma detalhada e segura
        print(f"ERRO: Exceção não tratada em processar_relatorio_route: {e.__class__.__name__}: {e}")
        return jsonify({'erro': 'Ocorreu um erro interno inesperado ao processar o relatório.'}), 500 # Internal Server Error