# app/blueprints/admin/routes_dashboard.py
import locale
import logging
import re
from datetime import datetime, timedelta

from flask import flash, redirect, render_template, request, url_for, send_file, make_response
from flask_login import current_user, login_required

## [MELHORIA] Importando Enums para popular os filtros do formulário.
from app.decorators.admin_required import admin_required
from app.models import Condominio, OcorrenciaTipo, Ronda, User
from app.services.dashboard import get_ronda_dashboard_data
from app.services.dashboard.comparativo_dashboard import \
    get_monthly_comparison_data
from app.services.dashboard.main_dashboard import get_main_dashboard_data
from app.services.dashboard.ocorrencia_dashboard import \
    get_ocorrencia_dashboard_data
from app.services.report.ronda_service import RondaReportService
from app.services.report.ocorrencia_service import OcorrenciaReportService
from app.utils.locale_config import LocaleConfig

from . import admin_bp

logger = logging.getLogger(__name__)

# --- Funções Auxiliares ---


def _setup_locale():
    """Tenta configurar o locale para pt_BR para nomes de meses em português."""
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "pt_BR")
        except locale.Error:
            logger.warning(
                "Locale 'pt_BR' não encontrado. Nomes de meses podem aparecer em inglês."
            )


# Configuração de localização usando a nova classe
LocaleConfig.setup_locale()


def _get_date_range_from_month(year, month):
    """Calcula e formata as datas de início e fim para um determinado mês e ano."""
    if not month or not 1 <= month <= 12:
        return None, None
    try:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    except ValueError:
        return None, None


def _get_period_description(year, month, start_date_str, end_date_str):
    """Gera uma descrição amigável para o período de tempo selecionado."""

    def get_month_name(y, m):
        try:
            return LocaleConfig.get_month_name(m, 'pt_BR')
        except Exception:
            # Fallback para o nome do mês padrão do sistema
            return datetime(y, m, 1).strftime("%B")

    if month and year:
        month_name = get_month_name(year, month)
        return f"Referente a {month_name} de {year}"
    elif start_date_str and end_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            if start_dt == end_dt:
                return f"Referente ao dia {start_dt.strftime('%d/%m/%Y')}"
            return f"Período de {start_dt.strftime('%d/%m/%Y')} a {end_dt.strftime('%d/%m/%Y')}"
        except ValueError:
            return "Período de data personalizado"
    else:
        now = datetime.now()
        month_name = get_month_name(now.year, now.month)
        return f"Referente a {month_name} de {now.year}"


def _get_months_of_year(year):
    """Retorna uma lista de dicionários com os meses do ano para filtros."""
    meses = []
    
    for i in range(1, 13):
        try:
            mes_nome = LocaleConfig.get_month_name(i, 'pt_BR')
        except Exception:
            # Fallback para o nome do mês padrão do sistema
            mes_nome = datetime(year, i, 1).strftime("%B")
        meses.append({"id": i, "nome": mes_nome})
    return meses


# --- Rotas do Dashboard ---


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Rota principal do painel admin, redireciona para as métricas gerais."""
    return redirect(url_for("admin.dashboard_metrics"))


@admin_bp.route("/dashboard_metrics")
@login_required
@admin_required
def dashboard_metrics():
    """Exibe o dashboard com métricas gerais do sistema."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de métricas.")
    context_data = get_main_dashboard_data()
    context_data["title"] = "Dashboard de Métricas Gerais"
    return render_template("admin/dashboard.html", **context_data)


@admin_bp.route("/ronda_dashboard")
@login_required
@admin_required
def ronda_dashboard():
    """Exibe o dashboard de métricas e análises de Rondas."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de rondas.")

    current_year = datetime.now().year

    filters = {
        "turno": request.args.get("turno", ""),
        "supervisor_id": request.args.get("supervisor_id", type=int),
        "condominio_id": request.args.get("condominio_id", type=int),
        "mes": request.args.get("mes", type=int),
        "data_inicio_str": request.args.get("data_inicio", ""),
        "data_fim_str": request.args.get("data_fim", ""),
        "data_especifica": request.args.get("data_especifica", ""),
    }

    if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
        start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
        if start_date and end_date:
            filters["data_inicio_str"] = start_date
            filters["data_fim_str"] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters["mes"] = None

    context_data = get_ronda_dashboard_data(filters)

    # --- Preenchendo dados para os filtros do template ---
    context_data["title"] = "Dashboard de Métricas de Rondas"
    ## [MELHORIA] Usando lista de strings para turnos, já que os enums foram removidos.
    context_data["turnos"] = ["Noturno Par", "Noturno Impar", "Diurno Par", "Diurno Impar"]
    context_data["supervisors"] = (
        User.query.filter_by(is_supervisor=True, is_approved=True)
        .order_by(User.username)
        .all()
    )
    context_data["condominios"] = (
        Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    )
    context_data["meses_do_ano"] = _get_months_of_year(current_year)

    context_data["selected_filters"] = filters

    context_data["period_description"] = _get_period_description(
        current_year,
        filters["mes"],
        context_data["selected_data_inicio_str"],
        context_data["selected_data_fim_str"],
    )

    return render_template("admin/ronda_dashboard.html", **context_data)





@admin_bp.route("/ronda_dashboard/export_pdf")
@login_required
@admin_required
def export_ronda_dashboard_pdf():
    """Exporta o dashboard de rondas como PDF."""
    logger.info(f"Usuário '{current_user.username}' exportou relatório PDF do dashboard de rondas.")
    
    try:
        current_year = datetime.now().year
        
        # Aplica os mesmos filtros da rota principal
        filters = {
            "turno": request.args.get("turno", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "condominio_id": request.args.get("condominio_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
            "data_especifica": request.args.get("data_especifica", ""),
        }
        
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        
        # Busca os dados do dashboard
        dashboard_data = get_ronda_dashboard_data(filters)
        
        # Busca nomes reais dos filtros aplicados
        supervisor_name = None
        condominio_name = None
        
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            supervisor_name = supervisor.username if supervisor else "N/A"
        
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            condominio_name = condominio.nome if condominio else "N/A"
        
        # Prepara informações dos filtros para o relatório
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor_name,
            "condominio_name": condominio_name,
            "turno": filters.get("turno", ""),
            "mes": filters.get("mes")
        }
        
        # Gera o PDF
        report_service = RondaReportService()
        pdf_buffer = report_service.generate_ronda_dashboard_pdf(dashboard_data, filters_info)
        
        # Nome do arquivo
        filename = f"relatorio_rondas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF: {e}", exc_info=True)
        flash("Erro ao gerar relatório PDF. Tente novamente.", "danger")
        return redirect(url_for("admin.ronda_dashboard"))


@admin_bp.route("/ocorrencia_dashboard/export_pdf")
@login_required
@admin_required
def export_ocorrencia_dashboard_pdf():
    """Exporta o dashboard de ocorrências como PDF."""
    logger.info(f"Usuário '{current_user.username}' exportou relatório PDF do dashboard de ocorrências.")
    
    try:
        current_year = datetime.now().year
        
        # Aplica os mesmos filtros da rota principal
        filters = {
            "condominio_id": request.args.get("condominio_id", type=int),
            "tipo_id": request.args.get("tipo_id", type=int),
            "status": request.args.get("status", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
        }
        
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        
        # Busca os dados do dashboard
        dashboard_data = get_ocorrencia_dashboard_data(filters)
        
        # Busca nomes reais dos filtros aplicados
        supervisor_name = None
        condominio_name = None
        tipo_name = None
        
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            supervisor_name = supervisor.username if supervisor else "N/A"
        
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            condominio_name = condominio.nome if condominio else "N/A"
        
        if filters.get("tipo_id"):
            tipo = OcorrenciaTipo.query.get(filters["tipo_id"])
            tipo_name = tipo.nome if tipo else "N/A"
        
        # Prepara informações dos filtros para o relatório
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor_name,
            "condominio_name": condominio_name,
            "tipo_name": tipo_name,
            "status": filters.get("status", ""),
            "mes": filters.get("mes")
        }
        
        # Gera o PDF
        report_service = OcorrenciaReportService()
        pdf_buffer = report_service.generate_ocorrencia_dashboard_pdf(dashboard_data, filters_info)
        
        # Nome do arquivo
        filename = f"relatorio_ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF de ocorrências: {e}", exc_info=True)
        flash("Erro ao gerar relatório PDF. Tente novamente.", "danger")
        return redirect(url_for("admin.ocorrencia_dashboard"))


@admin_bp.route("/ocorrencia_dashboard")
@login_required
@admin_required
def ocorrencia_dashboard():
    """Exibe o dashboard de métricas e análises de Ocorrências."""
    logger.info(
        f"Usuário '{current_user.username}' acessou o dashboard de ocorrências."
    )

    current_year = datetime.now().year

    filters = {
        "condominio_id": request.args.get("condominio_id", type=int),
        "tipo_id": request.args.get("tipo_id", type=int),
        "status": request.args.get("status", ""),
        "supervisor_id": request.args.get("supervisor_id", type=int),
        "mes": request.args.get("mes", type=int),
        "data_inicio_str": request.args.get("data_inicio", ""),
        "data_fim_str": request.args.get("data_fim", ""),
    }

    if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
        start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
        if start_date and end_date:
            filters["data_inicio_str"] = start_date
            filters["data_fim_str"] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters["mes"] = None

    ## [MELHORIA CRÍTICA] A rota agora apenas chama o serviço e passa os dados.
    # Toda a lógica de cálculo de KPIs foi movida para dashboard_service.py.
    context_data = get_ocorrencia_dashboard_data(filters)

    # --- Preenchendo dados para os filtros do template ---
    context_data["title"] = "Dashboard de Ocorrências"
    context_data["condominios"] = Condominio.query.order_by(Condominio.nome).all()
    context_data["tipos_ocorrencia"] = OcorrenciaTipo.query.order_by(
        OcorrenciaTipo.nome
    ).all()
    context_data["supervisors"] = (
        User.query.filter_by(is_supervisor=True, is_approved=True)
        .order_by(User.username)
        .all()
    )
    ## [MELHORIA] Usando Enum para popular a lista de status.
    context_data["status_list"] = [
        'Registrada',
        'Em Andamento',
        'Concluída'
    ]
    context_data["meses_do_ano"] = _get_months_of_year(current_year)

    ## [MELHORIA] Passando o dicionário de filtros diretamente para o template.
    # Isso simplifica o código e evita atribuições manuais e repetitivas.
    context_data["selected_filters"] = filters
    
    # Adicionando variáveis selected_* para compatibilidade com o template
    context_data["selected_status"] = filters.get("status", "")
    context_data["selected_condominio_id"] = filters.get("condominio_id")
    context_data["selected_tipo_id"] = filters.get("tipo_id")
    context_data["selected_supervisor_id"] = filters.get("supervisor_id")
    context_data["selected_mes"] = filters.get("mes")
    context_data["selected_data_inicio_str"] = filters.get("data_inicio_str", "")
    context_data["selected_data_fim_str"] = filters.get("data_fim_str", "")

    context_data["period_description"] = _get_period_description(
        current_year,
        filters.get("mes"),
        context_data["selected_data_inicio_str"],
        context_data["selected_data_fim_str"],
    )

    # A rota agora está muito mais limpa e focada em sua responsabilidade.
    return render_template("admin/ocorrencia_dashboard.html", **context_data)


# --- [NOVO] Rota para o Dashboard Comparativo ---
@admin_bp.route("/dashboard/comparativo")
@login_required
@admin_required
def dashboard_comparativo():
    """Exibe o dashboard comparativo de rondas vs ocorrências."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard comparativo.")

    # Parâmetros de filtro
    year = request.args.get("year", type=int) or datetime.now().year
    comparison_mode = request.args.get("comparison_mode", "all")  # 'all', 'single', 'comparison'
    
    # Seleção de meses
    selected_months = []
    if comparison_mode == 'single':
        month = request.args.get("selected_month", type=int)
        if month and 1 <= month <= 12:
            selected_months = [month]
    elif comparison_mode == 'comparison':
        months_str = request.args.get("selected_months", "")
        if months_str:
            try:
                selected_months = [int(m) for m in months_str.split(',') if 1 <= int(m) <= 12]
            except ValueError:
                selected_months = []

    filters = {
        "condominio_id": request.args.get("condominio_id", type=int),
        "supervisor_id": request.args.get("supervisor_id", type=int),
        "turno": request.args.get("turno", ""),
        "tipo_ocorrencia_id": request.args.get("tipo_ocorrencia_id", type=int),
        "status": request.args.get("status", ""),
        "data_inicio_str": request.args.get("data_inicio", ""),
        "data_fim_str": request.args.get("data_fim", ""),
    }

    # Remove filtros vazios
    filters = {k: v for k, v in filters.items() if v not in [None, ""]}

    # Busca dados
    data = get_monthly_comparison_data(
        year=year, 
        filters=filters, 
        selected_months=selected_months,
        comparison_mode=comparison_mode
    )

    # Adiciona dados para o template
    data["title"] = "Dashboard Comparativo: Rondas vs Ocorrências"
    data["selected_year"] = year
    data["comparison_mode"] = comparison_mode
    data["selected_months"] = selected_months

    return render_template("admin/dashboard_comparativo.html", **data)


@admin_bp.route("/ronda_dashboard/export_pdf_html")
@login_required
@admin_required
def export_ronda_dashboard_pdf_html():
    """Exporta o dashboard de rondas como PDF estilizado via ReportLab."""
    logger.info(f"Usuário '{current_user.username}' exportou relatório PDF HTML do dashboard de rondas.")
    try:
        current_year = datetime.now().year
        filters = {
            "turno": request.args.get("turno", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "condominio_id": request.args.get("condominio_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
            "data_especifica": request.args.get("data_especifica", ""),
        }
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        dashboard_data = get_ronda_dashboard_data(filters)
        
        # Usar o serviço de relatório existente que já usa ReportLab
        report_service = RondaReportService()
        
        # Preparar informações dos filtros para o relatório
        filters_info = {}
        if filters.get("data_inicio_str"):
            filters_info["data_inicio"] = filters["data_inicio_str"]
        if filters.get("data_fim_str"):
            filters_info["data_fim"] = filters["data_fim_str"]
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            if supervisor:
                filters_info["supervisor_name"] = supervisor.username
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            if condominio:
                filters_info["condominio_name"] = condominio.nome
        if filters.get("turno"):
            filters_info["turno"] = filters["turno"]
        if filters.get("mes"):
            filters_info["mes"] = filters["mes"]
        
        pdf_data = report_service.generate_ronda_dashboard_pdf(dashboard_data, filters_info)
        
        filename = f"relatorio_rondas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_data,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF HTML: {e}", exc_info=True)
        flash("Erro ao gerar relatório PDF. Tente novamente.", "danger")
        return redirect(url_for("admin.ronda_dashboard"))


@admin_bp.route("/ronda_dashboard/preview")
@login_required
@admin_required
def preview_ronda_dashboard_report():
    """Pré-visualiza o relatório de rondas em HTML antes do download do PDF."""
    logger.info(f"Usuário '{current_user.username}' acessou a pré-visualização do relatório de rondas.")
    try:
        current_year = datetime.now().year
        filters = {
            "turno": request.args.get("turno", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "condominio_id": request.args.get("condominio_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
            "data_especifica": request.args.get("data_especifica", ""),
        }
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            from app.services.dashboard.helpers.date_utils import get_date_range_from_month
            start_date, end_date = get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        dashboard_data = get_ronda_dashboard_data(filters)
        supervisor_name = None
        condominio_name = None
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            supervisor_name = supervisor.username if supervisor else "N/A"
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            condominio_name = condominio.nome if condominio else "N/A"
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor_name,
            "condominio_name": condominio_name,
            "turno": filters.get("turno", ""),
            "mes": filters.get("mes")
        }
        return render_template(
            "admin/ronda_dashboard_preview.html",
            title="Pré-visualização do Relatório de Rondas",
            dashboard_data=dashboard_data,
            filters_info=filters_info,
            request_args=request.args
        )
    except Exception as e:
        logger.error(f"Erro ao gerar pré-visualização do relatório: {e}", exc_info=True)
        flash("Erro ao gerar pré-visualização do relatório. Tente novamente.", "danger")
        return redirect(url_for("admin.ronda_dashboard"))


@admin_bp.route("/ronda_dashboard/export_pdf_compact")
@login_required
@admin_required
def export_ronda_dashboard_pdf_compact():
    """Exporta o dashboard de rondas como PDF compacto."""
    logger.info(f"Usuário '{current_user.username}' exportou relatório PDF compacto do dashboard de rondas.")
    
    try:
        current_year = datetime.now().year
        
        # Aplica os mesmos filtros da rota principal
        filters = {
            "turno": request.args.get("turno", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "condominio_id": request.args.get("condominio_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
            "data_especifica": request.args.get("data_especifica", ""),
        }
        
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        
        # Busca os dados do dashboard
        dashboard_data = get_ronda_dashboard_data(filters)
        
        # Busca nomes reais dos filtros aplicados
        supervisor_name = None
        condominio_name = None
        
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            supervisor_name = supervisor.username if supervisor else "N/A"
        
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            condominio_name = condominio.nome if condominio else "N/A"
        
        # Prepara informações dos filtros para o relatório
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor_name,
            "condominio_name": condominio_name,
            "turno": filters.get("turno", ""),
            "mes": filters.get("mes")
        }
        
        # Gera o PDF compacto
        report_service = RondaReportService()
        pdf_buffer = report_service.generate_compact_ronda_dashboard_pdf(dashboard_data, filters_info)
        
        # Nome do arquivo
        filename = f"relatorio_rondas_compacto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF compacto: {e}", exc_info=True)
        flash("Erro ao gerar relatório PDF compacto. Tente novamente.", "danger")
        return redirect(url_for("admin.ronda_dashboard"))


@admin_bp.route("/ocorrencia_dashboard/export_pdf_compact")
@login_required
@admin_required
def export_ocorrencia_dashboard_pdf_compact():
    """Exporta o dashboard de ocorrências como PDF compacto."""
    logger.info(f"Usuário '{current_user.username}' exportou relatório PDF compacto do dashboard de ocorrências.")
    
    try:
        current_year = datetime.now().year
        
        # Aplica os mesmos filtros da rota principal
        filters = {
            "condominio_id": request.args.get("condominio_id", type=int),
            "tipo_id": request.args.get("tipo_id", type=int),
            "status": request.args.get("status", ""),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "mes": request.args.get("mes", type=int),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
        }
        
        if filters["mes"] and not (filters["data_inicio_str"] or filters["data_fim_str"]):
            start_date, end_date = _get_date_range_from_month(current_year, filters["mes"])
            if start_date and end_date:
                filters["data_inicio_str"] = start_date
                filters["data_fim_str"] = end_date
        
        # Busca os dados do dashboard
        dashboard_data = get_ocorrencia_dashboard_data(filters)
        
        # Busca nomes reais dos filtros aplicados
        supervisor_name = None
        condominio_name = None
        tipo_name = None
        
        if filters.get("supervisor_id"):
            supervisor = User.query.get(filters["supervisor_id"])
            supervisor_name = supervisor.username if supervisor else "N/A"
        
        if filters.get("condominio_id"):
            condominio = Condominio.query.get(filters["condominio_id"])
            condominio_name = condominio.nome if condominio else "N/A"
        
        if filters.get("tipo_id"):
            tipo = OcorrenciaTipo.query.get(filters["tipo_id"])
            tipo_name = tipo.nome if tipo else "N/A"
        
        # Prepara informações dos filtros para o relatório
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor_name,
            "condominio_name": condominio_name,
            "tipo_name": tipo_name,
            "status": filters.get("status", ""),
            "mes": filters.get("mes")
        }
        
        # Gera o PDF compacto
        report_service = OcorrenciaReportService()
        pdf_buffer = report_service.generate_compact_ocorrencia_dashboard_pdf(dashboard_data, filters_info)
        
        # Nome do arquivo
        filename = f"relatorio_ocorrencias_compacto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF compacto de ocorrências: {e}", exc_info=True)
        flash("Erro ao gerar relatório PDF compacto. Tente novamente.", "danger")
        return redirect(url_for("admin.ocorrencia_dashboard"))


@admin_bp.route("/rondas/alertas")
@login_required
@admin_required
def verificar_alertas_rondas():
    """Exibe página para verificar alertas em rondas salvas."""
    logger.info(f"Usuário '{current_user.username}' acessou a página de alertas de rondas.")
    
    current_year = datetime.now().year
    
    # Filtros da query string
    condominio_id = request.args.get("condominio_id", type=int)
    supervisor_id = request.args.get("supervisor_id", type=int)
    turno = request.args.get("turno", "")
    mes = request.args.get("mes", type=int)
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")
    
    # Constrói a query base
    query = Ronda.query.order_by(Ronda.data_plantao_ronda.desc(), Ronda.id.desc())
    
    # Aplica filtros
    if condominio_id:
        query = query.filter(Ronda.condominio_id == condominio_id)
    
    if supervisor_id:
        query = query.filter(Ronda.supervisor_id == supervisor_id)
    
    if turno:
        query = query.filter(Ronda.turno_ronda == turno)
    
    # Se mês foi selecionado e não há datas específicas, calcula o range do mês
    if mes and not (data_inicio or data_fim):
        start_date, end_date = _get_date_range_from_month(current_year, mes)
        if start_date and end_date:
            data_inicio = start_date
            data_fim = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            mes = None
    
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            query = query.filter(Ronda.data_plantao_ronda >= data_inicio_dt)
        except ValueError:
            flash("Data de início inválida. Use o formato YYYY-MM-DD", "danger")
            data_inicio = ""
    
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d").date()
            query = query.filter(Ronda.data_plantao_ronda <= data_fim_dt)
        except ValueError:
            flash("Data de fim inválida. Use o formato YYYY-MM-DD", "danger")
            data_fim = ""
    
    # Busca todas as rondas
    rondas = query.all()
    
    # Padrões para identificar alertas
    padrao_secao_alertas = re.compile(
        r'Observações/Alertas de Pareamento:',
        re.IGNORECASE
    )
    
    rondas_com_alertas = []
    total_alertas = 0
    
    # Processa cada ronda
    for ronda in rondas:
        if not ronda.relatorio_processado:
            continue
        
        relatorio = ronda.relatorio_processado
        
        # Verifica se há seção de alertas
        if padrao_secao_alertas.search(relatorio):
            # Extrai os alertas
            alertas_encontrados = []
            
            # Encontra a posição da seção de alertas
            match_secao = padrao_secao_alertas.search(relatorio)
            if match_secao:
                # Pega o texto a partir da seção de alertas
                texto_alertas = relatorio[match_secao.end():]
                
                # Extrai cada alerta (linhas que começam com "- ⚠️")
                linhas = texto_alertas.split('\n')
                for linha in linhas:
                    linha = linha.strip()
                    if linha.startswith('- ⚠️') or linha.startswith('⚠️'):
                        # Remove o prefixo "- ⚠️" ou "⚠️"
                        alerta_limpo = re.sub(r'^-\s*⚠️\s*', '', linha)
                        alerta_limpo = re.sub(r'^⚠️\s*', '', alerta_limpo)
                        if alerta_limpo:
                            alertas_encontrados.append(alerta_limpo)
            
            if alertas_encontrados:
                # Categoriza os alertas
                alertas_categorizados = {
                    'horario': [],
                    'sem_inicio': [],
                    'sem_termino': [],
                    'outros': []
                }
                
                for alerta in alertas_encontrados:
                    if 'ALERTA DE HORÁRIO' in alerta.upper() or 'ocorreu ANTES' in alerta:
                        alertas_categorizados['horario'].append(alerta)
                    elif 'sem início' in alerta.lower() or 'sem inicio' in alerta.lower():
                        alertas_categorizados['sem_inicio'].append(alerta)
                    elif 'sem término' in alerta.lower() or 'sem termino' in alerta.lower():
                        alertas_categorizados['sem_termino'].append(alerta)
                    else:
                        alertas_categorizados['outros'].append(alerta)
                
                rondas_com_alertas.append({
                    'ronda': ronda,
                    'alertas': alertas_encontrados,
                    'alertas_categorizados': alertas_categorizados,
                    'total_alertas': len(alertas_encontrados)
                })
                total_alertas += len(alertas_encontrados)
    
    # Estatísticas
    stats = {
        'total_rondas': len(rondas),
        'rondas_com_alertas': len(rondas_com_alertas),
        'total_alertas': total_alertas,
        'alertas_horario': sum(len(item['alertas_categorizados']['horario']) for item in rondas_com_alertas),
        'alertas_sem_inicio': sum(len(item['alertas_categorizados']['sem_inicio']) for item in rondas_com_alertas),
        'alertas_sem_termino': sum(len(item['alertas_categorizados']['sem_termino']) for item in rondas_com_alertas),
        'alertas_outros': sum(len(item['alertas_categorizados']['outros']) for item in rondas_com_alertas),
    }
    
    if len(rondas) > 0:
        stats['porcentagem_com_alertas'] = round((len(rondas_com_alertas) / len(rondas)) * 100, 1)
    else:
        stats['porcentagem_com_alertas'] = 0
    
    # Dados para os filtros
    condominios = Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    supervisors = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    turnos = ["Noturno Par", "Noturno Impar", "Diurno Par", "Diurno Impar"]
    meses_do_ano = _get_months_of_year(current_year)
    
    return render_template(
        "admin/rondas_alertas.html",
        title="Verificação de Alertas em Rondas",
        rondas_com_alertas=rondas_com_alertas,
        stats=stats,
        condominios=condominios,
        supervisors=supervisors,
        turnos=turnos,
        meses_do_ano=meses_do_ano,
        selected_condominio_id=condominio_id,
        selected_supervisor_id=supervisor_id,
        selected_turno=turno,
        selected_mes=mes,
        selected_data_inicio=data_inicio,
        selected_data_fim=data_fim,
    )
