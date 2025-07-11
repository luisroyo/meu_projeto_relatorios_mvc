# app/blueprints/ocorrencia/routes.py

import logging
import re
from datetime import datetime
import pytz
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Ocorrencia, OcorrenciaTipo, Colaborador, OrgaoPublico, Condominio, User
from app.forms import OcorrenciaForm
from utils.classificador import classificar_ocorrencia

logger = logging.getLogger(__name__)

ocorrencia_bp = Blueprint(
    'ocorrencia',
    __name__,
    template_folder='templates',
    url_prefix='/ocorrencias'
)

# --- Funções Auxiliares (Inalteradas) ---
def optional_int_coerce(value):
    try: return int(value)
    except (ValueError, TypeError): return None

def populate_ocorrencia_form_choices(form):
    form.condominio_id.choices = [('', '-- Selecione um Condomínio --')] + [(str(c.id), c.nome) for c in Condominio.query.order_by('nome').all()]
    form.ocorrencia_tipo_id.choices = [('', '-- Selecione um Tipo --')] + [(str(t.id), t.nome) for t in OcorrenciaTipo.query.order_by('nome').all()]
    form.orgaos_acionados.choices = [(str(o.id), o.nome) for o in OrgaoPublico.query.order_by('nome').all()]
    form.colaboradores_envolvidos.choices = [(str(col.id), col.nome_completo) for col in Colaborador.query.filter_by(status='Ativo').order_by('nome_completo').all()]
    form.supervisor_id.choices = [('', '-- Selecione um Supervisor --')] + [(str(s.id), s.username) for s in User.query.filter_by(is_supervisor=True, is_approved=True).order_by('username').all()]

def pode_editar_ocorrencia(f):
    @wraps(f)
    def decorated_function(ocorrencia_id, *args, **kwargs):
        ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
        if not (current_user.is_admin or current_user.id == ocorrencia.registrado_por_user_id):
            flash('Você não tem permissão para editar esta ocorrência.', 'danger')
            return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=ocorrencia.id))
        return f(ocorrencia_id, *args, **kwargs)
    return decorated_function

# --- Rotas (Inalteradas, exceto pela correção na função listar_ocorrencias) ---
@ocorrencia_bp.route('/historico')
@login_required
def listar_ocorrencias():
    page = request.args.get('page', 1, type=int)
    selected_status = request.args.get('status', '')
    selected_condominio_id = request.args.get('condominio_id', type=int)
    selected_supervisor_id = request.args.get('supervisor_id', type=int)
    selected_tipo_id = request.args.get('tipo_id', type=int)
    selected_data_inicio = request.args.get('data_inicio', '')
    selected_data_fim = request.args.get('data_fim', '')

    query = Ocorrencia.query.options(db.joinedload(Ocorrencia.tipo), db.joinedload(Ocorrencia.registrado_por), db.joinedload(Ocorrencia.condominio), db.joinedload(Ocorrencia.supervisor))

    if selected_status: query = query.filter(Ocorrencia.status == selected_status)
    if selected_condominio_id: query = query.filter(Ocorrencia.condominio_id == selected_condominio_id)
    if selected_supervisor_id: query = query.filter(Ocorrencia.supervisor_id == selected_supervisor_id)
    if selected_tipo_id: query = query.filter(Ocorrencia.ocorrencia_tipo_id == selected_tipo_id)
    if selected_data_inicio:
        try:
            data_inicio_obj = datetime.strptime(selected_data_inicio, '%Y-%m-%d').astimezone(pytz.utc)
            query = query.filter(Ocorrencia.data_hora_ocorrencia >= data_inicio_obj)
        except ValueError: flash('Formato de data de início inválido. Use AAAA-MM-DD.', 'danger')
    if selected_data_fim:
        try:
            data_fim_obj = datetime.strptime(selected_data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59).astimezone(pytz.utc)
            query = query.filter(Ocorrencia.data_hora_ocorrencia <= data_fim_obj)
        except ValueError: flash('Formato de data de fim inválido. Use AAAA-MM-DD.', 'danger')

    ocorrencias_pagination = query.order_by(Ocorrencia.data_hora_ocorrencia.desc()).paginate(page=page, per_page=15, error_out=False)

    condominios = Condominio.query.order_by(Condominio.nome).all()
    supervisors = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    tipos_ocorrencia = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    status_list = ['Registrada', 'Em Andamento', 'Concluída', 'Cancelada']

    filter_args = {k: v for k, v in request.args.items() if k != 'page'}

    return render_template('ocorrencia/list.html',
                           title='Histórico de Ocorrências',
                           ocorrencias_pagination=ocorrencias_pagination,
                           condominios=condominios,
                           supervisors=supervisors,
                           tipos_ocorrencia=tipos_ocorrencia,
                           status_list=status_list,
                           selected_status=selected_status,
                           selected_condominio_id=selected_condominio_id,
                           selected_supervisor_id=selected_supervisor_id,
                           selected_tipo_id=selected_tipo_id,
                           selected_data_inicio=selected_data_inicio,
                           selected_data_fim=selected_data_fim,
                           filter_args=filter_args)


@ocorrencia_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_ocorrencia():
    form = OcorrenciaForm()
    populate_ocorrencia_form_choices(form)

    if request.method == 'GET':
        if request.args.get('relatorio_final'): form.relatorio_final.data = request.args.get('relatorio_final')
        form.data_hora_ocorrencia.data = datetime.now()

    if form.validate_on_submit():
        try:
            tipo_ocorrencia_id = form.ocorrencia_tipo_id.data
            if form.novo_tipo_ocorrencia.data:
                tipo_existente = OcorrenciaTipo.query.filter(OcorrenciaTipo.nome.ilike(form.novo_tipo_ocorrencia.data.strip())).first()
                if tipo_existente: tipo_ocorrencia_id = tipo_existente.id
                else:
                    novo_tipo = OcorrenciaTipo(nome=form.novo_tipo_ocorrencia.data.strip())
                    db.session.add(novo_tipo)
                    db.session.flush()
                    tipo_ocorrencia_id = novo_tipo.id
            
            utc_datetime = None
            if form.data_hora_ocorrencia.data:
                naive_datetime = form.data_hora_ocorrencia.data
                local_tz = pytz.timezone('America/Sao_Paulo')
                aware_local_datetime = local_tz.localize(naive_datetime)
                utc_datetime = aware_local_datetime.astimezone(pytz.utc)

            nova_ocorrencia = Ocorrencia(
                condominio_id=form.condominio_id.data, data_hora_ocorrencia=utc_datetime,
                turno=form.turno.data, relatorio_final=form.relatorio_final.data,
                status=form.status.data, endereco_especifico=form.endereco_especifico.data,
                ocorrencia_tipo_id=tipo_ocorrencia_id, registrado_por_user_id=current_user.id,
                supervisor_id=form.supervisor_id.data
            )
            if form.orgaos_acionados.data:
                orgaos = OrgaoPublico.query.filter(OrgaoPublico.id.in_(form.orgaos_acionados.data)).all()
                nova_ocorrencia.orgaos_acionados.extend(orgaos)
            if form.colaboradores_envolvidos.data:
                colaboradores = Colaborador.query.filter(Colaborador.id.in_(form.colaboradores_envolvidos.data)).all()
                nova_ocorrencia.colaboradores_envolvidos.extend(colaboradores)
            
            db.session.add(nova_ocorrencia)
            db.session.commit()
            flash('Ocorrência registrada com sucesso!', 'success')
            return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=nova_ocorrencia.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar nova ocorrência: {e}", exc_info=True)
            flash(f'Erro ao salvar a ocorrência: {e}', 'danger')
            
    return render_template('ocorrencia/form_direto.html', title='Registrar Nova Ocorrência', form=form)


@ocorrencia_bp.route('/detalhes/<int:ocorrencia_id>')
@login_required
def detalhes_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    return render_template('ocorrencia/details.html', title=f'Detalhes da Ocorrência #{ocorrencia.id}', ocorrencia=ocorrencia)


@ocorrencia_bp.route('/editar/<int:ocorrencia_id>', methods=['GET', 'POST'])
@login_required
@pode_editar_ocorrencia
def editar_ocorrencia(ocorrencia_id):
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    form = OcorrenciaForm(obj=ocorrencia)
    populate_ocorrencia_form_choices(form)
    # Lógica de edição (pode ser expandida depois)
    if form.validate_on_submit():
        # ...
        db.session.commit()
        flash('Ocorrência atualizada com sucesso!', 'success')
        return redirect(url_for('ocorrencia.detalhes_ocorrencia', ocorrencia_id=ocorrencia.id))
    
    return render_template('ocorrencia/form_direto.html', title=f'Editar Ocorrência #{ocorrencia.id}', form=form)

@ocorrencia_bp.route('/deletar/<int:ocorrencia_id>', methods=['POST'])
@login_required
def deletar_ocorrencia(ocorrencia_id):
    # Lógica de exclusão (pode ser expandida depois)
    ocorrencia = db.get_or_404(Ocorrencia, ocorrencia_id)
    db.session.delete(ocorrencia)
    db.session.commit()
    flash('Ocorrência deletada com sucesso.', 'success')
    return redirect(url_for('ocorrencia.listar_ocorrencias'))

# --- ROTA DE ANÁLISE FINAL USANDO O NOVO MÓDULO CLASSIFICADOR ---
@ocorrencia_bp.route('/analisar-relatorio', methods=['POST'])
@login_required
def analisar_relatorio():
    data = request.get_json()
    texto = data.get('texto_relatorio', '')
    if not texto:
        return jsonify({'sucesso': False, 'message': 'Texto do relatório está vazio.'}), 400

    texto_limpo = texto.replace(u'\xa0', u' ').strip()
    
    print("\n" + "="*50)
    print("--- INICIANDO ANÁLISE COM MÓDULO CLASSIFICADOR EXTERNO ---")
    print("="*50)

    dados_extraidos = {}

    # 1. DATA, HORA E TURNO
    print("\n[1] Buscando Data, Hora e determinando o Turno...")
    match_data = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", texto_limpo)
    match_hora = re.search(r"Hora:\s*(\d{2}:\d{2})", texto_limpo)
    if match_data and match_hora:
        data_str = match_data.group(1).strip()
        hora_str = match_hora.group(1).strip()
        try:
            datetime_obj = datetime.strptime(f"{data_str} {hora_str}", '%d/%m/%Y %H:%M')
            dados_extraidos['data_hora_ocorrencia'] = datetime_obj.strftime('%Y-%m-%dT%H:%M')
            hora_int = datetime_obj.hour
            if 18 <= hora_int or hora_int < 6:
                dados_extraidos['turno'] = 'Noturno'
            else:
                dados_extraidos['turno'] = 'Diurno'
        except ValueError:
            pass # Ignora erros de formatação

    # 2. LOCAL, ENDEREÇO E CONDOMÍNIO
    print("\n[2] Buscando Local e Condomínio...")
    match_local = re.search(r"Local:\s*([^\n\r]+)", texto_limpo)
    if match_local:
        endereco_completo = match_local.group(1).strip()
        dados_extraidos['endereco_especifico'] = endereco_completo
        
        condominio_encontrado = None
        match_condo_keyword = re.search(r"(?:Residencial|Condomínio|Cond\.)\s+([^\n\r,]+)", endereco_completo, re.IGNORECASE)
        if match_condo_keyword:
            nome_condo_extraido = match_condo_keyword.group(1).strip()
            condominio_encontrado = Condominio.query.filter(Condominio.nome.ilike(f"%{nome_condo_extraido}%")).first()
        if not condominio_encontrado:
            for condo in Condominio.query.all():
                if condo.nome.lower() in endereco_completo.lower():
                    condominio_encontrado = condo
                    break
        if condominio_encontrado:
            dados_extraidos['condominio_id'] = condominio_encontrado.id

    # 3. TIPO DA OCORRÊNCIA (AGORA USANDO O NOVO MÓDULO)
    print("\n[3] Buscando Tipo da Ocorrência (com classificador.py)...")
    texto_ocorrencia = ""
    match_ocorrencia_texto = re.search(r"Ocorrência:\s*([^\n\r]+)", texto_limpo, re.IGNORECASE)
    if match_ocorrencia_texto:
        texto_ocorrencia = match_ocorrencia_texto.group(1)
    
    texto_completo_analise = texto_ocorrencia + " " + texto_limpo
    nome_tipo_encontrado = classificar_ocorrencia(texto_completo_analise)
    
    if nome_tipo_encontrado:
        print(f"-> Classificador retornou o tipo: '{nome_tipo_encontrado}'")
        tipo_obj = OcorrenciaTipo.query.filter(OcorrenciaTipo.nome.ilike(nome_tipo_encontrado)).first()
        if tipo_obj:
            dados_extraidos['ocorrencia_tipo_id'] = tipo_obj.id
            print(f"   [SUCESSO] Tipo encontrado no DB: ID={tipo_obj.id}")
        else:
            print(f"   [AVISO] O tipo '{nome_tipo_encontrado}' foi classificado, mas não encontrado no DB.")
    else:
        print("   [AVISO] Nenhuma palavra-chave correspondeu a um Tipo de Ocorrência.")

    # 4. RESPONSÁVEL (COLABORADOR)
    print("\n[4] Buscando Responsável pelo Registro...")
    match_responsavel = re.search(r"Responsável pelo registro:\s*([^\n\r(]+)", texto_limpo)
    if match_responsavel:
        nome_responsavel = match_responsavel.group(1).strip()
        colaborador = Colaborador.query.filter(Colaborador.nome_completo.ilike(f"%{nome_responsavel}%")).first()
        if colaborador:
            dados_extraidos['colaboradores_envolvidos'] = [colaborador.id]

    print("\n" + "="*50)
    print(f"DADOS FINAIS A SEREM ENVIADOS PARA O FORMULÁRIO: {dados_extraidos}")
    print("--- FIM DA ANÁLISE ---")
    print("="*50 + "\n")
    
    return jsonify({'sucesso': True, 'dados': dados_extraidos})