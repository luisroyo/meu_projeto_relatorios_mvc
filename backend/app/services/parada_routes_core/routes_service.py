import logging
from datetime import datetime
from app import db
from app.models import Condominio, User, Parada, EscalaMensal
from app.services.parada_logic import processar_log_de_paradas
from sqlalchemy import func
import pytz
from app.services.parada_routes_core.helpers import inferir_turno
from app.services.parada_routes_core.validation import validar_campos_essenciais, validar_condominio_existe
from app.services.parada_routes_core.persistence_service import (
    get_parada_by_id, delete_parada, save_parada, update_parada, build_parada_query, list_paradas, get_parada_stats, get_top_supervisor
)
from app.services.parada_routes_core.business_service import atribuir_supervisor
from typing import Optional

logger = logging.getLogger(__name__)

class ParadaRoutesService:
    @staticmethod
    def preparar_dados_formulario():
        """Obtém listas de condomínios e supervisores para popular o formulário."""
        condominios_db = Condominio.query.order_by(Condominio.nome).all()
        supervisores_db = (
            User.query.filter_by(is_supervisor=True, is_approved=True)
            .order_by(User.username)
            .all()
        )
        return condominios_db, supervisores_db

    @staticmethod
    def processar_registro_parada(form, current_user):
        """
        Orquestra o processamento do registro de parada a partir do formulário.
        Retorna: (relatorio_processado_final, condominio_obj, mensagem, status)
        """
        try:
            log_bruto = form.log_bruto_paradas.data
            data_plantao_obj = form.data_plantao.data
            escala_plantao_str = form.escala_plantao.data
            condominio_id_sel = str(form.nome_condominio.data)
            nome_condominio_outro_str = form.nome_condominio_outro.data
            supervisor_id_sel = str(form.supervisor_id.data)

            nome_condo_para_processar = (
                nome_condominio_outro_str
                if condominio_id_sel == "Outro"
                else next((nome for id_, nome in form.nome_condominio.choices if id_ == condominio_id_sel), "")
            )
            data_plantao_fmt = (
                data_plantao_obj.strftime("%d/%m/%Y") if data_plantao_obj else None
            )

            if condominio_id_sel == "Outro":
                condominio_obj = Condominio(nome=nome_condo_para_processar)
                db.session.add(condominio_obj)
                db.session.flush()
            elif condominio_id_sel and condominio_id_sel.isdigit():
                condominio_obj = db.session.get(Condominio, int(condominio_id_sel))
            else:
                condominio_obj = None

            valid, msg = validar_campos_essenciais(log_bruto, condominio_obj, data_plantao_fmt, escala_plantao_str)
            if not valid:
                return None, None, msg, "error"
            valid, msg = validar_condominio_existe(condominio_obj)
            if not valid:
                return None, None, msg, "error"

            relatorio, total, p_evento, u_evento, duracao = processar_log_de_paradas(
                log_bruto_paradas_str=log_bruto or "",
                nome_condominio_str=condominio_obj.nome,
                data_plantao_manual_str=data_plantao_fmt or "",
                escala_plantao_str=escala_plantao_str or "",
            )
            mensagem = "Relatório de parada processado. Verifique os dados e salve se estiver correto."
            status = "success"
            return relatorio, condominio_obj, mensagem, status
        except Exception as e:
            logger.error(f"Erro ao processar o log de paradas: {e}", exc_info=True)
            return None, None, f"Erro ao processar o log de paradas: {str(e)}", "error"

    @staticmethod
    def salvar_parada(data: dict, user: User):
        """
        Orquestra o salvamento de uma parada a partir dos dados recebidos da rota /salvar.
        Retorna: (success: bool, message: str, status_code: int, parada_id: Optional[int])
        """
        from datetime import date
        try:
            parada_id = (
                int(data.get("parada_id"))
                if data.get("parada_id")
                and str(data.get("parada_id")).isdigit()
                and int(data.get("parada_id")) > 0
                else None
            )
            log_bruto = data.get("log_bruto")
            condominio_id_str = data.get("condominio_id")
            nome_condominio_outro = data.get("nome_condominio_outro", "").strip()
            data_plantao_str = data.get("data_plantao")
            escala_plantao = data.get("escala_plantao")
            supervisor_id_manual_str = data.get("supervisor_id")

            condominio_obj = None
            if condominio_id_str == "Outro":
                if not nome_condominio_outro:
                    return False, "O nome do condomínio é obrigatório.", 400, None
                condominio_obj = Condominio.query.filter(
                    func.lower(Condominio.nome) == func.lower(nome_condominio_outro)
                ).first()
                if not condominio_obj:
                    condominio_obj = Condominio(nome=nome_condominio_outro)
                    db.session.add(condominio_obj)
                    db.session.flush()
            elif condominio_id_str and condominio_id_str.isdigit():
                condominio_obj = db.session.get(Condominio, int(condominio_id_str))

            valid, msg = validar_campos_essenciais(log_bruto, condominio_obj, data_plantao_str, escala_plantao)
            if not valid:
                return False, msg, 400, None
            valid, msg = validar_condominio_existe(condominio_obj)
            if not valid:
                return False, msg, 400, None

            data_plantao = date.fromisoformat(data_plantao_str)
            relatorio, total, p_evento, u_evento, duracao = processar_log_de_paradas(
                log_bruto_paradas_str=log_bruto,
                nome_condominio_str=condominio_obj.nome,
                data_plantao_manual_str=data_plantao.strftime("%d/%m/%Y"),
                escala_plantao_str=escala_plantao,
            )

            if total == 0:
                return False, "Não foi possível salvar: Nenhum evento de parada válido foi encontrado no log fornecido.", 400, None

            # --- Fuso horário ---
            primeiro_evento_utc, ultimo_evento_utc = None, None
            local_tz = pytz.timezone("America/Sao_Paulo")
            if p_evento:
                primeiro_evento_utc = local_tz.localize(p_evento).astimezone(pytz.utc)
            if u_evento:
                ultimo_evento_utc = local_tz.localize(u_evento).astimezone(pytz.utc)

            # --- Turno e supervisor ---
            turno_parada = inferir_turno(data_plantao, escala_plantao)
            supervisor_id_para_db = atribuir_supervisor(data_plantao, turno_parada, supervisor_id_manual_str)

            if parada_id:
                parada = get_parada_by_id(parada_id)
                if not parada:
                    return False, "Parada não encontrada para atualização.", 404, None

                if not user.is_admin and parada.user_id != user.id and parada.supervisor_id != user.id:
                    return False, "Você não tem permissão para editar esta parada.", 403, None

                parada.log_parada_bruto = log_bruto
                parada.relatorio_processado = relatorio
                parada.condominio_id = condominio_obj.id
                parada.data_plantao_parada = data_plantao
                parada.escala_plantao = escala_plantao
                parada.turno_parada = turno_parada
                parada.supervisor_id = supervisor_id_para_db
                parada.total_paradas_no_log = total
                parada.primeiro_evento_log_dt = primeiro_evento_utc
                parada.ultimo_evento_log_dt = ultimo_evento_utc
                parada.duracao_total_paradas_minutos = duracao
                update_parada()
                mensagem_sucesso = "Parada atualizada com sucesso!"
            else:
                if Parada.query.filter_by(
                    condominio_id=condominio_obj.id,
                    data_plantao_parada=data_plantao,
                    turno_parada=turno_parada,
                ).first():
                    return False, "Já existe um registro de parada para este condomínio, data e turno.", 409, None
                
                parada = Parada(
                    log_parada_bruto=log_bruto,
                    relatorio_processado=relatorio,
                    condominio_id=condominio_obj.id,
                    escala_plantao=escala_plantao,
                    data_plantao_parada=data_plantao,
                    turno_parada=turno_parada,
                    user_id=user.id,
                    supervisor_id=supervisor_id_para_db,
                    total_paradas_no_log=total,
                    primeiro_evento_log_dt=primeiro_evento_utc,
                    ultimo_evento_log_dt=ultimo_evento_utc,
                    duracao_total_paradas_minutos=duracao,
                    data_hora_inicio=datetime.now(pytz.utc),
                )
                save_parada(parada)
                mensagem_sucesso = "Parada registrada com sucesso!"
            return True, mensagem_sucesso, 200, parada.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar/finalizar parada: {e}", exc_info=True)
            return False, f"Erro interno ao salvar parada: {str(e)}", 500, None

    @staticmethod
    def listar_paradas(page=1, filter_params=None):
        """
        Lista paradas com filtros e paginação.
        """
        filter_params = filter_params or {}
        query = build_parada_query(filter_params)
        paradas_pagination = list_paradas(query, page=page, per_page=10)
        total_paradas, soma_duracao = get_parada_stats(query)
        duracao_media = round(soma_duracao / total_paradas, 2) if total_paradas > 0 else 0
        
        # Obter opções para filtros
        condominios = Condominio.query.order_by(Condominio.nome).all()
        supervisores = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        
        # Buscar lista de turnos distintos das paradas
        turnos_db = db.session.query(Parada.turno_parada).distinct().all()
        turnos = [t[0] for t in turnos_db if t[0]]
        
        supervisor_mais_ativo = get_top_supervisor(query) if total_paradas > 0 else "N/A"

        return (
            paradas_pagination,
            total_paradas,
            soma_duracao,
            duracao_media,
            0, # media_paradas_dia (pode ser mockado ou calculado)
            supervisor_mais_ativo,
            condominios,
            supervisores,
            turnos,
            filter_params
        )

    @staticmethod
    def excluir_parada(parada_id, user):
        """Orquestra a exclusão de uma parada."""
        try:
            parada = get_parada_by_id(parada_id)
            if not parada:
                return False, "Parada não encontrada.", 404

            if not user.is_admin:
                return False, "Apenas administradores podem excluir paradas.", 403

            delete_parada(parada)
            return True, "Parada excluída com sucesso!", 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao excluir parada {parada_id}: {e}", exc_info=True)
            return False, f"Erro ao excluir parada: {str(e)}", 500
