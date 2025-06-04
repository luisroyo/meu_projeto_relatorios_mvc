# config.py
import re

# --- Constantes de Expressões Regulares Pré-compiladas ---
REGEX_PREFIXO_LINHA = re.compile(
    r"^\s*\["                          # Início da linha e '['
    r"(?:[^,\]]*?)"                    # Qualquer coisa que não seja vírgula ou ']', opcional (para a hora do prefixo)
    r"(?:[, ]\s*| )?"                  # Separador opcional (vírgula ou espaço) ou apenas um espaço
    r"(\d{1,2}/\d{1,2}/\d{4})\s*"      # Grupo 1: Data do log (DD/MM/YYYY)
    r"\]\s*"                           # Fim do ']' do prefixo
    r"(?:(VTR\s*\d+|Águia\s*\d+):\s*)?" # Grupo 2 (opcional): Identificador da VTR (ex: "VTR 05:", "Águia 04:")
    r"(.*)$",                          # Grupo 3: Restante da mensagem
    re.IGNORECASE
)

REGEX_VTR_MENSAGEM_ALTERNATIVA = re.compile(r"^(VTR\s*\d+|Águia\s*\d+):\s*(.*)$", re.IGNORECASE)

REGEX_BLOCO_DATA = re.compile(r"Data:\s*(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE)
# Para REGEX_BLOCO_INICIO e _TERMINO, a hora já é capturada de forma mais genérica (aceitando : ou h)
# e normalizar_hora_capturada lidará com isso. Se precisarmos de ; aqui também, mudaremos.
# Por ora, vamos focar nas regex de evento na mensagem.
REGEX_BLOCO_INICIO = re.compile(r"In[ií]cio:\s*(\d{1,2}\s*[:;hH]\s*\d{1,2})", re.IGNORECASE)
REGEX_BLOCO_TERMINO = re.compile(r"T[eé]rmino:\s*(\d{1,2}\s*[:;hH]\s*\d{1,2})", re.IGNORECASE)
REGEX_BLOCO_QRA = re.compile(r"QRA\s+.*", re.IGNORECASE) 

INICIO_KEYWORDS_REGEX_PART = r"(?:[ií]n[ií]cio|in[ií]cio|inicio|iniciou|come[cç]o|come[cç]ou)"
TERMINO_KEYWORDS_REGEX_PART = r"(?:t[eé]rmino|termino|t[eé]rminou|terminou|fim|final|encerrou)"
TIPO_RONDA_REGEX_PART = r"(?:ronda|vigil[âa]ncia|patrulha)"
PREPOSICOES_ARTIGOS_REGEX_PART = r"(?:s\sde\s|\sde\s|\sda\s|\s)"

# ATUALIZADO: Grupo de captura de hora agora inclui ';' e espera HH e MM (ou M)
TIME_CAPTURE_REGEX_PART = r"(\d{1,2}\s*[:;hH]\s*\d{1,2})" # Ex: 19:20, 03;19, 8h30
# Para horas como "06h" (sem minutos explícitos)
SIMPLE_HOUR_CAPTURE_REGEX_PART = r"(\d{1,2}\s*h(?!\d))"


RONDA_EVENT_REGEX_PATTERNS = [
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
]

COMPILED_RONDA_EVENT_REGEXES = [
    {"tipo": p["tipo"], "regex": re.compile(p["regex_str"], re.IGNORECASE)}
    for p in RONDA_EVENT_REGEX_PATTERNS
]

DEFAULT_VTR_ID = "VTR_DESCONHECIDA"
FALLBACK_DATA_INDEFINIDA = "[Data Indefinida]"
FALLBACK_ESCALA_NAO_INFORMADA = "[Escala não Informada]"