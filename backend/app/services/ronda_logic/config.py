# config.py
import re

# --- Constantes de Expressões Regulares Pré-compiladas ---
REGEX_PREFIXO_LINHA = re.compile(
    r"^\s*\["  # Início da linha e '['
    r"([^,\]]*?)"  # Grupo 1: Hora do log no prefixo (ex: "19:41" ou "22:08")
    r"(?:[, ]\s*| )?"  # Separador opcional (vírgula ou espaço) ou apenas um espaço
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s*"  # Grupo 2: Data do log (DD/MM/YYYY ou DD/MM/YY) - AJUSTADO PARA ACEITAR ANO COM 2 OU 4 DIGITOS NA CAPTURA INICIAL
    r"\]\s*"  # Fim do ']' do prefixo
    r"(?:(VTR\s*\d+|Águia\s*\d+):\s*)?"  # Grupo 3 (opcional): Identificador da VTR (ex: "VTR 05:", "Águia 04:")
    r"(.*)$",  # Grupo 4: Restante da mensagem
    re.IGNORECASE,
)

REGEX_VTR_MENSAGEM_ALTERNATIVA = re.compile(
    r"^(VTR\s*\d+|Águia\s*\d+):\s*(.*)$", re.IGNORECASE
)

REGEX_VTR_LINHA_SIMPLES = re.compile(
    r"^(VTR\s*\d+|Águia\s*\d+)$", re.IGNORECASE
)

REGEX_BLOCO_DATA = re.compile(
    r"Data:\s*(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE
)
REGEX_BLOCO_INICIO = re.compile(
    r"In[ií]cio:\s*(\d{1,2}\s*[:;hH]\s*\d{1,2})", re.IGNORECASE
)
REGEX_BLOCO_TERMINO = re.compile(
    r"T[eé]rmino:\s*(\d{1,2}\s*[:;hH]\s*\d{1,2})", re.IGNORECASE
)
REGEX_BLOCO_QRA = re.compile(r"QRA\s+.*", re.IGNORECASE)

INICIO_KEYWORDS_REGEX_PART = (
    r"(?:[ií]n[ií]cio|in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou|inicial)"
)
TERMINO_KEYWORDS_REGEX_PART = r"(?:t[eé]rmino|termino|t[eé]rminou|terminou|fim|final|encerrou)"
TIPO_RONDA_REGEX_PART = r"(?:ronda|vigil[âa]ncia|patrulha)"
PREPOSICOES_ARTIGOS_REGEX_PART = r"(?:s\sde\s|\sde\s|\sda\s|\s)"

TIME_CAPTURE_REGEX_PART = r"(\d{1,2}\s*[:;hH]\s*\d{1,2})"
SIMPLE_HOUR_CAPTURE_REGEX_PART = r"(\d{1,2}\s*h(?!\d))"

LONE_TIME_CAPTURE_REGEX = re.compile(rf"^\s*{TIME_CAPTURE_REGEX_PART}\s*$", re.IGNORECASE)

# --- ALTERAÇÃO APLICADA AQUI ---
# Regex para capturar uma hora no início de uma linha para ser usada como contexto
CONTEXT_TIME_CAPTURE_REGEX = re.compile(rf"^\s*{TIME_CAPTURE_REGEX_PART}", re.IGNORECASE)


RONDA_EVENT_REGEX_PATTERNS = [
    # --- Padrões específicos para formatos como "Termino: 6:31", "Ínicio 06:11" e "Inicial 06:11" ---
    {"tipo": "inicio", "regex_str": rf"^{INICIO_KEYWORDS_REGEX_PART}\s+{TIME_CAPTURE_REGEX_PART}$"},
    {"tipo": "inicio", "regex_str": rf"^inicial\s+{TIME_CAPTURE_REGEX_PART}$"},
    {"tipo": "inicio", "regex_str": rf"^{TIME_CAPTURE_REGEX_PART}\s+inicial$"},
    {"tipo": "termino", "regex_str": rf"^{TERMINO_KEYWORDS_REGEX_PART}:\s*{TIME_CAPTURE_REGEX_PART}$"},
    {"tipo": "termino", "regex_str": rf"^{TERMINO_KEYWORDS_REGEX_PART}\s+{TIME_CAPTURE_REGEX_PART}$"},
    
    # Padrões com hora e minuto explícitos (hora primeiro)
    {"tipo": "inicio", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}.*?{INICIO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}.*?{TERMINO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}"},
    {"tipo": "inicio", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}.*?{INICIO_KEYWORDS_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}.*?{TERMINO_KEYWORDS_REGEX_PART}"},
    
    # Padrões com hora e minuto explícitos (palavra-chave primeiro)
    {"tipo": "inicio", "regex_str": rf"{INICIO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}.*?\s+{TIME_CAPTURE_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TERMINO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}.*?\s+{TIME_CAPTURE_REGEX_PART}"},
    {"tipo": "inicio", "regex_str": rf"{INICIO_KEYWORDS_REGEX_PART}.*?\s+{TIME_CAPTURE_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TERMINO_KEYWORDS_REGEX_PART}.*?\s+{TIME_CAPTURE_REGEX_PART}"},
    
    # Padrões curtos com hora e minuto explícitos
    {"tipo": "inicio", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}\s*{INICIO_KEYWORDS_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TIME_CAPTURE_REGEX_PART}\s*{TERMINO_KEYWORDS_REGEX_PART}"},
    {"tipo": "inicio", "regex_str": rf"{INICIO_KEYWORDS_REGEX_PART}\s*{TIME_CAPTURE_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TERMINO_KEYWORDS_REGEX_PART}\s*{TIME_CAPTURE_REGEX_PART}"},

    # Padrões com horas simples "HHh" (sem minutos explícitos)
    {"tipo": "inicio", "regex_str": rf"{SIMPLE_HOUR_CAPTURE_REGEX_PART}.*?{INICIO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{SIMPLE_HOUR_CAPTURE_REGEX_PART}.*?{TERMINO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}"},
    {"tipo": "inicio", "regex_str": rf"{INICIO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}.*?\s+{SIMPLE_HOUR_CAPTURE_REGEX_PART}"},
    {"tipo": "termino", "regex_str": rf"{TERMINO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}.*?\s+{SIMPLE_HOUR_CAPTURE_REGEX_PART}"},
    
    # Padrões que detectam apenas a palavra-chave (sem hora) para a lógica de bloco
    {"tipo": "inicio", "regex_str": rf"^\s*{INICIO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}\s*$", "keyword_only": True},
    {"tipo": "termino", "regex_str": rf"^\s*{TERMINO_KEYWORDS_REGEX_PART}{PREPOSICOES_ARTIGOS_REGEX_PART}{TIPO_RONDA_REGEX_PART}\s*$", "keyword_only": True},
    {"tipo": "inicio", "regex_str": rf"^\s*{INICIO_KEYWORDS_REGEX_PART}\s*$", "keyword_only": True},
    {"tipo": "termino", "regex_str": rf"^\s*{TERMINO_KEYWORDS_REGEX_PART}\s*$", "keyword_only": True},
]

COMPILED_RONDA_EVENT_REGEXES = [
    {
        "tipo": p["tipo"],
        "regex": re.compile(p["regex_str"], re.IGNORECASE),
        "keyword_only": p.get("keyword_only", False),
    }
    for p in RONDA_EVENT_REGEX_PATTERNS
]

DEFAULT_VTR_ID = "VTR_DESCONHECIDA"
FALLBACK_DATA_INDEFINIDA = "[Data Indefinida]"
FALLBACK_ESCALA_NAO_INFORMADA = "[Escala não Informada]"