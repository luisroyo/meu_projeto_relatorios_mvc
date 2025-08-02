from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import ocorrencia_routes, ronda_routes, ronda_esporadica_routes, ronda_esporadica_consolidacao_routes, ronda_tempo_real_routes 