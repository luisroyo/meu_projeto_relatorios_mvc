import os
import sys

# Add backend dir to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.services.consolidated_report_service import ConsolidatedReportService

raw_text = """
1. OPERAÇÃO INTERNA – MASTER / RESIDENCIAIS
1.1 Distribuição da Equipe
Agentes de Monitoramento
Dayane Messias de Jesus
Eylen Leandro dos Santos
José de Souza Lima
Luciellen Pereira da Silva (Remanejo)
Samuel Borges da Rocha 
Walter Vinícius Alves de Melo

Agentes de Portaria – Ronda – Monitoramento / Cobertura
Rodrigo Maciel da Silva
Luciellen Pereira da Silva

1.2 Coberturas e Remanejamentos
Luciellen Pereira da Silva
Função Original: Agente de Portaria
Função Desempenhada: Agente de Monitoramento
Horário: 18h00 às 06h00
Motivo: Cobertura de posto / Remanejamento

Rodrigo Maciel da Silva
Função Original: Agente de Portaria
Função Desempenhada: Guarda Patrimonial
Local: Residencial Fribourg
Horário: 18h00 às 06h00
Motivo: Cobertura de férias (Leia Goldin)

1.3 Ausências
Master
Daniel dos Santos Alves – Atestado
Elton Dener da Silva Vitor – Falta
Gustavo Fernando Pompeu Junior – Afastado
Lucimar Aparecido – Afastado

Residenciais
Guilherme Manfre Coelho dos Santos (Biel) – Afastado
Josenildo José de Ataíde Felix (Glarus) – Falta
Larissa Santos (Fribourg) – Afastada
Mairon (Basel) – Afastado

1.4 Férias
Residenciais
André Luis da Rocha (Basel)
Leia Goldin dos Santos (Fribourg)

1.5 Informações Gerais
Senha do dia: Sierra
Abastecimentos: Toro e MT 05.
Folgas Trabalhadas (FT - Reforço Residencial):
Eyshila Gabryelli – Residencial Fribourg

2. OPERAÇÃO UNISETER
2.1 Distribuição da Equipe
Inspetor
S.1: Almeida 

Lider
S.2: William

Vigilantes
VTR 02 – Tainara (Setor 1)
VTR 03 – Marcelo (Setor 2)
M.T 01 – Robson (Rota 2)
M.T 02 – Heber (Almocista)
M.T 04 – Jorge (Rota 1)
M.T 05 – Felipe (Rota 3)

Apoio 90
PA: Claudinei Aparecido
PG: Lindomar Aparecido
PL: Diogo Alexandre
PC: Mario Gomes
Velado 1: Ruan Mendes
Velado 2: Adriano Marcos

2.2 Rotas
Rota 1
St. Moritz, Lugano, Zermatt, Lenk, Baden, Arosa, Villeneuve

Rota 2
Lauerz, Luzern, Zurich (não permite entrada), Glarus, Davos, La Vie (somente moto), Parque Botânico, Eco Vila Genebra

Rota 3
Vevey, Fribourg, Geneve (não permite entrada), Biel, Basel

2.3 Rondas Realizadas
Arosa – 06
Baden – 05
Basel – 04
Biel – 05
Davos – 04
Eco Villa Genebra – 05
Fribourg – 05
Glarus – 05
Lauerz – 04
La Vie – 06
Lenk – 03
Lugano – 04
Luzern – 03
St. Moritz – 05
Vevey – 05
Zermatt – 04
Total de rondas: 73

Paradas à frente dos residenciais
Arosa – 06
Baden – 04
Basel – 03
Bern – 04
Biel – 03
Botânico – 03
Davos – 05
Fribourg – 03
Geneve – 06
Glarus – 05
Lauerz – 05
Lenk – 03
Lugano – 04
Luzern – 04
Novile – 03
Office – 03
St. Moritz – 05
Vevey – 03
Villeneuve – 03
Zermatt – 04
Zurich – 08
Total de paradas: 86 

3.1 Ocorrência
Data: 26/02/2026
Hora: 21:56
Local: EKTO, Rua Lázaro Marchete N°1508h
Ocorrência: Porta Aberta em Comércio
Relato:
Em deslocamento para averiguação no Residencial Ekto Seguros, foi avistada a porta de acesso ao comércio Ekto Seguros em condição aberta. A Central de Monitoramento foi notificada da situação e solicitou o acionamento da equipe Apoio 90. A equipe Apoio 90 realizou a varredura do local em conjunto com o Líder William Santos, conforme registrado por imagens do sistema de monitoramento. Após a averiguação, nenhuma anomalia ou indício de violação foi constatado.
Ações Realizadas:
- Notificação à Central de Monitoramento sobre a porta de acesso aberta.
- Acionamento da equipe Apoio 90 para averiguação.
- Realização de varredura completa no comércio Ekto Seguros.
- Constatação de ausência de anormalidades ou violação.

Acionamentos:
(X) Central (X) Apoio 90 ( ) Supervisor ( ) Coordenador

Envolvidos/Testemunhas:
- Vigilante William Santos (Líder, VTR-11)
- Vigilante Tainara Barros (VTR-11)
- Supervisor Master Luis
- Equipe Apoio-Velado 02

Veículo (envolvido na ocorrência):
VTR-11
Responsável pelo registro: Líder Tainara Barros (VTR-11)

3.2 Ocorrência
Data: 27/02/2026
Hora: 05:42
Local: Zermatt
Ocorrência: Veículo com Pane Elétrica
Relato:
Às 05:42, a equipe da VTR-03, em deslocamento para averiguação no Residencial Zermatt, constatou a presença de um veículo com pane elétrica. O veículo, modelo Prisma, placa EIX5H68, estava imobilizado nas proximidades da loja pet Santa Teresina. Foi feito contato com o condutor, identificado como Luis Carlos, que informou estar aguardando a chegada de serviço de guincho.
Ações Realizadas:
- Averiguação da situação de pane elétrica veicular.
- Estabelecimento de contato e coleta de informações com o condutor.

Envolvidos/Testemunhas:
Luis Carlos (Condutor)

Veículo (envolvido na ocorrência):
Modelo: Prisma
Cor: Não informada
Placa: EIX5H68
Responsável pelo registro: Agente Martins / VTR-03
"""

app = create_app()

with app.app_context():
    print("Testing ConsolidatedReportService...")
    service = ConsolidatedReportService()
    try:
        report = service.gerar_relatorio_consolidado(raw_text)
        print("\n\n------- GENERATED REPORT -------\n")
        print(report)
        print("\n--------------------------------\n")
    except Exception as e:
        print(f"Error: {e}")
