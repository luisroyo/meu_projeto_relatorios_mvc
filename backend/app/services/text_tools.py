from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from flask import current_app
from email import policy
from email.parser import BytesParser


ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTI_WS_RE = re.compile(r"[\t\x0b\x0c\r ]{2,}")
MULTI_NL_RE = re.compile(r"\n{3,}")


def clean_text(raw_text: str) -> str:
    """Remove formatações invisíveis e normaliza o texto.

    - Remove zero-width chars
    - Remove tags HTML
    - Normaliza unicode (NFC)
    - Converte NBSP em espaço normal
    - Colapsa espaços e quebras de linha excessivos
    """
    if not raw_text:
        return ""

    text = unicodedata.normalize("NFC", raw_text)
    text = text.replace("\u00A0", " ")
    text = ZERO_WIDTH_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    # normaliza espaços em linha
    def _collapse_ws_line(line: str) -> str:
        return MULTI_WS_RE.sub(" ", line).strip()

    lines = [ _collapse_ws_line(line) for line in text.split("\n") ]
    text = "\n".join(lines)
    text = MULTI_NL_RE.sub("\n\n", text).strip()
    return text


@dataclass
class LTMatch:
    message: str
    shortMessage: str
    offset: int
    length: int
    replacements: List[str]
    rule_id: str
    rule_description: str


def languagetool_check(text: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Chama LanguageTool (público ou self-hosted) se configurado.

    Retorna dict com lista de matches ou {'matches': []} em caso de indisponibilidade.
    """
    language = language or (current_app.config.get("DEFAULT_LANGUAGE") or "pt-BR")
    lt_base = current_app.config.get("LANGUAGE_TOOL_URL") or "https://api.languagetool.org"
    url = lt_base.rstrip("/") + "/v2/check"

    try:
        resp = requests.post(
            url,
            data={
                "text": text,
                "language": language,
            },
            timeout=8,
        )
        if resp.status_code != 200:
            return {"matches": [], "error": f"LT status {resp.status_code}"}
        data = resp.json()
        # Normaliza estrutura de retorno
        matches: List[Dict[str, Any]] = []
        for m in data.get("matches", []):
            matches.append(
                {
                    "message": m.get("message", ""),
                    "shortMessage": m.get("shortMessage", ""),
                    "offset": m.get("offset", 0),
                    "length": m.get("length", 0),
                    "replacements": [r.get("value") for r in m.get("replacements", [])][:5],
                    "rule": {
                        "id": (m.get("rule") or {}).get("id", ""),
                        "description": (m.get("rule") or {}).get("description", ""),
                    },
                }
            )
        return {"matches": matches}
    except Exception as e:
        return {"matches": [], "error": str(e)}


def ai_transform(text: str, mode: str = "formal", tone: Optional[str] = None, max_chars: Optional[int] = None) -> str:
    """Usa Google Generative AI para transformar o texto conforme o modo.

    mode: 'formal' | 'simplify' | 'tone' | 'summarize'
    tone: exemplo 'amigável', 'direto', etc. (apenas para mode='tone')
    """
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    if max_chars:
        cleaned = cleaned[:max_chars]

    # Import lazy para evitar overhead se não utilizado
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY_1") or os.environ.get("GOOGLE_API_KEY_2")
    if not api_key:
        return cleaned
    client = genai.Client(api_key=api_key)

    sys_prompt = (
        "Você é um assistente de escrita em PT-BR. Responda apenas com o texto transformado, sem comentários."
    )
    if mode == "formal":
        user_prompt = "Reescreva o texto a seguir em tom formal e profissional, mantendo significado:\n\n" + cleaned
    elif mode == "simplify":
        user_prompt = "Simplifique o texto a seguir (frases curtas, linguagem clara), mantendo o sentido:\n\n" + cleaned
    elif mode == "tone":
        t = tone or "amigável"
        user_prompt = f"Ajuste o tom do texto a seguir para um tom {t}, mantendo o sentido e a clareza:\n\n" + cleaned
    elif mode == "summarize":
        user_prompt = "Resuma o texto a seguir de forma objetiva (3-5 frases):\n\n" + cleaned
    else:
        user_prompt = cleaned

    # Nova API oficial
    full_prompt = f"{sys_prompt}\n\n{user_prompt}"
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    output = resp.text or ""
    return clean_text(output)


def parse_eml_to_text(eml_data: bytes | str) -> str:
    """Extrai texto legível de um arquivo .eml.

    - Prioriza partes text/plain
    - Se só houver text/html, remove tags básicas e preserva quebras
    - Decodifica quoted-printable/base64 automaticamente
    """
    if isinstance(eml_data, str):
        eml_bytes = eml_data.encode('utf-8', errors='ignore')
    else:
        eml_bytes = eml_data

    try:
        msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)
    except Exception:
        return clean_text(eml_data.decode('utf-8', errors='ignore') if isinstance(eml_data, (bytes, bytearray)) else eml_data)

    plain_parts: List[str] = []
    html_parts: List[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain':
                try:
                    plain_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b''
                    plain_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='ignore'))
            elif ctype == 'text/html':
                try:
                    html_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b''
                    html_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='ignore'))
    else:
        ctype = msg.get_content_type()
        try:
            content = msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True) or b''
            content = payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
        if ctype == 'text/plain':
            plain_parts.append(content)
        elif ctype == 'text/html':
            html_parts.append(content)

    if plain_parts:
        return clean_text("\n\n".join(plain_parts))

    # Converter HTML em texto simples básico
    def html_to_text(html: str) -> str:
        html = re.sub(r'<\s*br\s*/?>', '\n', html, flags=re.I)
        html = re.sub(r'</\s*p\s*>', '\n\n', html, flags=re.I)
        return clean_text(HTML_TAG_RE.sub('', html))

    if html_parts:
        return html_to_text("\n\n".join(html_parts))

    return ""


