import logging
from datetime import datetime
from app import db
from app.models import Condominio, User, Ronda, EscalaMensal
from app.services.rondaservice import processar_log_de_rondas
from sqlalchemy import func
import pytz
from app.services.ronda_routes_core.helpers import inferir_turno
from app.services.ronda_routes_core.validation import validar_campos_essenciais, validar_condominio_existe
from app.services.ronda_routes_core.persistence_service import (
    get_ronda_by_id, delete_ronda, save_ronda, update_ronda, build_ronda_query, list_rondas, get_ronda_stats, get_top_supervisor
)
from app.services.ronda_routes_core.business_service import atribuir_supervisor

logger = logging.getLogger(__name__)

class RondaRoutesService:
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
    def processar_registro_ronda(form, current_user):
        """
        Orquestra o processamento do registro de ronda a partir do formulário.
        Retorna: (relatorio_processado_final, condominio_obj, mensagem, status)
        """
        try:
            log_bruto = form.log_bruto_rondas.data
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
                condominio_obj = db.get_or_404(Condominio, int(condominio_id_sel))
            else:
                condominio_obj = None

            valid, msg = validar_campos_essenciais(log_bruto, condominio_obj, data_plantao_fmt, escala_plantao_str)
            if not valid:
                return None, None, msg, "error"
            valid, msg = validar_condominio_existe(condominio_obj)
            if not valid:
                return None, None, msg, "error"

            relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
                log_bruto_rondas_str=log_bruto or "",
                nome_condominio_str=condominio_obj.nome,
                data_plantao_manual_str=data_plantao_fmt or "",
                escala_plantao_str=escala_plantao_str or "",
            )
            mensagem = "Relatório de ronda processado. Verifique os dados e salve se estiver correto."
            status = "success"
            return relatorio, condominio_obj, mensagem, status
        except Exception as e:
            logger.error(f"Erro ao processar o log de rondas: {e}", exc_info=True)
            return None, None, f"Erro ao processar o log de rondas: {str(e)}", "error"

    @staticmethod
    def salvar_ronda(data, current_user):
        """
        Orquestra o salvamento de uma ronda a partir dos dados recebidos da rota /salvar.
        Retorna: (success: bool, message: str, status_code: int, ronda_id: Optional[int])
        """
        from datetime import date, datetime, timezone
        try:
            ronda_id = (
                int(data.get("ronda_id"))
                if data.get("ronda_id")
                and str(data.get("ronda_id")).isdigit()
                and int(data.get("ronda_id")) > 0
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
                condominio_obj = db.get_or_404(Condominio, int(condominio_id_str))

            valid, msg = validar_campos_essenciais(log_bruto, condominio_obj, data_plantao_str, escala_plantao)
            if not valid:
                return False, msg, 400, None
            valid, msg = validar_condominio_existe(condominio_obj)
            if not valid:
                return False, msg, 400, None

            data_plantao = date.fromisoformat(data_plantao_str)
            relatorio, total, p_evento, u_evento, duracao = processar_log_de_rondas(
                log_bruto_rondas_str=log_bruto,
                nome_condominio_str=condominio_obj.nome,
                data_plantao_manual_str=data_plantao.strftime("%d/%m/%Y"),
                escala_plantao_str=escala_plantao,
            )

            if total == 0:
                return False, "Não foi possível salvar: Nenhum evento de ronda válido foi encontrado no log fornecido.", 400, None

            # --- Fuso horário ---
            primeiro_evento_utc, ultimo_evento_utc = None, None
            local_tz = pytz.timezone("America/Sao_Paulo")
            if p_evento:
                primeiro_evento_utc = local_tz.localize(p_evento).astimezone(pytz.utc)
            if u_evento:
                ultimo_evento_utc = local_tz.localize(u_evento).astimezone(pytz.utc)

            # --- Turno e supervisor ---
            turno_ronda = inferir_turno(data_plantao, escala_plantao)
            supervisor_id_para_db = atribuir_supervisor(data_plantao, turno_ronda, supervisor_id_manual_str)

            if ronda_id:
                ronda = get_ronda_by_id(ronda_id)
                ronda.log_ronda_bruto = log_bruto
                ronda.relatorio_processado = relatorio
                ronda.condominio_id = condominio_obj.id
                ronda.data_plantao_ronda = data_plantao
                ronda.escala_plantao = escala_plantao
                ronda.turno_ronda = turno_ronda
                ronda.supervisor_id = supervisor_id_para_db
                ronda.total_rondas_no_log = total
                ronda.primeiro_evento_log_dt = primeiro_evento_utc
                ronda.ultimo_evento_log_dt = ultimo_evento_utc
                ronda.duracao_total_rondas_minutos = duracao
                update_ronda()
                mensagem_sucesso = "Ronda atualizada com sucesso!"
            else:
                from app.models import Ronda
                if Ronda.query.filter_by(
                    condominio_id=condominio_obj.id,
                    data_plantao_ronda=data_plantao,
                    turno_ronda=turno_ronda,
                ).first():
                    return False, "Já existe uma ronda para este condomínio, data e turno.", 409, None
                ronda = Ronda(
                    log_ronda_bruto=log_bruto,
                    relatorio_processado=relatorio,
                    condominio_id=condominio_obj.id,
                    escala_plantao=escala_plantao,
                    data_plantao_ronda=data_plantao,
                    turno_ronda=turno_ronda,
                    user_id=current_user.id,
                    supervisor_id=supervisor_id_para_db,
                    total_rondas_no_log=total,
                    primeiro_evento_log_dt=primeiro_evento_utc,
                    ultimo_evento_log_dt=ultimo_evento_utc,
                    duracao_total_rondas_minutos=duracao,
                    data_hora_inicio=datetime.now(timezone.utc),
                )
                save_ronda(ronda)
                mensagem_sucesso = "Ronda registrada com sucesso!"
            return True, mensagem_sucesso, 200, ronda.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar/finalizar ronda: {e}", exc_info=True)
            return False, f"Erro interno ao salvar ronda: {str(e)}", 500, None

    @staticmethod
    def listar_rondas(page=1, filter_params=None):
        """
        Lista rondas com filtros e paginação. Retorna: (pagination, total_rondas, soma_duracao, duracao_media, media_rondas_dia, supervisor_mais_ativo, condominios, supervisores, turnos, active_filter_params)
        """
        from app.models import Condominio, User
        filter_params = filter_params or {}
        query = build_ronda_query(filter_params)
        rondas_pagination = list_rondas(query, page=page, per_page=10)
        total_rondas, soma_duracao = get_ronda_stats(query)
        duracao_media = round(soma_duracao / total_rondas, 2) if total_rondas > 0 else 0
        data_inicio_obj, data_fim_obj = None, None
        if filter_params.get("data_inicio") and filter_params.get("data_fim"):
            from datetime import date
            try:
                data_inicio_obj = date.fromisoformat(filter_params["data_inicio"])
                data_fim_obj = date.fromisoformat(filter_params["data_fim"])
                if (data_fim_obj - data_inicio_obj).days >= 0:
                    num_dias = (data_fim_obj - data_inicio_obj).days + 1
                    media_rondas_dia = round(total_rondas / num_dias, 1)
                else:
                    media_rondas_dia = "N/A"
            except (ValueError, TypeError):
                media_rondas_dia = "N/A"
        else:
            media_rondas_dia = "N/A"
        supervisor_mais_ativo = get_top_supervisor(query)
        condominios = Condominio.query.order_by(Condominio.nome).all()
        supervisors = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        turnos = ["Noturno Par", "Noturno Impar", "Diurno Par", "Diurno Impar"]
        active_filter_params = {k: v for k, v in filter_params.items() if v not in [None, ""]}
        return (
            rondas_pagination, total_rondas, soma_duracao, duracao_media, media_rondas_dia,
            supervisor_mais_ativo, condominios, supervisors, turnos, active_filter_params
        )

    @staticmethod
    def detalhes_ronda(ronda_id):
        return get_ronda_by_id(ronda_id)

    @staticmethod
    def excluir_ronda(ronda_id):
        try:
            ronda = get_ronda_by_id(ronda_id)
            delete_ronda(ronda)
            return True, f"Ronda #{ronda.id} excluída com sucesso.", 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao excluir ronda {ronda_id}: {e}", exc_info=True)
            return False, f"Erro ao excluir ronda: {str(e)}", 500 