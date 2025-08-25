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

    from app.models.vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas
    query = VWOcorrenciasDetalhadas.query

    ## [REMOVIDO] Bloco inteiro de IFs para filtragem manual foi removido daqui.
    # if selected_status: query = query.filter(Ocorrencia.status == selected_status)
    # ... e todos os outros ifs ...

    ## [ADICIONADO] Chamada única para a função de serviço centralizada.
    query = ocorrencia_service.apply_ocorrencia_filters(query, filters)

    from app.models.vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas
    ocorrencias_pagination = query.order_by(
        VWOcorrenciasDetalhadas.data_hora_ocorrencia.desc()
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
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados JSON não fornecidos"}), 400
        
        # Aceita tanto 'relatorio_bruto' quanto 'texto_relatorio' para compatibilidade
        texto = data.get("relatorio_bruto") or data.get("texto_relatorio", "")
        formatar_para_email = data.get("formatar_para_email", False)
        
        if not texto:
            return jsonify({"erro": "Texto do relatório está vazio"}), 400

        texto_limpo = texto.replace("\xa0", " ").strip()
        
        # Processamento e correção do texto
        relatorio_processado = processar_e_corrigir_texto(texto_limpo)
        
        # Extrair dados estruturados do relatório
        dados_extraidos = extrair_dados_relatorio(relatorio_processado)
        
        # Preparar resposta
        resposta = {
            "relatorio_processado": relatorio_processado,
            "sucesso": True,
            "dados": dados_extraidos  # ✅ Adiciona os dados estruturados
        }
        
        # Se solicitado, gerar versão para email
        if formatar_para_email:
            relatorio_email = formatar_para_email_profissional(relatorio_processado)
            resposta["relatorio_email"] = relatorio_email
        
        return jsonify(resposta), 200
        
    except Exception as e:
        print(f"Erro ao analisar relatório: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

def processar_e_corrigir_texto(texto):
    """Processa e corrige o texto do relatório"""
    # Correções básicas
    correcoes = {
        "hoirario": "horário",
        "conatto": "contato",
        "marador": "morador",
        "fernado": "Fernando",
        "ocorrencia": "ocorrência",
        "marad": "morador"
    }
    
    texto_corrigido = texto
    for erro, correcao in correcoes.items():
        texto_corrigido = texto_corrigido.replace(erro, correcao)
    
    # Melhorias de formatação
    texto_corrigido = texto_corrigido.strip()
    texto_corrigido = re.sub(r'\s+', ' ', texto_corrigido)  # Remove espaços extras
    texto_corrigido = re.sub(r'([.!?])\s*([A-Za-z])', r'\1 \2', texto_corrigido)  # Espaços após pontuação
    
    # Capitalização de início de frases
    linhas = texto_corrigido.split('\n')
    linhas_corrigidas = []
    for linha in linhas:
        if linha.strip():
            linha = linha.strip()
            if linha and not linha[0].isupper():
                linha = linha[0].upper() + linha[1:]
            linhas_corrigidas.append(linha)
        else:
            linhas_corrigidas.append('')
    
    return '\n'.join(linhas_corrigidas)

def formatar_para_email_profissional(texto):
    """Formata o texto para envio profissional por email"""
    # Adiciona cabeçalho profissional
    cabecalho = "RELATÓRIO DE OCORRÊNCIA\n"
    cabecalho += "=" * 30 + "\n\n"
    
    # Formata o corpo
    corpo = texto.replace('\n', '\n    ')
    
    # Adiciona rodapé
    rodape = "\n\n" + "=" * 30 + "\n"
    rodape += "Este relatório foi gerado automaticamente pelo sistema de gestão de segurança.\n"
    rodape += "Data de geração: " + datetime.now().strftime("%d/%m/%Y %H:%M")
    
    return cabecalho + corpo + rodape

def extrair_dados_relatorio(texto):
    """Extrai dados estruturados do relatório de ocorrência"""
    dados = {}
    
    try:
        # Extrair data
        import re
        data_match = re.search(r'Data:\s*(\d{2}/\d{2}/\d{4})', texto)
        if data_match:
            data_str = data_match.group(1)
            # Converter formato DD/MM/YYYY para YYYY-MM-DD
            dia, mes, ano = data_str.split('/')
            dados['data_hora_ocorrencia'] = f"{ano}-{mes}-{dia}"
            print(f"Data extraída: {data_str} -> {dados['data_hora_ocorrencia']}")
        
        # Extrair hora
        hora_match = re.search(r'Hora:\s*(\d{2}:\d{2})', texto)
        if hora_match:
            dados['hora_ocorrencia'] = hora_match.group(1)
            print(f"Hora extraída: {dados['hora_ocorrencia']}")
        
        # Extrair local/endereço
        local_match = re.search(r'Local:\s*([^\n]+)', texto)
        if local_match:
            dados['endereco_especifico'] = local_match.group(1).strip()
            print(f"Local extraído: {dados['endereco_especifico']}")
        
        # Extrair endereço específico
        endereco_match = re.search(r'Endereço:\s*([^\n]+)', texto)
        if endereco_match:
            dados['endereco_especifico'] = endereco_match.group(1).strip()
            print(f"Endereço extraído: {dados['endereco_especifico']}")
        
        # Extrair turno (baseado na hora)
        if 'hora_ocorrencia' in dados:
            hora = int(dados['hora_ocorrencia'].split(':')[0])
            if 6 <= hora < 18:
                dados['turno'] = 'Diurno'
            else:
                dados['turno'] = 'Noturno'
            print(f"Turno determinado: {dados['turno']} (hora: {hora})")
        
        # Tentar identificar condomínio pelo texto
        condominios = Condominio.query.all()
        for condominio in condominios:
            if condominio.nome.lower() in texto.lower():
                dados['condominio_id'] = condominio.id
                print(f"Condomínio identificado: {condominio.nome} (ID: {condominio.id})")
                break
        
        # Tentar identificar tipo de ocorrência pelo texto
        tipos_ocorrencia = OcorrenciaTipo.query.all()
        for tipo in tipos_ocorrencia:
            if tipo.nome.lower() in texto.lower():
                dados['ocorrencia_tipo_id'] = tipo.id
                print(f"Tipo de ocorrência identificado: {tipo.nome} (ID: {tipo.id})")
                break
        
        # Se não encontrou tipo específico, usar padrão
        if 'ocorrencia_tipo_id' not in dados:
            tipo_padrao = OcorrenciaTipo.query.filter_by(nome="verificação").first()
            if tipo_padrao:
                dados['ocorrencia_tipo_id'] = tipo_padrao.id
                print(f"Usando tipo padrão: verificação (ID: {tipo_padrao.id})")
        
        # Extrair colaboradores mencionados
        colaboradores_envolvidos = []
        colaboradores = Colaborador.query.all()
        for colaborador in colaboradores:
            if colaborador.nome_completo.lower() in texto.lower():
                colaboradores_envolvidos.append(colaborador.id)
                print(f"Colaborador identificado: {colaborador.nome_completo} (ID: {colaborador.id})")
        
        if colaboradores_envolvidos:
            dados['colaboradores_envolvidos'] = colaboradores_envolvidos
        
        print(f"Dados extraídos finais: {dados}")
            
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        dados = {}
    
    return dados
