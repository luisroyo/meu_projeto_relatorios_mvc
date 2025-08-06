"""
APIs de ocorrências para fornecer dados para o frontend.
"""
import logging
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

from app import db
from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User, Colaborador, OrgaoPublico
from app.services import ocorrencia_service
from flask import Blueprint

ocorrencia_api_bp = Blueprint('ocorrencia_api', __name__, url_prefix='/api/ocorrencias')

logger = logging.getLogger(__name__)


def get_user_name(user_id):
    """Obtém o nome do usuário pelo ID."""
    if not user_id:
        return 'N/A'
    try:
        user = User.query.get(user_id)
        return user.username if user else 'N/A'
    except Exception:
        return 'N/A'


@ocorrencia_api_bp.route('', methods=['GET'])
@ocorrencia_api_bp.route('/', methods=['GET'])
@ocorrencia_api_bp.route('/historico', methods=['GET'])
@jwt_required()
def listar_ocorrencias():
    """Listar ocorrências com filtros e paginação."""
    try:
        # Log para debug
        logger.info(f"API de ocorrências chamada - User ID: {get_jwt_identity()}")
        logger.info(f"Filtros recebidos: {request.args}")
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtros
        filters = {
            'status': request.args.get('status', ''),
            'condominio_id': request.args.get('condominio_id', type=int),
            'supervisor_id': request.args.get('supervisor_id', type=int),
            'tipo_id': request.args.get('tipo_id', type=int),
            'data_inicio': request.args.get('data_inicio', ''),
            'data_fim': request.args.get('data_fim', ''),
            'texto_relatorio': request.args.get('texto_relatorio', '')
        }
        
        # Query base
        query = Ocorrencia.query.options(
            db.joinedload(Ocorrencia.tipo),
            db.joinedload(Ocorrencia.condominio),
            db.joinedload(Ocorrencia.supervisor)
        )
        
        # Aplicar filtros usando o service centralizado
        query = ocorrencia_service.apply_ocorrencia_filters(query, filters)
        
        # Ordenação
        query = query.order_by(desc(Ocorrencia.data_hora_ocorrencia))
        
        # Paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serializar ocorrências
        ocorrencias = []
        for o in pagination.items:
            try:
                ocorrencias.append({
                    'id': o.id,
                    'tipo': o.tipo.nome if o.tipo else 'N/A',
                    'condominio': o.condominio.nome if o.condominio else 'N/A',
                    'data_hora_ocorrencia': o.data_hora_ocorrencia.isoformat() if o.data_hora_ocorrencia else None,
                    'descricao': o.relatorio_final,
                    'status': o.status,
                    'endereco': o.endereco_especifico,
                    'turno': o.turno,
                    'data_criacao': o.data_criacao.isoformat() if o.data_criacao else None,
                    'registrado_por': get_user_name(o.registrado_por_user_id),
                    'supervisor': get_user_name(o.supervisor_id),
                    'registrado_por_user_id': o.registrado_por_user_id,
                    'supervisor_id': o.supervisor_id,
                    'colaboradores_envolvidos': [{'id': col.id, 'nome': col.nome_completo} for col in o.colaboradores_envolvidos],
                    'orgaos_acionados': [{'id': org.id, 'nome': org.nome} for org in o.orgaos_acionados]
                })
            except Exception as e:
                logger.error(f"Erro ao serializar ocorrência {o.id}: {e}")
                continue
        
        # Log do resultado
        logger.info(f"Retornando {len(ocorrencias)} ocorrências de {pagination.total} total")
        
        return jsonify({
            'ocorrencias': ocorrencias,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar ocorrências: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos_ocorrencia():
    """Listar tipos de ocorrência."""
    try:
        tipos = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
        
        return jsonify({
            'tipos': [{
                'id': tipo.id,
                'nome': tipo.nome,
                'descricao': tipo.descricao
            } for tipo in tipos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar tipos de ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios_ocorrencia():
    """Listar condomínios para ocorrências."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        return jsonify({
            'condominios': [{
                'id': condominio.id,
                'nome': condominio.nome
            } for condominio in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/colaboradores', methods=['GET'])
@jwt_required()
def listar_colaboradores_ocorrencia():
    """Listar colaboradores para ocorrências."""
    try:
        colaboradores = Colaborador.query.filter_by(status='Ativo').order_by(Colaborador.nome_completo).all()
        
        return jsonify({
            'colaboradores': [{
                'id': col.id,
                'nome': col.nome_completo,
                'cargo': col.cargo,
                'matricula': col.matricula
            } for col in colaboradores]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar colaboradores: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/orgaos-publicos', methods=['GET'])
@jwt_required()
def listar_orgaos_publicos_ocorrencia():
    """Listar órgãos públicos para ocorrências."""
    try:
        orgaos = OrgaoPublico.query.order_by(OrgaoPublico.nome).all()
        
        return jsonify({
            'orgaos_publicos': [{
                'id': org.id,
                'nome': org.nome,
                'contato': org.contato
            } for org in orgaos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar órgãos públicos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/supervisores', methods=['GET'])
@jwt_required()
def listar_supervisores_ocorrencia():
    """Listar supervisores para ocorrências."""
    try:
        supervisores = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        
        return jsonify({
            'supervisores': [{
                'id': sup.id,
                'nome': sup.username,
                'email': sup.email
            } for sup in supervisores]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar supervisores: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/status', methods=['GET'])
@jwt_required()
def listar_status_ocorrencia():
    """Listar status disponíveis para ocorrências."""
    try:
        status_list = [
            "Registrada",
            "Em Andamento", 
            "Concluída",
            "Pendente",
            "Rejeitada"
        ]
        
        return jsonify({
            'status': status_list
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar status: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['GET'])
@jwt_required()
def obter_ocorrencia(ocorrencia_id):
    """Obter detalhes de uma ocorrência específica."""
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        
        return jsonify({
            'id': ocorrencia.id,
            'tipo': ocorrencia.tipo.nome if ocorrencia.tipo else 'N/A',
            'condominio': ocorrencia.condominio.nome if ocorrencia.condominio else 'N/A',
            'data_hora_ocorrencia': ocorrencia.data_hora_ocorrencia.isoformat() if ocorrencia.data_hora_ocorrencia else None,
            'descricao': ocorrencia.relatorio_final,
            'status': ocorrencia.status,
            'endereco': ocorrencia.endereco_especifico,
            'turno': ocorrencia.turno,
            'data_criacao': ocorrencia.data_criacao.isoformat() if ocorrencia.data_criacao else None,
            'registrado_por': get_user_name(ocorrencia.registrado_por_user_id),
            'supervisor': get_user_name(ocorrencia.supervisor_id),
            'registrado_por_user_id': ocorrencia.registrado_por_user_id,
            'supervisor_id': ocorrencia.supervisor_id,
            'ocorrencia_tipo_id': ocorrencia.ocorrencia_tipo_id,
            'condominio_id': ocorrencia.condominio_id,
            'colaboradores_envolvidos': [{'id': col.id, 'nome': col.nome_completo} for col in ocorrencia.colaboradores_envolvidos],
            'orgaos_acionados': [{'id': org.id, 'nome': org.nome} for org in ocorrencia.orgaos_acionados]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('', methods=['POST'])
@ocorrencia_api_bp.route('/', methods=['POST'])
@jwt_required()
def criar_ocorrencia():
    """Criar uma nova ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['relatorio_final', 'ocorrencia_tipo_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Verificar se precisa criar novo tipo de ocorrência
        tipo_ocorrencia_id = data['ocorrencia_tipo_id']
        if data.get('novo_tipo_ocorrencia'):
            tipo_existente = OcorrenciaTipo.query.filter(
                OcorrenciaTipo.nome.ilike(data['novo_tipo_ocorrencia'].strip())
            ).first()
            if tipo_existente:
                tipo_ocorrencia_id = tipo_existente.id
            else:
                novo_tipo = OcorrenciaTipo(nome=data['novo_tipo_ocorrencia'].strip())
                db.session.add(novo_tipo)
                db.session.flush()
                tipo_ocorrencia_id = novo_tipo.id
        
        # Processar data/hora se fornecida
        data_hora_ocorrencia = None
        if data.get('data_hora_ocorrencia'):
            try:
                # Aceita tanto ISO format quanto DD/MM/YYYY HH:MM
                if 'T' in data['data_hora_ocorrencia']:
                    data_hora_ocorrencia = datetime.fromisoformat(data['data_hora_ocorrencia'].replace('Z', '+00:00'))
                else:
                    data_hora_ocorrencia = datetime.strptime(data['data_hora_ocorrencia'], '%d/%m/%Y %H:%M')
                    # Converter para UTC
                    from app.blueprints.ocorrencia.routes import local_to_utc
                    data_hora_ocorrencia = local_to_utc(data_hora_ocorrencia)
            except ValueError:
                pass
        
        # Criar nova ocorrência
        nova_ocorrencia = Ocorrencia()
        nova_ocorrencia.relatorio_final = data['relatorio_final']
        nova_ocorrencia.ocorrencia_tipo_id = tipo_ocorrencia_id
        nova_ocorrencia.condominio_id = data.get('condominio_id')
        nova_ocorrencia.supervisor_id = data.get('supervisor_id')
        nova_ocorrencia.turno = data.get('turno')
        nova_ocorrencia.status = data.get('status', 'Registrada')
        nova_ocorrencia.endereco_especifico = data.get('endereco_especifico')
        nova_ocorrencia.registrado_por_user_id = current_user_id
        if data_hora_ocorrencia:
            nova_ocorrencia.data_hora_ocorrencia = data_hora_ocorrencia
        
        # Adicionar colaboradores envolvidos
        if data.get('colaboradores_envolvidos'):
            colaboradores = Colaborador.query.filter(
                Colaborador.id.in_(data['colaboradores_envolvidos'])
            ).all()
            nova_ocorrencia.colaboradores_envolvidos.extend(colaboradores)
        
        # Adicionar órgãos acionados
        if data.get('orgaos_acionados'):
            orgaos = OrgaoPublico.query.filter(
                OrgaoPublico.id.in_(data['orgaos_acionados'])
            ).all()
            nova_ocorrencia.orgaos_acionados.extend(orgaos)
        
        db.session.add(nova_ocorrencia)
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência criada com sucesso',
            'id': nova_ocorrencia.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['PUT'])
@jwt_required()
def editar_ocorrencia(ocorrencia_id):
    """Editar uma ocorrência existente."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Verificar permissão para editar
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    if not (user.is_admin or user.id == ocorrencia.registrado_por_user_id):
        return jsonify({'error': 'Você não tem permissão para editar esta ocorrência'}), 403
    
    try:
        data = request.get_json()
        
        # Atualizar campos
        if 'relatorio_final' in data:
            ocorrencia.relatorio_final = data['relatorio_final']
        if 'ocorrencia_tipo_id' in data:
            ocorrencia.ocorrencia_tipo_id = data['ocorrencia_tipo_id']
        if 'condominio_id' in data:
            ocorrencia.condominio_id = data['condominio_id']
        if 'supervisor_id' in data:
            ocorrencia.supervisor_id = data['supervisor_id']
        if 'turno' in data:
            ocorrencia.turno = data['turno']
        if 'status' in data:
            ocorrencia.status = data['status']
        if 'endereco_especifico' in data:
            ocorrencia.endereco_especifico = data['endereco_especifico']
        
        # Processar data/hora se fornecida
        if 'data_hora_ocorrencia' in data and data['data_hora_ocorrencia']:
            try:
                # Aceita tanto ISO format quanto DD/MM/YYYY HH:MM
                if 'T' in data['data_hora_ocorrencia']:
                    data_hora_ocorrencia = datetime.fromisoformat(data['data_hora_ocorrencia'].replace('Z', '+00:00'))
                else:
                    data_hora_ocorrencia = datetime.strptime(data['data_hora_ocorrencia'], '%d/%m/%Y %H:%M')
                    # Converter para UTC
                    from app.blueprints.ocorrencia.routes import local_to_utc
                    data_hora_ocorrencia = local_to_utc(data_hora_ocorrencia)
                ocorrencia.data_hora_ocorrencia = data_hora_ocorrencia
            except ValueError:
                pass
        
        # Atualizar colaboradores envolvidos
        if 'colaboradores_envolvidos' in data:
            colaboradores = Colaborador.query.filter(
                Colaborador.id.in_(data['colaboradores_envolvidos'] or [])
            ).all()
            ocorrencia.colaboradores_envolvidos = colaboradores
        
        # Atualizar órgãos acionados
        if 'orgaos_acionados' in data:
            orgaos = OrgaoPublico.query.filter(
                OrgaoPublico.id.in_(data['orgaos_acionados'] or [])
            ).all()
            ocorrencia.orgaos_acionados = orgaos
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência atualizada com sucesso',
            'id': ocorrencia.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao editar ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['DELETE'])
@jwt_required()
def deletar_ocorrencia(ocorrencia_id):
    """Deletar uma ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Verificar permissão para deletar
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    if not (user.is_admin or user.id == ocorrencia.registrado_por_user_id):
        return jsonify({'error': 'Você não tem permissão para deletar esta ocorrência'}), 403
    
    try:
        db.session.delete(ocorrencia)
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência deletada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 

@ocorrencia_api_bp.route('/<int:ocorrencia_id>/approve', methods=['POST'])
@jwt_required()
def approve_ocorrencia(ocorrencia_id):
    """Aprovar uma ocorrência pendente."""
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    
    if ocorrencia.status != 'Pendente':
        return jsonify({'message': 'Apenas ocorrências pendentes podem ser aprovadas'}), 400
    
    ocorrencia.status = 'Registrada'
    db.session.commit()
    
    logger.info(f"Ocorrência {ocorrencia_id} aprovada")
    return jsonify({'message': 'Ocorrência aprovada com sucesso'}), 200

@ocorrencia_api_bp.route('/<int:ocorrencia_id>/reject', methods=['POST'])
@jwt_required()
def reject_ocorrencia(ocorrencia_id):
    """Rejeitar uma ocorrência pendente."""
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    
    if ocorrencia.status != 'Pendente':
        return jsonify({'message': 'Apenas ocorrências pendentes podem ser rejeitadas'}), 400
    
    ocorrencia.status = 'Rejeitada'
    db.session.commit()
    
    logger.info(f"Ocorrência {ocorrencia_id} rejeitada")
    return jsonify({'message': 'Ocorrência rejeitada com sucesso'}), 200

@ocorrencia_api_bp.route('/analyze-report', methods=['POST'])
@ocorrencia_api_bp.route('/analisar-relatorio', methods=['POST'])
@jwt_required()
def analyze_report():
    """Analisar relatório usando IA e extrair dados."""
    data = request.get_json()
    
    if not data or not data.get('relatorio_bruto'):
        return jsonify({'error': 'Relatório bruto é obrigatório'}), 400
    
    try:
        import re
        from app.utils.classificador import classificar_ocorrencia
        from app.services.patrimonial_report_service import PatrimonialReportService
        
        texto = data['relatorio_bruto']
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
                dados_extraidos["turno"] = "Noturno" if 18 <= datetime_obj.hour or datetime_obj.hour < 6 else "Diurno"
            except ValueError:
                pass
        
        # 2. LOCAL, ENDEREÇO E CONDOMÍNIO
        match_local = re.search(r"(?:Endereço|Local):\s*([^\n\r]+)", texto_limpo)
        if match_local:
            endereco_completo = match_local.group(1).strip()
            dados_extraidos["endereco_especifico"] = endereco_completo
            # Lógica para encontrar condomínio
            condominio_encontrado = next(
                (c for c in Condominio.query.all() if c.nome.lower() in endereco_completo.lower() or endereco_completo.lower() in c.nome.lower()),
                None
            )
            if condominio_encontrado:
                dados_extraidos["condominio_id"] = condominio_encontrado.id
        
        # 3. TIPO DA OCORRÊNCIA
        nome_tipo_encontrado = classificar_ocorrencia(texto_limpo)
        if nome_tipo_encontrado:
            tipo_obj = OcorrenciaTipo.query.filter(OcorrenciaTipo.nome.ilike(nome_tipo_encontrado)).first()
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
        match_responsavel = re.search(r"Responsável pelo registro:\s*([^\n\r(]+)", texto_limpo)
        if match_responsavel:
            nome_responsavel = match_responsavel.group(1).strip()
            colaborador = Colaborador.query.filter(
                Colaborador.nome_completo.ilike(f"%{nome_responsavel}%")
            ).first()
            if colaborador:
                dados_extraidos["colaboradores_envolvidos"] = [colaborador.id]
        
        # 5. Classificação e relatório patrimonial
        classificacao = classificar_ocorrencia(texto_limpo)
        patrimonial_service = PatrimonialReportService()
        relatorio_processado = patrimonial_service.gerar_relatorio_seguranca(texto_limpo)
        
        return jsonify({
            'sucesso': True,
            'dados': dados_extraidos,
            'classificacao': classificacao,
            'relatorio_processado': relatorio_processado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao analisar relatório: {e}")
        return jsonify({'error': 'Erro ao analisar relatório'}), 500 