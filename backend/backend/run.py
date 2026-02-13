from app import create_app
import os
import sys
from config import DevelopmentConfig, ProductionConfig

# Garantir que o diretório backend esteja no PYTHONPATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Força uso da DevelopmentConfig para teste local
app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    if debug_mode and os.getenv("FLASK_ENV", "development") != "development":
        print(
            "[AVISO] O modo debug está ativado fora do ambiente de desenvolvimento! Nunca use debug=True em produção."
        )
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
