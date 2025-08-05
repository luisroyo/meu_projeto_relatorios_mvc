from app import create_app
import os
from config import DevelopmentConfig, ProductionConfig

# Seleciona a configuração com base em FLASK_ENV
# O padrão é 'development' se a variável não estiver definida
config_name = os.getenv('FLASK_ENV', 'development')

if config_name == 'production':
    app = create_app(ProductionConfig)
else:
    app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    if debug_mode and os.getenv("FLASK_ENV", "development") != "development":
        print(
            "[AVISO] O modo debug está ativado fora do ambiente de desenvolvimento! Nunca use debug=True em produção."
        )
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
