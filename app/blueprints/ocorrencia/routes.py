# app/blueprints/ocorrencia/routes.py

import logging
import re
from datetime import datetime
from functools import wraps

import pytz
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from flask_cors import cross_origin
from flask_wtf import csrf

from app import db
from app.forms import OcorrenciaForm
from app.models import (Colaborador, Condominio, Ocorrencia, OcorrenciaTipo,
                        OrgaoPublico, User)
## [ADICIONADO] Importa o novo serviço de ocorrência para usar a função de filtro
from app.services import ocorrencia_service
from app.utils.classificador import classificar_ocorrencia

logger = logging.getLogger(__name__)

ocorrencia_bp = Blueprint(
    "ocorrencia", __name__, template_folder="templates", url_prefix="/ocorrencias"
)


# --- Funções Auxiliares ---
def local_to_utc(dt_naive, timezone_str=None):
    """Converte datetime ingênuo (sem tzinfo) local para datetime UTC com tzinfo."""
    ## [MELHORIA] Usa o timezone da configuração da app, com um fallback.
    if not timezone_str:
        timezone_str = current_app.config.get("DEFAULT_TIMEZONE", "America/Sao_Paulo")

    local_tz = pytz.timezone(timezone_str)
    aware_local = local_tz.localize(dt_naive)
    utc_dt = aware_local.astimezone(pytz.utc)
    return utc_dt


def populate_ocorrencia_form_choices(form):
    form.condominio_id.choices = [("", "-- Selecione um Condomínio --")] + [
        (str(c.id), c.nome) for c in Condominio.query.order_by("nome").all()
    ]
    form.ocorrencia_tipo_id.choices = [("", "-- Selecione um Tipo --")] + [
        (str(t.id), t.nome) for t in OcorrenciaTipo.query.order_by("nome").all()
    ]
    form.orgaos_acionados.choices = [
        (str(o.id), o.nome) for o in OrgaoPublico.query.order_by("nome").all()
    ]
    form.colaboradores_envolvidos.choices = [
        (str(col.id), col.nome_completo)
        for col in Colaborador.query.filter_by(status="Ativo")
        .order_by("nome_completo")
        .all()
    ]
    form.supervisor_id.choices = [("", "-- Selecione um Supervisor --")] + [
        (str(s.id), s.username)
        for s in User.query.filter_by(is_supervisor=True, is_approved=True)
        .order_by("username")
        .all()
    ]


def pode_editar_ocorrencia(f):
    @wraps(f)
    def decorated_function(ocorrencia_id, *args, **kwargs):
        ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
        if not (
            current_user.is_admin
            or current_user.id == ocorrencia.registrado_por_user_id
        ):
            flash("Você não tem permissão para editar esta ocorrência.", "danger")
            return redirect(
                url_for("ocorrencia.detalhes_ocorrencia", ocorrencia_id=ocorrencia.id)
            )
        return f(ocorrencia_id, *args, **kwargs)

    return decorated_function


# --- Rotas ---
@ocorrencia_bp.route("/historico")
@login_required
def listar_ocorrencias():
    page = request.args.get("page", 1, type=int)

    # Coleta todos os argumentos de filtro em um dicionário
    filters = {
        "status": request.args.get("status", ""),
        "condominio_id": request.args.get("condominio_id", type=int),
        "supervisor_id": request.args.get("supervisor_id", type=int),
        "tipo_id": request.args.get("tipo_id", type=int),
        "data_inicio": request.args.get("data_inicio", ""),
        "data_fim": request.args.get("data_fim", ""),
        "texto_relatorio": request.args.get("texto_relatorio", ""),
    }

    query = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.tipo),
        db.joinedload(Ocorrencia.registrado_por),
        db.joinedload(Ocorrencia.condominio),
        db.joinedload(Ocorrencia.supervisor),
    )

    ## [REMOVIDO] Bloco inteiro de IFs para filtragem manual foi removido daqui.
    # if selected_status: query = query.filter(Ocorrencia.status == selected_status)
    # ... e todos os outros ifs ...

    ## [ADICIONADO] Chamada única para a função de serviço centralizada.
    query = ocorrencia_service.apply_ocorrencia_filters(query, filters)

    ocorrencias_pagination = query.order_by(
        Ocorrencia.data_hora_ocorrencia.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    # Carrega dados para preencher os formulários de filtro no template
    condominios = Condominio.query.order_by(Condominio.nome).all()
    supervisors = (
        User.query.filter_by(is_supervisor=True, is_approved=True)
        .order_by(User.username)
        .all()
    )
    tipos_ocorrencia = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    status_list = [
        "Registrada",
        "Em Andamento",
        "Concluída",
        "Pendente",
        "Rejeitada"
    ]

    filter_args = {k: v for k, v in request.args.items() if k != "page"}

    return render_template(
        "ocorrencia/list.html",
        title="Histórico de Ocorrências",
        ocorrencias_pagination=ocorrencias_pagination,
        condominios=condominios,
        supervisors=supervisors,
        tipos_ocorrencia=tipos_ocorrencia,
        status_list=status_list,
        selected_status=filters["status"],
        selected_condominio_id=filters["condominio_id"],
        selected_supervisor_id=filters["supervisor_id"],
        selected_tipo_id=filters["tipo_id"],
        selected_data_inicio=filters["data_inicio"],
        selected_data_fim=filters["data_fim"],
        filter_args=filter_args,
        texto_relatorio=filters["texto_relatorio"],
    )


## O restante do arquivo (registrar, editar, deletar, analisar) permanece o mesmo.
@ocorrencia_bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_ocorrencia():
    form = OcorrenciaForm()
    populate_ocorrencia_form_choices(form)

    if request.method == "GET":
        if request.args.get("relatorio_final"):
            form.relatorio_final.data = request.args.get("relatorio_final")
        form.data_hora_ocorrencia.data = datetime.now()

    if form.validate_on_submit():
        try:
            tipo_ocorrencia_id = form.ocorrencia_tipo_id.data
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter(
                    OcorrenciaTipo.nome.ilike(form.novo_tipo_ocorrencia.data.strip())
                ).first()
                if tipo_existente:
                    tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(
                        nome=form.novo_tipo_ocorrencia.data.strip()
                    )
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            
            # Validação adicional para garantir que tipo_ocorrencia_id não seja None
            if not tipo_ocorrencia_id:
                # Busca um tipo padrão se nenhum foi selecionado
                tipo_padrao = OcorrenciaTipo.query.filter_by(nome="verificação").first()
                if not tipo_padrao:
                    # Cria o tipo padrão se não existir
                    tipo_padrao = OcorrenciaTipo(nome="verificação")
                    db.session.add(tipo_padrao)
                    db.session.flush()
                tipo_ocorrencia_id = tipo_padrao.id

            utc_datetime = None
            if form.data_hora_ocorrencia.data:
                utc_datetime = local_to_utc(form.data_hora_ocorrencia.data)

            nova_ocorrencia = Ocorrencia(
                condominio_id=form.condominio_id.data,
                data_hora_ocorrencia=utc_datetime,
                turno=form.turno.data,
                relatorio_final=form.relatorio_final.data,
                status=form.status.data,
                endereco_especifico=form.endereco_especifico.data,
                ocorrencia_tipo_id=tipo_ocorrencia_id,
                registrado_por_user_id=current_user.id,
                supervisor_id=form.supervisor_id.data,
            )
            if form.orgaos_acionados.data:
                orgaos = OrgaoPublico.query.filter(
                    OrgaoPublico.id.in_(form.orgaos_acionados.data)
                ).all()
                nova_ocorrencia.orgaos_acionados.extend(orgaos)
            if form.colaboradores_envolvidos.data:
                colaboradores = Colaborador.query.filter(
                    Colaborador.id.in_(form.colaboradores_envolvidos.data)
                ).all()
                nova_ocorrencia.colaboradores_envolvidos.extend(colaboradores)

            db.session.add(nova_ocorrencia)
            db.session.commit()
            flash("Ocorrência registrada com sucesso!", "success")
            return redirect(
                url_for(
                    "ocorrencia.detalhes_ocorrencia", ocorrencia_id=nova_ocorrencia.id
                )
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar nova ocorrência: {e}", exc_info=True)
            flash(f"Erro ao salvar a ocorrência: {e}", "danger")

    return render_template(
        "ocorrencia/form_direto.html", title="Registrar Nova Ocorrência", form=form
    )


@ocorrencia_bp.route("/detalhes/<int:ocorrencia_id>")
@login_required
def detalhes_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    return render_template(
        "ocorrencia/details.html",
        title=f"Detalhes da Ocorrência #{ocorrencia.id}",
        ocorrencia=ocorrencia,
    )


@ocorrencia_bp.route("/editar/<int:ocorrencia_id>", methods=["GET", "POST"])
@login_required
@pode_editar_ocorrencia
def editar_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    form = OcorrenciaForm(obj=ocorrencia)
    populate_ocorrencia_form_choices(form)

    if request.method == "GET":
        form.colaboradores_envolvidos.data = [
            col.id for col in ocorrencia.colaboradores_envolvidos
        ]
        form.orgaos_acionados.data = [org.id for org in ocorrencia.orgaos_acionados]

    if form.validate_on_submit():
        try:
            # Popula apenas os campos simples, exceto os relacionamentos
            campos_simples = [
                "condominio_id", "data_hora_ocorrencia", "turno", "relatorio_final",
                "status", "endereco_especifico", "ocorrencia_tipo_id", "supervisor_id"
            ]
            for campo in campos_simples:
                if hasattr(form, campo) and hasattr(ocorrencia, campo):
                    setattr(ocorrencia, campo, getattr(form, campo).data)

            # Lida com o datetime
            if form.data_hora_ocorrencia.data:
                ocorrencia.data_hora_ocorrencia = local_to_utc(
                    form.data_hora_ocorrencia.data
                )

            # Lida com relacionamentos Many-to-Many
            colaboradores = Colaborador.query.filter(
                Colaborador.id.in_(form.colaboradores_envolvidos.data or [])
            ).all()
            ocorrencia.colaboradores_envolvidos = colaboradores

            orgaos = OrgaoPublico.query.filter(
                OrgaoPublico.id.in_(form.orgaos_acionados.data or [])
            ).all()
            ocorrencia.orgaos_acionados = orgaos

            db.session.commit()
            flash("Ocorrência atualizada com sucesso!", "success")
            return redirect(
                url_for("ocorrencia.detalhes_ocorrencia", ocorrencia_id=ocorrencia.id)
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar ocorrência: {e}", exc_info=True)
            flash(f"Erro ao atualizar a ocorrência: {e}", "danger")

    return render_template(
        "ocorrencia/form_direto.html",
        title=f"Editar Ocorrência #{ocorrencia.id}",
        form=form,
    )


@ocorrencia_bp.route("/deletar/<int:ocorrencia_id>", methods=["POST"])
@login_required
def deletar_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    if not (
        current_user.is_admin or current_user.id == ocorrencia.registrado_por_user_id
    ):
        flash("Você não tem permissão para deletar esta ocorrência.", "danger")
        return redirect(url_for("ocorrencia.listar_ocorrencias"))
    try:
        db.session.delete(ocorrencia)
        db.session.commit()
        flash("Ocorrência deletada com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar a ocorrência: {e}", "danger")
    return redirect(url_for("ocorrencia.listar_ocorrencias"))


@ocorrencia_bp.route("/aprovar/<int:ocorrencia_id>", methods=["POST"])
@login_required
def aprovar_ocorrencia(ocorrencia_id):
    """Aprova uma ocorrência pendente, mudando o status para 'Registrada'."""
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    
    if ocorrencia.status != "Pendente":
        flash("Apenas ocorrências pendentes podem ser aprovadas.", "warning")
        return redirect(url_for("ocorrencia.detalhes_ocorrencia", ocorrencia_id=ocorrencia.id))
    
    try:
        ocorrencia.status = "Registrada"
        db.session.commit()
        flash("Ocorrência aprovada com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao aprovar ocorrência: {e}", "danger")
    
    return redirect(url_for("ocorrencia.detalhes_ocorrencia", ocorrencia_id=ocorrencia.id))


@ocorrencia_bp.route("/rejeitar/<int:ocorrencia_id>", methods=["POST"])
@login_required
def rejeitar_ocorrencia(ocorrencia_id):
    """Rejeita uma ocorrência pendente, mudando o status para 'Rejeitada'."""
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    
    if ocorrencia.status != "Pendente":
        flash("Apenas ocorrências pendentes podem ser rejeitadas.", "warning")
        return redirect(url_for("ocorrencia.detalhes_ocorrencia", ocorrencia_id=ocorrencia.id))
    
    try:
        ocorrencia.status = "Rejeitada"
        db.session.commit()
        flash("Ocorrência rejeitada.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao rejeitar ocorrência: {e}", "danger")
    
    return redirect(url_for("ocorrencia.listar_ocorrencias"))


@ocorrencia_bp.route("/analisar-relatorio", methods=["POST", "OPTIONS"])
@cross_origin()
def analisar_relatorio():
    if request.method == "OPTIONS":
        return '', 200
    data = request.get_json()
    texto = data.get("texto_relatorio", "")
    if not texto:
        return (
            jsonify({"sucesso": False, "message": "Texto do relatório está vazio."}),
            400,
        )

    texto_limpo = texto.replace("\xa0", " ").strip()

    dados_extraidos = {}

    # 1. DATA, HORA E TURNO
    match_data = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", texto_limpo)
    match_hora = re.search(r"Hora:\s*(\d{2}:\d{2})", texto_limpo)
    if match_data and match_hora:
        data_str, hora_str = match_data.group(1).strip(), match_hora.group(1).strip()
        try:
            datetime_obj = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
            dados_extraidos["data_hora_ocorrencia"] = datetime_obj.strftime(
                "%Y-%m-%dT%H:%M"
            )
            dados_extraidos["turno"] = (
                "Noturno"
                if 18 <= datetime_obj.hour or datetime_obj.hour < 6
                else "Diurno"
            )
        except ValueError:
            pass

    # 2. LOCAL, ENDEREÇO E CONDOMÍNIO
    match_local = re.search(r"Local:\s*([^\n\r]+)", texto_limpo)
    if match_local:
        endereco_completo = match_local.group(1).strip()
        dados_extraidos["endereco_especifico"] = endereco_completo
        # Lógica para encontrar condomínio...
        condominio_encontrado = next(
            (
                c
                for c in Condominio.query.all()
                if c.nome.lower() in endereco_completo.lower()
            ),
            None,
        )
        if condominio_encontrado:
            dados_extraidos["condominio_id"] = condominio_encontrado.id

    # 3. TIPO DA OCORRÊNCIA
    nome_tipo_encontrado = classificar_ocorrencia(texto_limpo)
    if nome_tipo_encontrado:
        tipo_obj = OcorrenciaTipo.query.filter(
            OcorrenciaTipo.nome.ilike(nome_tipo_encontrado)
        ).first()
        if tipo_obj:
            dados_extraidos["ocorrencia_tipo_id"] = tipo_obj.id
        else:
            # Se o tipo não existir no banco, cria um novo
            novo_tipo = OcorrenciaTipo(nome=nome_tipo_encontrado)
            db.session.add(novo_tipo)
            db.session.flush()
            dados_extraidos["ocorrencia_tipo_id"] = novo_tipo.id
    else:
        # Se nenhum tipo for encontrado, usa o tipo padrão
        tipo_padrao = OcorrenciaTipo.query.filter_by(nome="verificação").first()
        if tipo_padrao:
            dados_extraidos["ocorrencia_tipo_id"] = tipo_padrao.id

    # 4. RESPONSÁVEL (COLABORADOR)
    match_responsavel = re.search(
        r"Responsável pelo registro:\s*([^\n\r(]+)", texto_limpo
    )
    if match_responsavel:
        nome_responsavel = match_responsavel.group(1).strip()
        colaborador = Colaborador.query.filter(
            Colaborador.nome_completo.ilike(f"%{nome_responsavel}%")
        ).first()
        if colaborador:
            dados_extraidos["colaboradores_envolvidos"] = [colaborador.id]

    return jsonify({"sucesso": True, "dados": dados_extraidos})
