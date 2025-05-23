# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user # Adicionado current_user se for usar para logs
from app import db
from app.models import User
import os
import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__) # Define um logger para este módulo

@main_bp.route('/')
@login_required
def index():
    # Adicionando log similar ao que estava no seu routesOld.py
    logger.debug(
        f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} "
        f"({current_user.username if current_user.is_authenticated else 'N/A'}). "
        f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
    )
    return render_template('index.html', title='Analisador de Relatórios IA')

#