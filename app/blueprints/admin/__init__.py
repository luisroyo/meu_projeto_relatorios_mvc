# app/blueprints/admin/__init__.py

from flask import Blueprint

# 1. O Blueprint é criado aqui, de forma isolada.
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates'
)

# 2. As rotas são importadas DEPOIS, o que as anexa ao blueprint.
from . import routes