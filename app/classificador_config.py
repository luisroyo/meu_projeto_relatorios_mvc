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
        "acidente com vítima",
        "atropelamento com feridos",
        "colisão com vítima",
        "batida com ferido",
        "colisão envolvendo ferido",
        "ferido em acidente",
        "vítima de trânsito",
        "envolvendo vítima",
    ],
    "Acidente de trânsito sem vítima": [
        "acidente sem vítima",
        "colisão sem feridos",
        "batida de carro",
        "batida leve",
        "choque entre veículos",
        "queda de motocicleta",
        "queda de moto",
        "queda de motociclista",
        "colisão entre veiculos",
        "acidente leve",
        "carro bateu",
        "batida sem feridos",
        "incidente no trânsito",
        "colisão entre dois veículos",
    ],
    "Tentativa de Roubo": [
        "tentativa de roubo",
        "tentaram roubar",
        "tentou roubar",
        "quase foi roubado",
        "tentaram levar",
        "tentativa de assalto",
    ],
    "Tentativa de furto": [
        "tentativa de furto",
        "tentaram furtar",
        "tentaram invadir para furtar",
        "tentaram levar objeto",
        "ação suspeita de furto",
    ],
    "Furtos": [
        "furto",
        "subtração",
        "furtaram",
        "sumiço de objeto",
        "objeto desaparecido",
        "foi levado",
        "pegou sem autorização",
        "retirado sem permissão",
    ],
    "Roubo": [
        "roubo",
        "assalto",
        "levou com ameaça",
        "subtração com violência",
        "foi roubado",
        "levado sob ameaça",
        "levou à força",
        "roubo à mão armada",
    ],
    "Prisões em ocorrência": [
        "foi preso",
        "indivíduo detido",
        "detenção",
        "encaminhado à delegacia",
        "conduzido pela polícia",
        "capturado",
        "suspeito preso",
    ],
    "Uso ou porte de entorpecentes": [
        "uso de entorpecente",
        "porte de droga",
        "entorpecente",
        "substância ilícita",
        "porte de entorpecente",
        "carregava droga",
        "drogas apreendidas",
        "portava entorpecente",
    ],
    "Danos ao patrimônio": [
        "dano ao patrimônio",
        "portão quebrado",
        "vidro quebrado",
        "amassou estrutura",
        "depredação",
        "estrutura danificada",
        "objeto danificado",
        "estragou patrimônio",
    ],
    "Vandalismo": [
        "vandalismo",
        "pichação",
        "quebra intencional",
        "depredou",
        "ação de vândalos",
        "vândalo",
        "destruição voluntária",
        "vandalizou",
    ],
    "Invasão": [
        "invasão",
        "entrada não autorizada",
        "pulou o muro",
        "acesso forçado",
        "entrou sem permissão",
        "invadiu área",
        "entrou irregularmente",
    ],
    "Desinteligência": [
        "desinteligência",
        "conflito verbal",
        "discussão acalorada",
        "bate-boca",
        "rixa",
        "desentendimento",
        "briga verbal",
        "tensão entre partes",
    ],
    "Atos obscenos": [
        "ato obsceno",
        "exibicionismo",
        "gesto obsceno",
        "nudismo",
        "se expôs",
        "exposição indecente",
        "ação obscena",
    ],
    "Apoio à Polícia Militar (PM)": [
        "apoio à pm",
        "auxílio à polícia militar",
        "apoio policial",
        "acompanhamento da pm",
        "solicitação da pm",
        "suporte à pm",
        "auxílio à PM",
    ],
    "Apoio à Guarda Civil Municipal (GCM)": [
        "apoio à gcm",
        "apoio guarda municipal",
        "apoio à guarda",
        "auxílio à gcm",
        "acompanhamento da gcm",
        "suporte à guarda",
        "solicitação da gcm",
    ],
    "Auxílio ao Residencial": [
        "acompanhamento de oficial",
        "suporte à administração",
        "auxílio ao condomínio",
        "apoio a prestador",
        "ajuda no residencial",
        "suporte interno",
        "assistência ao residencial",
    ],
    "Auxílio ao Morador": [
        "auxílio a morador",
        "ajuda a condômino",
        "apoio a morador",
        "prestou auxílio ao morador",
        "assistência ao morador",
        "suporte ao morador",
    ],
    "Auxílio ao público": [
        "ajuda ao público",
        "apoio ao cidadão",
        "auxílio a transeunte",
        "ajuda a pessoa",
        "assistência ao público",
        "prestou apoio ao público",
    ],
    "Orientação ao público": [
        "orientação ao público",
        "informação prestada",
        "instruiu morador",
        "orientou o cidadão",
        "averiguação de indivíduo",
        "verificação de pessoa",
        "qualificação de indivíduo",
        "prestou esclarecimento",
        "repassou informações",
        "tirou dúvida",
    ],
    "Perturbação de sossego": [
        "perturbação",
        "som alto",
        "barulho excessivo",
        "ruído perturbador",
        "baderna",
        "festa barulhenta",
        "volume elevado",
        "incomodando vizinhos",
    ],
    "Falta de energia": [
        "falta de energia",
        "queda de energia",
        "apagão",
        "energia cortada",
        "sem energia elétrica",
        "interrupção elétrica",
    ],
    "Oscilação de energia": [
        "oscilação de energia",
        "variação de energia",
        "queda momentânea",
        "energia instável",
        "picos de energia",
        "flutuação elétrica",
    ],
    "Ocorrências sem registro de B.O": [
        "sem registro de b.o",
        "não foi lavrado boletim",
        "ocorrência sem b.o",
        "registro não efetuado",
        "sem boletim de ocorrência",
        "não registrado na polícia",
    ],
    "verificação": [
        "verificação no local",
        "checagem",
        "nada constatado",
        "averiguação",
        "foi feita ronda",
        "foi feita vistoria",
        "verificado sem alteração",
        "nada de anormal",
        "sem constatação",
    ],
}
