from app import create_app # Importa a factory create_app
import os

# Cria a instância da aplicação chamando a factory
app = create_app()

if __name__ == '__main__':
    # Define a porta. Render usa a variável PORT. Localmente, pode ser 5000.
    port = int(os.environ.get("PORT", 5000))
    # debug=True é bom para desenvolvimento. Render controlará isso ou usará Gunicorn.
    # Em produção via Gunicorn, o debug=True do Flask não é usado.
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    if debug_mode and os.getenv("FLASK_ENV", "development") != "development":
        print("[AVISO] O modo debug está ativado fora do ambiente de desenvolvimento! Nunca use debug=True em produção.")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)