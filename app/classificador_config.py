# app/classificador_config.py

"""
Arquivo de configuração para o classificador de ocorrências.
Isola o dicionário de mapeamento para facilitar a manutenção e manter
a lógica de negócio separada da configuração.
"""

# Dicionário de palavras-chave. A chave é o nome exato do tipo de ocorrência
# no banco de dados, e o valor é uma lista de termos para busca.
MAPA_PALAVRAS_CHAVE_TIPO = {
    "Acidente de trânsito com vítima": [
        "acidente com vítima", "atropelamento com feridos", "colisão com vítima", "batida com ferido"
    ],
    "Acidente de trânsito sem vítima": [
    "acidente sem vítima", "colisão sem feridos", "batida de carro", "batida leve", "choque entre veículos",
    "queda de motocicleta", "queda de moto", "queda de motociclista", "colisão entre veiculos" # <--- ADICIONE AQUI
],
    "Tentativa de Roubo": [
        "tentativa de roubo", "tentaram roubar", "tentou roubar"
    ],
    "Tentativa de furto": [
        "tentativa de furto", "tentaram furtar"
    ],
    "Furtos": [
        "furto", "subtração", "furtaram"
    ],
    "Roubo": [
        "roubo", "assalto", "levou com ameaça", "subtração com violência", "foi roubado"
    ],
    "Prisões em ocorrência": [
        "foi preso", "indivíduo detido", "detenção", "encaminhado à delegacia"
    ],
    "Uso ou porte de entorpecentes": [
        "uso de entorpecente", "porte de droga", "entorpecente", "substância ilícita", "porte de entorpecente", "carregava droga"
    ],
    "Danos ao patrimônio": [
        "dano ao patrimônio", "portão quebrado", "vidro quebrado", "amassou estrutura", "depredação"
    ],
    "Vandalismo": [
        "vandalismo", "pichação", "quebra intencional", "depredou"
    ],
    "Invasão": [
        "invasão", "entrada não autorizada", "pulou o muro", "acesso forçado"
    ],
    "Desinteligência": [
        "desinteligência", "conflito verbal", "discussão acalorada", "bate-boca", "rixa"
    ],
    "Atos obscenos": [
        "ato obsceno", "exibicionismo", "gesto obsceno", "nudismo"
    ],
    "Apoio à Polícia Militar (PM)": [
        "apoio à pm", "auxílio à polícia militar", "apoio policial", "acompanhamento da pm"
    ],
    "Apoio à Guarda Civil Municipal (GCM)": [
        "apoio à gcm", "apoio guarda municipal", "apoio à guarda"
    ],
    "Auxílio ao Residencial": [
        "acompanhamento de oficial", "suporte à administração", "auxílio ao condomínio", "apoio a prestador"
    ],
    "Auxílio ao Morador": [
        "auxílio a morador", "ajuda a condômino", "apoio a morador"
    ],
    "Auxílio ao público": [
        "ajuda ao público", "apoio ao cidadão", "auxílio a transeunte"
    ],
    "Orientação ao público": [
    "orientação ao público", "informação prestada", "instruiu morador", "orientou o cidadão",
    "averiguação de indivíduo", "verificação de pessoa", "qualificação de indivíduo" # <--- ADICIONE AQUI
],
    "Perturbação de sossego": [
        "perturbação", "som alto", "barulho excessivo", "ruído perturbador"
    ],
    "Falta de energia": [
        "falta de energia", "queda de energia", "apagão"
    ],
    "Oscilação de energia": [
        "oscilação de energia", "variação de energia", "queda momentânea"
    ],
    "Ocorrências sem registro de B.O": [
        "sem registro de b.o", "não foi lavrado boletim", "ocorrência sem b.o", "registro não efetuado"
    ]
}