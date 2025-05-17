from flask import render_template
from app import app # Importa a instância 'app' de app/__init__.py

@app.route('/')
def index():
    # Por enquanto, vamos apenas renderizar um template simples.
    # Mais tarde, este template será nossa interface principal.
    return render_template('index.html', title='Página Inicial')