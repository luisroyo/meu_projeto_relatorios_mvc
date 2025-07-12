# config.py
import os

class Config:
    """Configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-dificil-de-adivinhar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'

class TestingConfig(Config):
    """Configuração de teste."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # CORREÇÃO: Mude de 'NullCache' para 'SimpleCache'
    # SimpleCache funciona em memória e é perfeito para testes.
    CACHE_TYPE = 'SimpleCache'
    
    RATELIMIT_ENABLED = False
    # Adicione SERVER_NAME para que url_for funcione fora de um request
    SERVER_NAME = 'localhost.local'