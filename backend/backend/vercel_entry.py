#!/usr/bin/env python3
"""
Entry point específico para o Vercel.
Este arquivo substitui o entrypoint.sh para funcionar no Vercel.
"""

import os
import sys
import logging
from pathlib import Path

# Adiciona o diretório backend ao Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Inicializa a aplicação Flask para o Vercel."""
    try:
        logger.info("=== INICIANDO APLICAÇÃO NO VERCEL ===")
        
        # Configura variáveis de ambiente se necessário
        os.environ.setdefault('FLASK_ENV', 'production')
        
        # Importa e inicializa a aplicação
        from app import create_app
        
        # Cria a aplicação
        app = create_app()
        
        logger.info("Aplicação Flask inicializada com sucesso no Vercel")
        return app
        
    except Exception as e:
        logger.error(f"Erro ao inicializar aplicação no Vercel: {e}")
        raise

# Para o Vercel, exporta a aplicação
app = main()

# Para desenvolvimento local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
