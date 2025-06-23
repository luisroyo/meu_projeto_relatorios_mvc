# app/commands.py
import click
from flask.cli import with_appcontext
from .models import User, Ronda, EscalaMensal, RondaSegmento, db # Importar RondaSegmento
import logging
from datetime import datetime
from app.services.ronda_logic.processor import processar_log_de_rondas, MIN_RONDA_DURATION_MINUTES, MAX_RONDA_DURATION_MINUTES # Importar constantes de min/max

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
            return
    db.session.commit()
    click.echo("Comando de inicialização do banco de dados concluído.")


@click.command('assign-supervisors')
@with_appcontext
def assign_supervisors_command():
    """
    Sincroniza TODAS as rondas existentes com as escalas mensais definidas na interface.
    """
    click.echo("Iniciando sincronização em massa de supervisores para TODAS as rondas...")
    try:
        periodos_com_rondas = db.session.query(
            db.extract('year', Ronda.data_plantao_ronda).label('ano'),
            db.extract('month', Ronda.data_plantao_ronda).label('mes')
        ).distinct().all()

        if not periodos_com_rondas:
            click.echo("Nenhuma ronda encontrada no banco de dados para sincronizar.")
            return

        click.echo(f"Encontrados {len(periodos_com_rondas)} períodos distintos (mês/ano) com rondas.")
        
        total_geral_updated = 0
        for periodo in periodos_com_rondas:
            ano, mes = periodo.ano, periodo.mes
            
            escalas_do_mes = EscalaMensal.query.filter_by(ano=ano, mes=mes).all()
            if not escalas_do_mes:
                click.echo(f"-> Pulando período {mes}/{ano}: Nenhuma escala definida na interface.")
                continue

            mapa_escala = {escala.nome_turno: escala.supervisor_id for escala in escalas_do_mes}
            click.echo(f"-> Processando período {mes}/{ano} com a escala: {mapa_escala}")

            periodo_updated_count = 0
            for turno, supervisor_id in mapa_escala.items():
                updated_rows = db.session.query(Ronda).filter(
                    db.extract('year', Ronda.data_plantao_ronda) == ano,
                    db.extract('month', Ronda.data_plantao_ronda) == mes,
                    Ronda.turno_ronda == turno,
                    Ronda.supervisor_id != supervisor_id 
                ).update({'supervisor_id': supervisor_id}, synchronize_session=False)
                
                if updated_rows > 0:
                    periodo_updated_count += updated_rows

            if periodo_updated_count > 0:
                click.echo(f"   - {periodo_updated_count} rondas atualizadas para {mes}/{ano}.")
                total_geral_updated += periodo_updated_count

        db.session.commit()
        click.echo(f"\nOperação concluída! Total de {total_geral_updated} rondas atualizadas em todos os períodos.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Falha na atribuição em massa de supervisores: {e}", exc_info=True)
        click.echo(f"ERRO: A operação falhou e foi revertida. Detalhes: {e}")


@click.command('reprocess-rondas')
@with_appcontext
def reprocess_rondas_command():
    """
    Reprocessa TODAS as rondas existentes no banco de dados para recalcular
    as flags de qualidade (is_incomplete, is_duration_anomalous) e outros campos derivados.
    Útil após mudanças na lógica de processamento de rondas.
    """
    click.echo("Iniciando reprocessamento em massa de todas as rondas...")
    
    total_rondas = Ronda.query.count()
    if total_rondas == 0:
        click.echo("Nenhuma ronda encontrada para reprocessar.")
        return

    click.echo(f"Total de {total_rondas} rondas a serem reprocessadas.")
    
    rondas_reprocessed_count = 0
    rondas_with_errors = 0

    batch_size = 100
    for offset in range(0, total_rondas, batch_size):
        rondas_batch = Ronda.query.order_by(Ronda.id).offset(offset).limit(batch_size).all()
        
        for ronda in rondas_batch:
            try:
                # Deletar segmentos antigos antes de reprocessar e criar novos
                RondaSegmento.query.filter_by(ronda_id=ronda.id).delete()
                db.session.flush() # Descarrega a operação DELETE para o DB imediatamente

                # Chama a função de processamento principal
                relatorio, total, p_evento, u_evento, duracao, rondas_pareadas_processadas = processar_log_de_rondas(
                    log_bruto_rondas_str=ronda.log_ronda_bruto,
                    nome_condominio_str=ronda.condominio_obj.nome if ronda.condominio_obj else "Desconhecido",
                    data_plantao_manual_str=ronda.data_plantao_ronda.strftime('%d/%m/%Y') if ronda.data_plantao_ronda else None,
                    escala_plantao_str=ronda.escala_plantao
                )

                is_incomplete_flag = False
                is_duration_anomalous_flag = False

                if not rondas_pareadas_processadas and total == 0:
                    is_incomplete_flag = True
                    is_duration_anomalous_flag = True
                
                # Para a Ronda principal, a flag é True se QUALQUER segmento for anômalo
                for ronda_pareada in rondas_pareadas_processadas: # Loop com a variável correta
                    if ronda_pareada.get('is_incomplete', False):
                        is_incomplete_flag = True
                    if ronda_pareada.get('is_duration_anomalous', False):
                        is_duration_anomalous_flag = True
                    
                    # Criar e adicionar RondaSegmento para cada segmento pareado
                    segmento = RondaSegmento(
                        ronda_id=ronda.id,
                        inicio_dt=ronda_pareada.get('inicio_dt'), # CORRIGIDO: de segment_data para ronda_pareada
                        termino_dt=ronda_pareada.get('termino_dt'), # CORRIGIDO: de segment_data para ronda_pareada
                        duracao_minutos=ronda_pareada.get('duracao_minutos', 0),
                        vtr=ronda_pareada.get('vtr'),
                        is_incomplete_segment=ronda_pareada.get('is_incomplete', False),
                        is_duration_anomalous_segment=ronda_pareada.get('is_duration_anomalous', False)
                    )
                    db.session.add(segmento)


                # Certifica-se que a flag na Ronda principal reflete a condição GLOBAL de duração anômala
                if duracao is not None:
                    if duracao < MIN_RONDA_DURATION_MINUTES or duracao > MAX_RONDA_DURATION_MINUTES:
                        is_duration_anomalous_flag = True


                # DEBUG LOG
                logger.debug(f"Reprocessando Ronda ID {ronda.id} (Cond: {ronda.condominio_obj.nome if ronda.condominio_obj else 'N/A'}, Data: {ronda.data_plantao_ronda}): Duracao={duracao}min, is_incomplete_calc={is_incomplete_flag}, is_duration_anomalous_calc={is_duration_anomalous_flag}")


                # Atualiza os campos da ronda principal no banco de dados
                ronda.relatorio_processado = relatorio
                ronda.total_rondas_no_log = total
                ronda.primeiro_evento_log_dt = p_evento
                ronda.ultimo_evento_log_dt = u_evento
                ronda.duracao_total_rondas_minutos = duracao
                ronda.is_incomplete = is_incomplete_flag
                ronda.is_duration_anomalous = is_duration_anomalous_flag

                rondas_reprocessed_count += 1
                if rondas_reprocessed_count % 10 == 0:
                    click.echo(f"Processadas {rondas_reprocessed_count}/{total_rondas} rondas...")
            
            except Exception as e:
                db.session.rollback()  # CORREÇÃO: Adicionado rollback para redefinir a transação em caso de erro
                rondas_with_errors += 1
                logger.error(f"Erro ao reprocessar ronda ID {ronda.id}: {e}", exc_info=True)
                click.echo(f"ERRO ao reprocessar ronda ID {ronda.id}: {e}")

        db.session.commit()

    click.echo(f"\nReprocessamento concluído! Total de {rondas_reprocessed_count} rondas reprocessadas.")
    if rondas_with_errors > 0:
        click.echo(f"Atenção: {rondas_with_errors} rondas apresentaram erros durante o reprocessamento. Verifique os logs.")

def init_app(app):
    app.cli.add_command(seed_db_command)
    app.cli.add_command(assign_supervisors_command)
    app.cli.add_command(reprocess_rondas_command)