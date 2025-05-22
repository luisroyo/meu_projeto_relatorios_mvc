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

RONDA_EVENT_REGEX_PATTERNS = [
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*:\s*\d{2}).*?(?:in[ií]cio|inicio)(?:s\sde\s|\sde\s|\s)ronda"},
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*:\s*\d{2}).*?(?:t[ée]rmino|termino)(?:s\sde\s|\sde\s|\s)ronda"},
    {"tipo": "inicio", "regex_str": r"(\d{1,2}\s*:\s*\d{2}).*?(?:in[ií]cio|inicio)"},
    {"tipo": "termino", "regex_str": r"(\d{1,2}\s*:\s*\d{2}).*?(?:t[ée]rmino|termino)"},
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio)(?:s\sde\s|\sde\s|\s)ronda.*?\s+(\d{1,2}\s*:\s*\d{2})"},
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino)(?:s\sde\s|\sde\s|\s)ronda.*?\s+(\d{1,2}\s*:\s*\d{2})"},
    {"tipo": "inicio", "regex_str": r"(?:in[ií]cio|inicio).*?\s+(\d{1,2}\s*:\s*\d{2})"},
    {"tipo": "termino", "regex_str": r"(?:t[ée]rmino|termino).*?\s+(\d{1,2}\s*:\s*\d{2})"},
]

COMPILED_RONDA_EVENT_REGEXES = [
    {"tipo": p["tipo"], "regex": re.compile(p["regex_str"], re.IGNORECASE)}
    for p in RONDA_EVENT_REGEX_PATTERNS
]

DEFAULT_VTR_ID = "VTR_DESCONHECIDA"
FALLBACK_DATA_INDEFINIDA = "[Data Indefinida]"
FALLBACK_ESCALA_NAO_INFORMADA = "[Escala não Informada]"