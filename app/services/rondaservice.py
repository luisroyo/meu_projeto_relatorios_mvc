import logging
from .ronda_logic import processar_log_de_rondas # Importa a função principal do subpacote

# Este logger é para o arquivo 'rondaservice.py' especificamente,
# caso você adicione alguma lógica de fachada aqui.
logger = logging.getLogger(__name__)

# A função 'processar_log_de_rondas' agora está disponível através deste módulo
# para qualquer outra parte da aplicação que importe 'app.services.rondaservice'.

# Se você precisar adicionar alguma lógica de orquestração de alto nível
# ou adaptação de interface específica para 'rondaservice', você pode fazer aqui.
# Exemplo:
# def minha_interface_de_servico_ronda(*args, **kwargs):
#     logger.info("Interface de serviço de ronda chamada.")
#     # ... alguma lógica de pré-processamento ou adaptação ...
#     resultado = processar_log_de_rondas(*args, **kwargs)
#     # ... alguma lógica de pós-processamento ...
#     return resultado
#
# E então, no __init__.py de ronda_logic, você exportaria 'minha_interface_de_servico_ronda'
# ou o resto do app chamaria essa nova função.
# Para manter a compatibilidade, apenas reexportar 'processar_log_de_rondas' é o mais simples.

# Se você tiver um exemplo de como usá-lo, pode mantê-lo aqui ou movê-lo
# para um script de teste/demonstração separado.
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_exemplo = """
    [10:30, 20/05/2024] VTR 01: Início ronda 10:30
    [11:00, 20/05/2024] VTR 01: Término ronda 11 : 00
    """
    nome_condominio = "Condomínio Exemplo Fachada"
    data_plantao = "20/05/2024"
    escala = "Equipe Teste Fachada"
    
    # A chamada usa a função importada de .ronda_logic
    relatorio = processar_log_de_rondas(log_exemplo, nome_condominio, data_plantao, escala)
    print("\n--- RELATÓRIO (via app.services.rondaservice.py) ---")
    print(relatorio)