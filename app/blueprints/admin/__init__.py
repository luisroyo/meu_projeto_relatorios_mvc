# app/blueprints/admin/__init__.py
from flask import Blueprint

# Definição do Blueprint de Admin
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'  # Adicionar um prefixo é uma boa prática
)

# Importa as rotas dos novos arquivos para que o Flask as reconheça.
# Esta linha DEVE vir DEPOIS da definição do admin_bp.
from . import routes_dashboard, routes_user, routes_colaborador, routes_tools