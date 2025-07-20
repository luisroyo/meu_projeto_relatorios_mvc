# config.py
import os

class Config:
    """Configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-dificil-de-adivinhar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    
    # Configuração do Redis - suporta tanto REDIS_URL quanto CACHE_REDIS_URL
    REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        # Fallback para SimpleCache se Redis não estiver disponível
        CACHE_TYPE = "SimpleCache"

class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'
    # Em desenvolvimento, sempre usa SimpleCache para simplicidade
    CACHE_TYPE = 'SimpleCache'

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

class ProductionConfig(Config):
    """Configuração de produção. Use sempre variáveis de ambiente para segredos!"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Não use fallback em produção
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    # Adicione outras configs de segurança conforme necessário

# AVISO IMPORTANTE:
# Nunca use o fallback do SECRET_KEY em produção!
# Sempre defina SECRET_KEY e outras variáveis sensíveis via ambiente.
# Exemplo de uso seguro:
#   export SECRET_KEY='sua-chave-super-secreta'
#   export DATABASE_URL='postgresql://usuario:senha@host:porta/banco'
#   export REDIS_URL='redis://usuario:senha@host:porta/0'  # Para Redis
#
# Para rodar em produção, use:
#   app = create_app(ProductionConfig)
#
# Para desenvolvimento, continue usando DevelopmentConfig.