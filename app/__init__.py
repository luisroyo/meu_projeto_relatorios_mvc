from flask import Flask
import os
from dotenv import load_dotenv

# Define o caminho para o arquivo .env na raiz do projeto
# O primeiro os.path.dirname(__file__) refere-se à pasta 'app'
# O segundo os.path.dirname() sobe um nível para a raiz do projeto
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
# Você pode adicionar uma SECRET_KEY para sessões, etc., se necessário no futuro
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))

# Importa as rotas (controllers) DEPOIS de criar a instância 'app'
# para evitar importação circular.
from app import routes