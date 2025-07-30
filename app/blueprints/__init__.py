from .admin.routes_dashboard import admin_bp
from .admin.routes_user import admin_bp as admin_user_bp
from .admin.routes_tools import admin_bp as admin_tools_bp
from .admin.routes_colaborador import admin_bp as admin_colaborador_bp
from .admin.routes_gemini_dashboard import gemini_dashboard_bp
from .ocorrencia.routes import ocorrencia_bp
from .ronda.routes import ronda_bp
from .auth.routes import auth_bp
from .api import api_bp
from .main.routes import main_bp

def register_blueprints(app):
    app.register_blueprint(admin_bp)
    # Os blueprints admin_* usam o mesmo admin_bp, rotas já estão agrupadas
    app.register_blueprint(gemini_dashboard_bp)
    app.register_blueprint(ocorrencia_bp)
    app.register_blueprint(ronda_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
