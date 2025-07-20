from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from app import csrf
import re
from datetime import datetime
from app.models import Condominio
from app.utils.classificador import classificar_ocorrencia

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/ocorrencias/analisar-relatorio", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def analisar_relatorio_api():
    if request.method == "OPTIONS":
        return '', 200
    data = request.get_json()
    texto = data.get("texto_relatorio", "")
    if not texto:
        return jsonify({"sucesso": False, "message": "Texto do relatório está vazio."}), 400
    texto_limpo = texto.replace("\xa0", " ").strip()
    dados_extraidos = {}
    # 1. DATA, HORA E TURNO
    match_data = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", texto_limpo)
    match_hora = re.search(r"Hora:\s*(\d{2}:\d{2})", texto_limpo)
    if match_data and match_hora:
        data_str, hora_str = match_data.group(1).strip(), match_hora.group(1).strip()
        try:
            datetime_obj = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
            dados_extraidos["data_hora_ocorrencia"] = datetime_obj.strftime("%Y-%m-%dT%H:%M")
            dados_extraidos["turno"] = (
                "Noturno" if 18 <= datetime_obj.hour or datetime_obj.hour < 6 else "Diurno"
            )
        except ValueError:
            pass
    # 2. LOCAL, ENDEREÇO E CONDOMÍNIO
    match_local = re.search(r"Local:\s*([^\n\r]+)", texto_limpo)
    if match_local:
        endereco_completo = match_local.group(1).strip()
        dados_extraidos["endereco_especifico"] = endereco_completo
        condominio_encontrado = next(
            (c for c in Condominio.query.all() if c.nome.lower() in endereco_completo.lower()),
            None,
        )
        if condominio_encontrado:
            dados_extraidos["condominio_id"] = condominio_encontrado.id
    # 3. TIPO DA OCORRÊNCIA
    nome_tipo_encontrado = classificar_ocorrencia(texto_limpo)
    if nome_tipo_encontrado:
        dados_extraidos["tipo_ocorrencia"] = nome_tipo_encontrado
    return jsonify({"sucesso": True, "dados": dados_extraidos}) 