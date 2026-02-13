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
        print(f"Texto recebido para análise: {texto_limpo[:200]}...")
        
        # Processamento e correção do texto
        relatorio_processado = processar_e_corrigir_texto(texto_limpo)
        print(f"Texto processado: {relatorio_processado[:200]}...")
        
        # Extrair dados estruturados do relatório
        dados_extraidos = extrair_dados_relatorio(relatorio_processado)
        print(f"Dados extraídos: {dados_extraidos}")
        
        # Preparar resposta
        resposta = {
            "relatorio_processado": relatorio_processado,
            "sucesso": True,
            "dados": dados_extraidos  # ✅ Adiciona os dados estruturados
        }
        
        # Verificação de segurança para garantir que os dados sejam válidos
        if not isinstance(dados_extraidos, dict):
            print(f"AVISO: dados_extraidos não é um dicionário: {type(dados_extraidos)}")
            dados_extraidos = {}
            resposta["dados"] = dados_extraidos
        
        print(f"Resposta final: {resposta}")
        print(f"Tipo da resposta: {type(resposta)}")
        print(f"Tipo dos dados: {type(dados_extraidos)}")
        print(f"Chaves da resposta: {list(resposta.keys())}")
        print(f"Chaves dos dados: {list(dados_extraidos.keys()) if isinstance(dados_extraidos, dict) else 'N/A'}")
        
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
        print(f"Iniciando extração de dados do texto: {texto[:200]}...")
        
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
        
        # ============================================================================
        # EXTRAÇÃO DE ENDEREÇO - ABORDAGEM SIMPLIFICADA
        # ============================================================================
        endereco_encontrado = False
        print("Iniciando busca por endereço...")
        
        # Buscar por "Local:" e extrair até a próxima linha ou palavra-chave
        local_match = re.search(r'Local:\s*([^\n\r]+)', texto, re.IGNORECASE)
        if local_match:
            endereco = local_match.group(1).strip()
            print(f"Endereço bruto encontrado: '{endereco}'")
            
            # Limpar o endereço - parar na primeira palavra-chave
            palavras_fim = ['ocorrência', 'ocorrencia', 'relato', 'ações', 'acionamentos']
            for palavra in palavras_fim:
                if palavra in endereco.lower():
                    pos = endereco.lower().find(palavra)
                    if pos > 0:
                        endereco = endereco[:pos].strip()
                        break
            
            # Se ainda estiver muito longo, parar na primeira vírgula ou hífen
            if len(endereco) > 50:
                for separador in [',', '-', ';']:
                    if separador in endereco:
                        pos = endereco.find(separador)
                        endereco = endereco[:pos].strip()
                        break
            
            dados['endereco_especifico'] = endereco
            print(f"Endereço limpo extraído: {endereco}")
            endereco_encontrado = True
        
        # ============================================================================
        # EXTRAÇÃO DE TIPO DE OCORRÊNCIA - LÓGICA INTELIGENTE
        # ============================================================================
        print("Iniciando busca por tipo de ocorrência...")
        
        tipos_ocorrencia = OcorrenciaTipo.query.all()
        tipo_encontrado = False
        
        # Palavras-chave para cada tipo de ocorrência
        palavras_chave_tipos = {
            'Auxílio ao Residencial': ['porta', 'residência', 'residencial', 'morador', 'auxílio', 'ajuda'],
            'Verificação': ['verificação', 'verificar', 'checagem', 'inspeção', 'observação'],
            'Perturbação de sossego': ['barulho', 'som', 'música', 'festa', 'perturbação', 'sossego'],
            'Tentativa de furto': ['tentativa', 'furto', 'roubo', 'invasão', 'suspeito'],
            'Furtos': ['furto', 'roubo', 'furtado', 'desapareceu'],
            'Vandalismo': ['vandalismo', 'destruição', 'danificado', 'quebrado', 'pichação']
        }
        
        # Primeiro: tentar encontrar por nome exato
        for tipo in tipos_ocorrencia:
            if tipo.nome.lower() in texto.lower():
                dados['ocorrencia_tipo_id'] = tipo.id
                print(f"Tipo de ocorrência identificado (nome exato): {tipo.nome} (ID: {tipo.id})")
                tipo_encontrado = True
                break
        
        # Segundo: se não encontrou, usar palavras-chave
        if not tipo_encontrado:
            print("Buscando por palavras-chave...")
            melhor_match = None
            melhor_score = 0
            
            for tipo in tipos_ocorrencia:
                if tipo.nome in palavras_chave_tipos:
                    palavras_chave = palavras_chave_tipos[tipo.nome]
                    score = 0
                    
                    for palavra in palavras_chave:
                        if palavra.lower() in texto.lower():
                            score += 1
                    
                    if score > melhor_score:
                        melhor_score = score
                        melhor_match = tipo
            
            if melhor_match and melhor_score > 0:
                dados['ocorrencia_tipo_id'] = melhor_match.id
                print(f"Tipo identificado por palavras-chave: {melhor_match.nome} (ID: {melhor_match.id}, score: {melhor_score})")
                tipo_encontrado = True
        
        # Terceiro: se ainda não encontrou, usar tipo padrão inteligente
        if not tipo_encontrado:
            print("Usando tipo padrão inteligente...")
            
            # Verificar se é algo relacionado a residencial/morador
            if any(palavra in texto.lower() for palavra in ['residencial', 'morador', 'porta', 'residência']):
                tipo_padrao = OcorrenciaTipo.query.filter_by(nome="Auxílio ao Residencial").first()
                if tipo_padrao:
                    dados['ocorrencia_tipo_id'] = tipo_padrao.id
                    print(f"Tipo padrão inteligente (residencial): {tipo_padrao.nome} (ID: {tipo_padrao.id})")
                else:
                    # Fallback para o primeiro tipo disponível
                    primeiro_tipo = OcorrenciaTipo.query.first()
                    if primeiro_tipo:
                        dados['ocorrencia_tipo_id'] = primeiro_tipo.id
                        print(f"Fallback para primeiro tipo: {primeiro_tipo.nome} (ID: {primeiro_tipo.id})")
            else:
                # Fallback para "Verificação" se existir
                tipo_verificacao = OcorrenciaTipo.query.filter_by(nome="Verificação").first()
                if tipo_verificacao:
                    dados['ocorrencia_tipo_id'] = tipo_verificacao.id
                    print(f"Tipo padrão (verificação): {tipo_verificacao.nome} (ID: {tipo_verificacao.id})")
                else:
                    # Último fallback
                    primeiro_tipo = OcorrenciaTipo.query.first()
                    if primeiro_tipo:
                        dados['ocorrencia_tipo_id'] = primeiro_tipo.id
                        print(f"Fallback final: {primeiro_tipo.nome} (ID: {primeiro_tipo.id})")
        
        # ============================================================================
        # EXTRAÇÃO DE COLABORADORES - LÓGICA CORRIGIDA E MELHORADA
        # ============================================================================
        print("Iniciando busca por colaboradores...")
        
        colaboradores_envolvidos = []
        colaboradores = Colaborador.query.all()
        
        # Palavras-chave que indicam que a pessoa é um colaborador do sistema
        indicadores_colaborador = [
            'águia', 'agente', 'segurança', 'vigilante', 'ronda', 'patrulha',
            'supervisor', 'coordenador', 'responsável pelo registro'
        ]
        
        # Palavras-chave que indicam que a pessoa NÃO é um colaborador
        indicadores_nao_colaborador = [
            'morador', 'residente', 'sócio', 'responsável pela mudança', 'testemunha',
            'envolvido', 'cpf', 'endereço', 'escritório', 'estabelecimento'
        ]
        
        for colaborador in colaboradores:
            nome_completo = colaborador.nome_completo.lower()
            primeiro_nome = colaborador.nome_completo.split()[0].lower()
            
            # Verificar se o nome aparece no texto
            if nome_completo in texto.lower() or primeiro_nome in texto.lower():
                print(f"Verificando colaborador: {colaborador.nome_completo}")
                
                # Buscar o contexto onde o nome aparece
                nome_para_buscar = nome_completo if len(nome_completo) > 3 else primeiro_nome
                pos_inicio = texto.lower().find(nome_para_buscar)
                
                print(f"  Nome para buscar: '{nome_para_buscar}'")
                print(f"  Posição encontrada: {pos_inicio}")
                
                if pos_inicio != -1:
                    # Pegar contexto antes e depois do nome (100 caracteres para mais contexto)
                    contexto_inicio = max(0, pos_inicio - 100)
                    contexto_fim = min(len(texto), pos_inicio + len(nome_para_buscar) + 100)
                    contexto = texto[contexto_inicio:contexto_fim]
                    
                    print(f"  Contexto encontrado: '{contexto}'")
                    
                    # Verificar se é realmente um colaborador
                    is_colaborador = False
                    indicador_encontrado = None
                    
                    # Se contém indicadores de colaborador, é válido
                    for indicador in indicadores_colaborador:
                        if indicador in contexto.lower():
                            is_colaborador = True
                            indicador_encontrado = indicador
                            print(f"  ✅ Indicador de colaborador encontrado: '{indicador}'")
                            break
                    
                    # Se contém indicadores de NÃO colaborador, verificar se não é um falso positivo
                    for indicador in indicadores_nao_colaborador:
                        if indicador in contexto.lower():
                            # Verificar se é um falso positivo (ex: "responsável pelo registro" vs "responsável pela mudança")
                            if indicador == 'responsável pelo registro':
                                # Este é um indicador POSITIVO, não negativo
                                continue
                            elif indicador == 'envolvido' and 'envolvido na ocorrência' in contexto.lower():
                                # "Envolvido na ocorrência" pode ser positivo para colaboradores
                                continue
                            else:
                                is_colaborador = False
                                print(f"  ❌ Indicador de NÃO colaborador encontrado: '{indicador}'")
                                break
                    
                    # Lógica adicional: se o nome aparece próximo a "responsável pelo registro", é colaborador
                    if 'responsável pelo registro' in contexto.lower() and nome_para_buscar in contexto.lower():
                        is_colaborador = True
                        indicador_encontrado = 'responsável pelo registro'
                        print(f"  ✅ Confirmado como responsável pelo registro")
                    
                    if is_colaborador:
                        colaboradores_envolvidos.append(colaborador.id)
                        print(f"  ✅ Colaborador confirmado: {colaborador.nome_completo} (ID: {colaborador.id}) - Indicador: '{indicador_encontrado}'")
                    else:
                        print(f"  ❌ Não é colaborador: {colaborador.nome_completo}")
                else:
                    print(f"  ❌ Nome não encontrado no texto: {colaborador.nome_completo}")
        
        if colaboradores_envolvidos:
            dados['colaboradores_envolvidos'] = colaboradores_envolvidos
            print(f"Total de colaboradores identificados: {len(colaboradores_envolvidos)}")
        else:
            print("Nenhum colaborador foi identificado")
        
        # ============================================================================
        # EXTRAÇÃO DE TURNO
        # ============================================================================
        if 'hora_ocorrencia' in dados:
            hora = int(dados['hora_ocorrencia'].split(':')[0])
            if 6 <= hora < 18:
                dados['turno'] = 'Diurno'
            else:
                dados['turno'] = 'Noturno'
            print(f"Turno determinado: {dados['turno']} (hora: {hora})")
        
        # ============================================================================
        # IDENTIFICAÇÃO DE CONDOMÍNIO
        # ============================================================================
        condominios = Condominio.query.all()
        for condominio in condominios:
            if condominio.nome.lower() in texto.lower():
                dados['condominio_id'] = condominio.id
                print(f"Condomínio identificado: {condominio.nome} (ID: {condominio.id})")
                break
        
        print(f"Dados extraídos finais: {dados}")
            
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        dados = {}
    
    return dados
