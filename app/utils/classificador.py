# utils/classificador.py
import unicodedata
from app.classificador_config import MAPA_PALAVRAS_CHAVE_TIPO


def normalizar_texto(texto):
    """Remove acentuação e converte para minúsculas."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("utf-8")
    return texto.lower()


def classificar_ocorrencia(texto):
    """
    Retorna o tipo de ocorrência com base no texto informado.
    Se nenhuma palavra-chave for encontrada, retorna None.
    """
    texto_normalizado = normalizar_texto(texto)

    for tipo, palavras_chave in MAPA_PALAVRAS_CHAVE_TIPO.items():
        for palavra in palavras_chave:
            if normalizar_texto(palavra) in texto_normalizado:
                return tipo

    return None
