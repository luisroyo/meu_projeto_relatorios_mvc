from flask import Flask
import os
from dotenv import load_dotenv
import logging # Adicionado

# Define o caminho para o arquivo .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24)) 

# Configuração básica de logging
# Em produção, você pode querer configurar isso para um arquivo ou serviço de logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Garante que o logger do Flask use o nível configurado e o mesmo handler
app.logger.handlers = logging.getLogger().handlers
app.logger.setLevel(logging.INFO)

app.logger.info("Aplicação Flask inicializada e logging configurado.")

# Importa as rotas (controllers) DEPOIS de criar a instância 'app'
# e DEPOIS de configurar o logging para que as rotas também possam logar.
from app import routes