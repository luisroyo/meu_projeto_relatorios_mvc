"""
APIs de ocorrências para fornecer dados para o frontend.
"""
import logging
import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

from app import db
from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User, Colaborador, OrgaoPublico
from app.services import ocorrencia_service
from app.blueprints.api.utils import success_response, error_response, pagination_response

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
        
        return success_response(
            data={'ocorrencias': ocorrencias},
            message=f'Lista de ocorrências obtida com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar ocorrências: {e}")
        return error_response('Erro interno ao listar ocorrências', status_code=500)


@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['GET'])
@jwt_required()
def obter_ocorrencia(ocorrencia_id):
    """Obter detalhes de uma ocorrência específica."""
    try:
        ocorrencia = Ocorrencia.query.options(
            db.joinedload(Ocorrencia.tipo),
            db.joinedload(Ocorrencia.condominio),
            db.joinedload(Ocorrencia.supervisor),
            db.joinedload(Ocorrencia.colaboradores_envolvidos),
            db.joinedload(Ocorrencia.orgaos_acionados)
        ).get(ocorrencia_id)
        
        if not ocorrencia:
            return error_response('Ocorrência não encontrada', status_code=404)
        
        # Serializar ocorrência completa
        ocorrencia_data = {
            'id': ocorrencia.id,
            'tipo': ocorrencia.tipo.nome if ocorrencia.tipo else 'N/A',
            'tipo_obj': {
                'id': ocorrencia.tipo.id,
                'nome': ocorrencia.tipo.nome
            } if ocorrencia.tipo else None,
            'condominio': ocorrencia.condominio.nome if ocorrencia.condominio else 'N/A',
            'condominio_obj': {
                'id': ocorrencia.condominio.id,
                'nome': ocorrencia.condominio.nome,
                'endereco': None
            } if ocorrencia.condominio else None,
            'data_hora_ocorrencia': ocorrencia.data_hora_ocorrencia.isoformat() if ocorrencia.data_hora_ocorrencia else None,
            'relatorio_final': ocorrencia.relatorio_final,
            'status': ocorrencia.status,
            'endereco_especifico': ocorrencia.endereco_especifico,
            'turno': ocorrencia.turno,
            'data_criacao': ocorrencia.data_criacao.isoformat() if ocorrencia.data_criacao else None,
            'data_modificacao': ocorrencia.data_modificacao.isoformat() if ocorrencia.data_modificacao else None,
            'registrado_por': get_user_name(ocorrencia.registrado_por_user_id),
            'registrado_por_obj': {
                'id': ocorrencia.registrado_por_user_id,
                'username': get_user_name(ocorrencia.registrado_por_user_id)
            },
            'supervisor': get_user_name(ocorrencia.supervisor_id),
            'supervisor_obj': {
                'id': ocorrencia.supervisor_id,
                'username': get_user_name(ocorrencia.supervisor_id)
            } if ocorrencia.supervisor_id else None,
            'colaboradores_envolvidos': [
                {'id': col.id, 'nome': col.nome_completo, 'cargo': col.cargo}
                for col in ocorrencia.colaboradores_envolvidos
            ],
            'orgaos_acionados': [
                {'id': org.id, 'nome': org.nome, 'tipo': org.tipo}
                for org in ocorrencia.orgaos_acionados
            ]
        }
        
        return success_response(
            data={'ocorrencia': ocorrencia_data},
            message='Ocorrência obtida com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrência {ocorrencia_id}: {e}")
        return error_response('Erro interno ao obter ocorrência', status_code=500)


@ocorrencia_api_bp.route('', methods=['POST'])
@jwt_required()
def criar_ocorrencia():
    """Criar nova ocorrência."""
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Dados não fornecidos', status_code=400)
        
        # Validar campos obrigatórios
        required_fields = ['relatorio_final', 'ocorrencia_tipo_id', 'condominio_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return error_response(f'Campos obrigatórios: {", ".join(missing_fields)}', status_code=400)
        
        # Criar ocorrência
        nova_ocorrencia = Ocorrencia(
            relatorio_final=data['relatorio_final'],
            ocorrencia_tipo_id=data['ocorrencia_tipo_id'],
            condominio_id=data['condominio_id'],
            supervisor_id=data.get('supervisor_id'),
            turno=data.get('turno', 'Não especificado'),
            status=data.get('status', 'Registrada'),
            endereco_especifico=data.get('endereco_especifico', ''),
            registrado_por_user_id=get_jwt_identity()
        )
        
        db.session.add(nova_ocorrencia)
        db.session.commit()
        
        logger.info(f"Nova ocorrência criada: ID {nova_ocorrencia.id}")
        
        return success_response(
            data={'ocorrencia_id': nova_ocorrencia.id},
            message='Ocorrência criada com sucesso',
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ocorrência: {e}")
        return error_response('Erro interno ao criar ocorrência', status_code=500)


@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['PUT'])
@jwt_required()
def atualizar_ocorrencia(ocorrencia_id):
    """Atualizar ocorrência existente."""
    try:
        ocorrencia = Ocorrencia.query.get(ocorrencia_id)
        
        if not ocorrencia:
            return error_response('Ocorrência não encontrada', status_code=404)
        
        data = request.get_json()
        
        if not data:
            return error_response('Dados não fornecidos', status_code=400)
        
        # Atualizar campos permitidos
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
        
        db.session.commit()
        
        logger.info(f"Ocorrência {ocorrencia_id} atualizada com sucesso")
        
        return success_response(
            data={'ocorrencia_id': ocorrencia_id},
            message='Ocorrência atualizada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar ocorrência {ocorrencia_id}: {e}")
        return error_response('Erro interno ao atualizar ocorrência', status_code=500)


@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['DELETE'])
@jwt_required()
def deletar_ocorrencia(ocorrencia_id):
    """Deletar ocorrência."""
    try:
        ocorrencia = Ocorrencia.query.get(ocorrencia_id)
        
        if not ocorrencia:
            return error_response('Ocorrência não encontrada', status_code=404)
        
        db.session.delete(ocorrencia)
        db.session.commit()
        
        logger.info(f"Ocorrência {ocorrencia_id} deletada com sucesso")
        
        return success_response(
            data={'ocorrencia_id': ocorrencia_id},
            message='Ocorrência deletada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar ocorrência {ocorrencia_id}: {e}")
        return error_response('Erro interno ao deletar ocorrência', status_code=500)


@ocorrencia_api_bp.route('/<int:ocorrencia_id>/approve', methods=['POST'])
@jwt_required()
def aprovar_ocorrencia(ocorrencia_id):
    """Aprovar ocorrência."""
    try:
        ocorrencia = Ocorrencia.query.get(ocorrencia_id)
        
        if not ocorrencia:
            return error_response('Ocorrência não encontrada', status_code=404)
        
        ocorrencia.status = 'Aprovada'
        db.session.commit()
        
        logger.info(f"Ocorrência {ocorrencia_id} aprovada com sucesso")
        
        return success_response(
            data={'ocorrencia_id': ocorrencia_id, 'status': 'Aprovada'},
            message='Ocorrência aprovada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao aprovar ocorrência {ocorrencia_id}: {e}")
        return error_response('Erro interno ao aprovar ocorrência', status_code=500)


@ocorrencia_api_bp.route('/<int:ocorrencia_id>/reject', methods=['POST'])
@jwt_required()
def rejeitar_ocorrencia(ocorrencia_id):
    """Rejeitar ocorrência."""
    try:
        ocorrencia = Ocorrencia.query.get(ocorrencia_id)
        
        if not ocorrencia:
            return error_response('Ocorrência não encontrada', status_code=404)
        
        ocorrencia.status = 'Rejeitada'
        db.session.commit()
        
        logger.info(f"Ocorrência {ocorrencia_id} rejeitada com sucesso")
        
        return success_response(
            data={'ocorrencia_id': ocorrencia_id, 'status': 'Rejeitada'},
            message='Ocorrência rejeitada com sucesso'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao rejeitar ocorrência {ocorrencia_id}: {e}")
        return error_response('Erro interno ao rejeitar ocorrência', status_code=500)


@ocorrencia_api_bp.route('/analyze-report', methods=['POST'])
@jwt_required(optional=True)
def analisar_relatorio():
    """Analisar relatório usando IA (Extração inteligente)."""
    try:
        from flask_login import current_user
        from flask import current_app
        
        # Verificar autenticação (JWT ou Sessão)
        if not get_jwt_identity() and not current_user.is_authenticated:
            return error_response('Não autorizado', status_code=401)

        data = request.get_json()
        
        if not data or not data.get('relatorio_bruto'):
            return error_response('Relatório bruto é obrigatório', status_code=400)
        
        relatorio_bruto = data['relatorio_bruto']
        formatar_para_email = data.get('formatar_para_email', False)
        
        # Tentar usar a IA para corrigir e formatar o relatório, seguindo o template
        try:
            from app.services.patrimonial_report_service import PatrimonialReportService
            
            # Instancia o serviço de relatório patrimonial (usa o template padrão)
            report_service = PatrimonialReportService()
            
            # Gera o relatório corrigido usando a IA
            relatorio_corrigido = report_service.gerar_relatorio_seguranca(relatorio_bruto)
            
        except Exception as e:
            # Fallback seguro para o parser antigo se a IA falhar (ex: sem API Code, erro de rede)
            current_app.logger.error(f"Falha ao usar PatrimonialReportService: {e}. Usando fallback local.")
            from app.services.ocorrencia_parser import OcorrenciaParser
            relatorio_corrigido = OcorrenciaParser.processar_e_corrigir_texto(relatorio_bruto)

        # Extração de dados (mantém a lógica existente ou usa a do novo serviço se implementada)
        # Por enquanto, mantemos a extração via Regex do OcorrenciaParser para os metadados,
        # pois o PatrimonialReportService foca na geração do TEXTO do relatório.
        from app.services.ocorrencia_parser import OcorrenciaParser
        dados_extraidos = OcorrenciaParser.extrair_dados_relatorio(relatorio_corrigido)
        
        # Preparar resposta
        resposta = {
            'relatorio_processado': relatorio_corrigido, # Use o relatório corrigido, seja pela IA ou fallback
            'dados_extraidos': dados_extraidos,
            'sucesso': True
        }
        
        # Se solicitado, gerar versão para email
        if formatar_para_email:
            relatorio_email = OcorrenciaParser.formatar_para_email_profissional(relatorio_processado)
            resposta['relatorio_email'] = relatorio_email
        
        return success_response(
            data=resposta,
            message='Relatório analisado com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao analisar relatório na API: {e}")
        return error_response('Erro interno ao analisar relatório', status_code=500)

# Funções auxiliares antigas removidas pois agora usamos o serviço



@ocorrencia_api_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos_ocorrencia():
    """Listar tipos de ocorrência."""
    try:
        tipos = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
        
        tipos_data = [{
            'id': tipo.id,
            'nome': tipo.nome,
            'descricao': tipo.descricao
        } for tipo in tipos]
        
        return success_response(
            data={'tipos': tipos_data},
            message='Tipos de ocorrência obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar tipos de ocorrência: {e}")
        return error_response('Erro interno ao listar tipos de ocorrência', status_code=500)


@ocorrencia_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios():
    """Listar condomínios."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        condominios_data = [{
            'id': condominio.id,
            'nome': condominio.nome,
            'endereco': None
        } for condominio in condominios]
        
        return success_response(
            data={'condominios': condominios_data},
            message='Condomínios obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return error_response('Erro interno ao listar condomínios', status_code=500) 

@ocorrencia_api_bp.route('/colaboradores', methods=['GET'])
@jwt_required()
def listar_colaboradores():
    """Listar colaboradores."""
    try:
        colaboradores = Colaborador.query.order_by(Colaborador.nome_completo).all()
        
        colaboradores_data = [{
            'id': col.id,
            'nome': col.nome_completo,
            'cargo': col.cargo,
            'matricula': col.matricula
        } for col in colaboradores]
        
        return success_response(
            data={'colaboradores': colaboradores_data},
            message='Colaboradores obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar colaboradores: {e}")
        return error_response('Erro interno ao listar colaboradores', status_code=500)


@ocorrencia_api_bp.route('/orgaos-publicos', methods=['GET'])
@jwt_required()
def listar_orgaos_publicos():
    """Listar órgãos públicos."""
    try:
        orgaos = OrgaoPublico.query.order_by(OrgaoPublico.nome).all()
        
        orgaos_data = [{
            'id': org.id,
            'nome': org.nome,
            'contato': org.contato
        } for org in orgaos]
        
        return success_response(
            data={'orgaos_publicos': orgaos_data},
            message='Órgãos públicos obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar órgãos públicos: {e}")
        return error_response('Erro interno ao listar órgãos públicos', status_code=500)