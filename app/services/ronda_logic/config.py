# config.py
import re

# --- Constantes de Expressões Regulares Pré-compiladas ---
REGEX_PREFIXO_LINHA = re.compile(
    r"^\s*\["                          # Início da linha e '['
    r"(?:[^,\]]*?)"                    # Qualquer coisa que não seja vírgula ou ']', opcional (para a hora do prefixo)
    r"(?:[, ]\s*| )?"                  # Separador opcional (vírgula ou espaço) ou apenas um espaço
    r"(\d{1,2}/\d{1,2}/\d{4})\s*"      # Grupo 1: Data do log (DD/MM/YYYY)
    r"\]\s*"                           # Fim do ']' do prefixo
    r"(?:(VTR\s*\d+):\s*)?"            # Grupo 2 (opcional): Identificador da VTR (ex: "VTR 05:")
    r"(.*)$",                          # Grupo 3: Restante da mensagem
    re.IGNORECASE
)

REGEX_VTR_MENSAGEM_ALTERNATIVA = re.compile(r"^(VTR\s*\d+):\s*(.*)$", re.IGNORECASE)

# Padrões expandidos para eventos de ronda
RONDA_EVENT_REGEX_PATTERNS = [
    # Padrões existentes (hora primeiro)
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2}).*?(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha)"},
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2}).*?(?:t[ée]rmino|termino|terminou|fim|final|encerrou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha)"},
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2}).*?(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)"}, # Sem "ronda" explícito
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2}).*?(?:t[ée]rmino|termino|terminou|fim|final|encerrou)"}, # Sem "ronda" explícito

    # Padrões com palavra-chave primeiro, depois hora
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha).*?\s+(\d{1,2}\s*[:hH]\s*\d{2})"},
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino|terminou|fim|final|encerrou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha).*?\s+(\d{1,2}\s*[:hH]\s*\d{2})"},
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou).*?\s+(\d{1,2}\s*[:hH]\s*\d{2})"}, # Sem "ronda" explícito
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino|terminou|fim|final|encerrou).*?\s+(\d{1,2}\s*[:hH]\s*\d{2})"}, # Sem "ronda" explícito

    # Padrões muito curtos (apenas hora e palavra-chave, para capturas mais difíceis)
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2})\s*(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)"},
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*[:hH]\s*\d{2})\s*(?:t[ée]rmino|termino|terminou|fim|final|encerrou)"},
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)\s*(\d{1,2}\s*[:hH]\s*\d{2})"},
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino|terminou|fim|final|encerrou)\s*(\d{1,2}\s*[:hH]\s*\d{2})"},

    # Padrões que podem capturar horas como "HHh" (ex: 06h, 18h)
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*h(?!\d)).*?(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha)"}, # ex: 06h inicio de ronda
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*h(?!\d)).*?(?:t[ée]rmino|termino|terminou|fim|final|encerrou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha)"}, # ex: 18h termino de ronda
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha).*?\s+(\d{1,2}\s*h(?!\d))"}, # ex: inicio de ronda 06h
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino|terminou|fim|final|encerrou)(?:s\sde\s|\sde\s|\sda\s|\s)(?:ronda|vigil[âa]ncia|patrulha).*?\s+(\d{1,2}\s*h(?!\d))"}, # ex: termino de ronda 18h

]

COMPILED_RONDA_EVENT_REGEXES = [
    {"tipo": p["tipo"], "regex": re.compile(p["regex_str"], re.IGNORECASE)}
    for p in RONDA_EVENT_REGEX_PATTERNS
]

DEFAULT_VTR_ID = "VTR_DESCONHECIDA"
FALLBACK_DATA_INDEFINIDA = "[Data Indefinida]"
FALLBACK_ESCALA_NAO_INFORMADA = "[Escala não Informada]"