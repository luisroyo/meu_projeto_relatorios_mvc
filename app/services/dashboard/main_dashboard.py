# app/services/dashboard/main_dashboard.py
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app import db
from app.models import LoginHistory, ProcessingHistory, User

from .helpers import chart_data, date_utils

logger = logging.getLogger(__name__)


def get_main_dashboard_data():
    """Busca e processa os dados para o dashboard principal de métricas."""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc).date()

    total_users = db.session.query(func.count(User.id)).scalar()
    total_approved_users = (
        db.session.query(func.count(User.id)).filter_by(is_approved=True).scalar()
    )
    total_pending_users = total_users - total_approved_users

    successful_logins = (
        db.session.query(func.count(LoginHistory.id))
        .filter(LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == True)
        .scalar()
    )
    failed_logins = (
        db.session.query(func.count(LoginHistory.id))
        .filter(
            LoginHistory.timestamp >= thirty_days_ago, LoginHistory.success == False
        )
        .scalar()
    )

    successful_reports = (
        db.session.query(func.count(ProcessingHistory.id))
        .filter(
            ProcessingHistory.timestamp >= thirty_days_ago,
            ProcessingHistory.success == True,
        )
        .scalar()
    )
    failed_reports = (
        db.session.query(func.count(ProcessingHistory.id))
        .filter(
            ProcessingHistory.timestamp >= thirty_days_ago,
            ProcessingHistory.success == False,
        )
        .scalar()
    )

    processing_by_type = (
        db.session.query(
            ProcessingHistory.processing_type, func.count(ProcessingHistory.id)
        )
        .filter(ProcessingHistory.timestamp >= thirty_days_ago)
        .group_by(ProcessingHistory.processing_type)
        .all()
    )
    processing_types_data = {item[0]: item[1] for item in processing_by_type}

    logins_per_day = (
        db.session.query(func.date(LoginHistory.timestamp), func.count(LoginHistory.id))
        .filter(LoginHistory.timestamp >= thirty_days_ago)
        .group_by(func.date(LoginHistory.timestamp))
        .order_by(func.date(LoginHistory.timestamp))
        .all()
    )
    processing_per_day = (
        db.session.query(
            func.date(ProcessingHistory.timestamp), func.count(ProcessingHistory.id)
        )
        .filter(ProcessingHistory.timestamp >= thirty_days_ago)
        .group_by(func.date(ProcessingHistory.timestamp))
        .order_by(func.date(ProcessingHistory.timestamp))
        .all()
    )

    # Lógica de datas e gráficos substituída por chamadas aos helpers
    date_labels = date_utils.generate_date_labels(thirty_days_ago.date(), end_date)
    logins_chart_data = chart_data.fill_series_with_zeros(logins_per_day, date_labels)
    processing_chart_data = chart_data.fill_series_with_zeros(
        processing_per_day, date_labels
    )

    return {
        "total_users": total_users,
        "total_approved_users": total_approved_users,
        "total_pending_users": total_pending_users,
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "successful_reports": successful_reports,
        "failed_reports": failed_reports,
        "processing_types_data": processing_types_data,
        "date_labels": date_labels,
        "logins_chart_data": logins_chart_data,
        "processing_chart_data": processing_chart_data,
    }
