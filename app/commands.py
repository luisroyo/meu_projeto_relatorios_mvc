# app/commands.py
import click
import logging
from flask.cli import with_appcontext
from .models import User, Ronda, EscalaMensal, TipoOcorrencia # Adicionado TipoOcorrencia
from . import db
from datetime import datetime

logger = logging.getLogger(__name__)

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Cria os usuários administradores e supervisores padrão."""
    default_users = [
        {"username": "Luis Royo", "email": "luisroyo25@gmail.com", "password": "edu123cs", "is_admin": True, "is_supervisor": True},
        {"username": "Romel / Arnaldo", "email": "romel.arnaldo@example.com", "password": "password123", "is_admin": False, "is_supervisor": True},
        {"username": "Gleison", "email": "gleison@example.com", "password": "password123", "is_admin": False, "is_supervisor": True},
        {"username": "Douglas", "email": "douglas@example.com", "password": "password123", "is_admin": False, "is_supervisor": True}
    ]
    for user_data in default_users:
        try:
            user_exists = User.query.filter_by(email=user_data['email']).first()
            if not user_exists:
                new_user = User(
                    username=user_data['username'], email=user_data['email'],
                    is_admin=user_data.get('is_admin', False), is_supervisor=user_data.get('is_supervisor', False),
                    is_approved=True
                )
                new_user.set_password(user_data['password'])
                db.session.add(new_user)
                click.echo(f"Usuário '{user_data['username']}' criado com sucesso.")
            else:
                if user_data.get('is_supervisor') and not user_exists.is_supervisor:
                    user_exists.is_supervisor = True
                    click.echo(f"Usuário '{user_data['username']}' atualizado para supervisor.")
                else:
                    click.echo(f"Usuário '{user_data['username']}' já existe.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Falha ao criar/atualizar usuário '{user_data['username']}': {e}", exc_info=True)
            click.echo(f"Erro ao processar usuário '{user_data['username']}': {e}")
            return # Retorna para evitar commit de sessão inconsistente
    db.session.commit()
    click.echo("Comando de inicialização do banco de dados concluído.")

# --- ADIÇÃO CRÍTICA: COMANDO seed-ocorrencias ---
@click.command('seed-ocorrencias')
@with_appcontext
def seed_ocorrencias_command():
    """Cria os tipos de ocorrência iniciais no banco de dados."""
    try:
        tipos_iniciais = [
            {'nome': 'Perturbação de Sossego', 'categoria': 'Atendimento ao Público'},
            {'nome': 'Conflito entre Moradores', 'categoria': 'Atendimento ao Público'},
            {'nome': 'Orientação Geral', 'categoria': 'Atendimento ao Público'},
            {'nome': 'Primeiros Socorros', 'categoria': 'Atendimento ao Público'},
            {'nome': 'Apoio Externo (Polícia/Bombeiros)', 'categoria': 'Segurança Patrimonial'},
            {'nome': 'Atitude Suspeita', 'categoria': 'Segurança Patrimonial'},
            {'nome': 'Disparo de Alarme', 'categoria': 'Segurança Patrimonial'},
            {'nome': 'Vandalismo / Dano ao Patrimônio', 'categoria': 'Segurança Patrimonial'},
            {'nome': 'Violação de Perímetro', 'categoria': 'Segurança Patrimonial'},
            {'nome': 'Falha de Equipamento (Câmera, Portão)', 'categoria': 'Operacional'},
            {'nome': 'Ronda não Conforme', 'categoria': 'Operacional'},
            {'nome': 'Problema na Escala', 'categoria': 'Operacional'},
        ]
        
        tipos_existentes = {t.nome for t in TipoOcorrencia.query.all()}
        
        count = 0
        for tipo_data in tipos_iniciais:
            if tipo_data['nome'] not in tipos_existentes:
                novo_tipo = TipoOcorrencia(nome=tipo_data['nome'], categoria=tipo_data.get('categoria'))
                db.session.add(novo_tipo)
                count += 1
                click.echo(f"Adicionado tipo: {tipo_data['nome']}")
        
        if count > 0:
            db.session.commit()
            click.echo(f"\n{count} novos tipos de ocorrência foram adicionados com sucesso!")
        else:
            click.echo("\nNenhum novo tipo de ocorrência para adicionar. O banco de dados já está populado.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Falha ao popular tipos de ocorrência: {e}", exc_info=True)
        click.echo(f"ERRO: A operação falhou. Detalhes: {e}")
        return # Retorna para evitar commit de sessão inconsistente

# --- VERSÃO FINAL E MAIS PODEROSA DO COMANDO ---
@click.command('assign-supervisors')
@with_appcontext
def assign_supervisors_command():
    """
    Sincroniza TODAS as rondas existentes com as escalas mensais definidas na interface.
    """
    click.echo("Iniciando sincronização em massa de supervisores para TODAS as rondas...")
    try:
        # 1. Encontra todos os períodos (ano, mês) únicos que têm rondas
        periodos_com_rondas = db.session.query(
            db.extract('year', Ronda.data_plantao_ronda).label('ano'),
            db.extract('month', Ronda.data_plantao_ronda).label('mes')
        ).distinct().all()

        if not periodos_com_rondas:
            click.echo("Nenhuma ronda encontrada no banco de dados para sincronizar.")
            return

        click.echo(f"Encontrados {len(periodos_com_rondas)} períodos distintos (mês/ano) com rondas.")
        
        total_geral_updated = 0
        # 2. Para cada período, busca a escala e atualiza as rondas
        for periodo in periodos_com_rondas:
            ano, mes = periodo.ano, periodo.mes
            
            escalas_do_mes = EscalaMensal.query.filter_by(ano=ano, mes=mes).all()
            if not escalas_do_mes:
                click.echo(f"-> Pulando período {mes}/{ano}: Nenhuma escala definida na interface.")
                continue

            mapa_escala = {escala.nome_turno: escala.supervisor_id for escala in escalas_do_mes}
            click.echo(f"-> Processando período {mes}/{ano} com a escala: {mapa_escala}")

            periodo_updated_count = 0
            # 3. Para cada turno definido na escala, atualiza as rondas correspondentes
            for turno, supervisor_id in mapa_escala.items():
                updated_rows = db.session.query(Ronda).filter(
                    db.extract('year', Ronda.data_plantao_ronda) == ano,
                    db.extract('month', Ronda.data_plantao_ronda) == mes,
                    Ronda.turno_ronda == turno,
                    # Atualiza apenas se o supervisor for diferente, para otimizar
                    Ronda.supervisor_id != supervisor_id 
                ).update({'supervisor_id': supervisor_id}, synchronize_session=False)
                
                if updated_rows > 0:
                    periodo_updated_count += updated_rows

            if periodo_updated_count > 0:
                click.echo(f"   - {periodo_updated_count} rondas atualizadas para {mes}/{ano}.")
                total_geral_updated += periodo_updated_count

        # 4. Salva todas as alterações no banco de dados de uma vez
        db.session.commit()
        click.echo(f"\nOperação concluída! Total de {total_geral_updated} rondas atualizadas em todos os períodos.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Falha na atribuição em massa de supervisores: {e}", exc_info=True)
        click.echo(f"ERRO: A operação falhou e foi revertida. Detalhes: {e}")

