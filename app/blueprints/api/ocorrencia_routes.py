from flask import request, jsonify
from flask_cors import cross_origin
from app import csrf
import re
from datetime import datetime
from app.models import Condominio, Colaborador, VWColaboradores, VWLogradouros
from app.utils.classificador import classificar_ocorrencia
from app.services.patrimonial_report_service import PatrimonialReportService
from app.models.ocorrencia import Ocorrencia
from app.models.condominio import Condominio
from app.models.ocorrencia_tipo import OcorrenciaTipo
from app.models.user import User
from app.models.colaborador import Colaborador
from app.models.orgao_publico import OrgaoPublico
from app.services import ocorrencia_service
from app import db
from . import api_bp

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
    # 4. IA - Corrigir relatório
    service = PatrimonialReportService()
    relatorio_corrigido = service.gerar_relatorio_seguranca(texto)
    dados_extraidos["relatorio_corrigido"] = relatorio_corrigido
    return jsonify({"sucesso": True, "dados": dados_extraidos})

@api_bp.route("/colaboradores", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_colaboradores():
    nome = request.args.get("nome", type=str)
    query = Colaborador.query
    if nome:
        query = query.filter(Colaborador.nome_completo.ilike(f"%{nome}%"))
    colaboradores = query.all()
    resultado = []
    for c in colaboradores:
        resultado.append({
            "id": c.id,
            "nome_completo": c.nome_completo,
            "cargo": c.cargo,
            "matricula": c.matricula,
            "data_admissao": c.data_admissao.isoformat() if c.data_admissao else None,
            "status": c.status,
            "data_criacao": c.data_criacao.isoformat() if c.data_criacao else None,
            "data_modificacao": c.data_modificacao.isoformat() if c.data_modificacao else None
        })
    return jsonify({"colaboradores": resultado})

@api_bp.route("/colaboradores_view", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_colaboradores_view():
    nome = request.args.get("nome", type=str)
    query = VWColaboradores.query
    if nome:
        query = query.filter(VWColaboradores.nome_completo.ilike(f"%{nome}%"))
    colaboradores = query.all()
    resultado = [
        {
            "id": c.id,
            "nome_completo": c.nome_completo,
            "cargo": c.cargo,
            "matricula": c.matricula,
            "data_admissao": c.data_admissao.isoformat() if c.data_admissao else None,
            "status": c.status,
            "data_criacao": c.data_criacao.isoformat() if c.data_criacao else None,
            "data_modificacao": c.data_modificacao.isoformat() if c.data_modificacao else None
        }
        for c in colaboradores
    ]
    return jsonify({"colaboradores": resultado})

@api_bp.route("/logradouros_view", methods=["GET"])
@cross_origin()
@csrf.exempt
def listar_logradouros_view():
    nome = request.args.get("nome", type=str)
    query = VWLogradouros.query
    if nome:
        query = query.filter(VWLogradouros.nome.ilike(f"%{nome}%"))
    logradouros = query.all()
    resultado = [
        {"id": l.id, "nome": l.nome}
        for l in logradouros
    ]
    return jsonify({"logradouros": resultado})

@api_bp.route("/ocorrencias/historico", methods=["GET"])
@cross_origin()
@csrf.exempt
def historico_ocorrencias():
    # Filtros opcionais
    status = request.args.get("status")
    condominio_id = request.args.get("condominio_id", type=int)
    tipo_id = request.args.get("tipo_id", type=int)
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    supervisor_id = request.args.get("supervisor_id", type=int)

    filters = {}
    if status:
        filters["status"] = status
    if condominio_id:
        filters["condominio_id"] = condominio_id
    if tipo_id:
        filters["tipo_id"] = tipo_id
    if data_inicio:
        filters["data_inicio_str"] = data_inicio
    if data_fim:
        filters["data_fim_str"] = data_fim
    if supervisor_id:
        filters["supervisor_id"] = supervisor_id

    query = Ocorrencia.query
    query = ocorrencia_service.apply_ocorrencia_filters(query, filters)
    query = query.order_by(Ocorrencia.data_hora_ocorrencia.desc())
    ocorrencias = query.limit(100).all()  # Limite de 100 para evitar resposta gigante

    def serialize_ocorrencia(o):
        return {
            "id": o.id,
            "relatorio_final": o.relatorio_final,
            "data_hora_ocorrencia": o.data_hora_ocorrencia.isoformat() if o.data_hora_ocorrencia else None,
            "turno": o.turno,
            "status": o.status,
            "endereco_especifico": o.endereco_especifico,
            "condominio": o.condominio.nome if o.condominio else None,
            "tipo": o.tipo.nome if o.tipo else None,
            "supervisor": o.supervisor_id,
            "colaboradores": [c.nome_completo for c in o.colaboradores_envolvidos],
            "orgaos_acionados": [org.nome for org in o.orgaos_acionados],
            "data_criacao": o.data_criacao.isoformat() if o.data_criacao else None,
            "data_modificacao": o.data_modificacao.isoformat() if o.data_modificacao else None
        }
    resultado = [serialize_ocorrencia(o) for o in ocorrencias]
    return jsonify({"historico": resultado})

@api_bp.route("/ocorrencias/<int:id>", methods=["GET", "OPTIONS"])
@cross_origin()
@csrf.exempt
def detalhe_ocorrencia(id):
    if request.method == "OPTIONS":
        return '', 200
    ocorrencia = Ocorrencia.query.get_or_404(id)
    resultado = {
        "id": ocorrencia.id,
        "relatorio_final": ocorrencia.relatorio_final,
        "data_hora_ocorrencia": ocorrencia.data_hora_ocorrencia.isoformat() if ocorrencia.data_hora_ocorrencia else None,
        "turno": ocorrencia.turno,
        "status": ocorrencia.status,
        "endereco_especifico": ocorrencia.endereco_especifico,
        "condominio": ocorrencia.condominio.nome if ocorrencia.condominio else None,
        "tipo": ocorrencia.tipo.nome if ocorrencia.tipo else None,
        "supervisor": ocorrencia.supervisor_id,
        "colaboradores": [c.nome_completo for c in ocorrencia.colaboradores_envolvidos],
        "orgaos_acionados": [org.nome for org in ocorrencia.orgaos_acionados],
        "data_criacao": ocorrencia.data_criacao.isoformat() if ocorrencia.data_criacao else None,
        "data_modificacao": ocorrencia.data_modificacao.isoformat() if ocorrencia.data_modificacao else None
    }
    return jsonify(resultado)

@api_bp.route("/ocorrencias/salvar", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def salvar_ocorrencia():
    if request.method == "OPTIONS":
        return '', 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"sucesso": False, "message": "Dados não fornecidos."}), 400

        # Campos obrigatórios
        relatorio_final = data.get("relatorio_final")
        if not relatorio_final:
            return jsonify({"sucesso": False, "message": "Relatório final é obrigatório."}), 400

        # Criar nova ocorrência
        nova_ocorrencia = Ocorrencia(
            relatorio_final=relatorio_final,
            status="Pendente",  # Status especial para indicar que precisa ser revisada
            data_hora_ocorrencia=datetime.utcnow(),
            turno=data.get("turno", "Diurno"),
            endereco_especifico=data.get("endereco_especifico", ""),
            condominio_id=data.get("condominio_id"),
            ocorrencia_tipo_id=data.get("ocorrencia_tipo_id"),
            registrado_por_user_id=data.get("registrado_por_user_id"),
            supervisor_id=data.get("supervisor_id")
        )

        # Salvar no banco
        db.session.add(nova_ocorrencia)
        db.session.commit()

        return jsonify({
            "sucesso": True,
            "message": "Ocorrência salva com sucesso. Aguardando revisão.",
            "ocorrencia_id": nova_ocorrencia.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "message": f"Erro ao salvar ocorrência: {str(e)}"}), 500 