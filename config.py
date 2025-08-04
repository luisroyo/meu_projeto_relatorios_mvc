# config.py
import os
from datetime import timedelta


class Config:
    """Configuração base."""

    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "uma-chave-secreta-dificil-de-adivinhar"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    # Expiração de sessão por inatividade (15 minutos)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_PERMANENT = True

    # Configuração do Redis - suporta tanto REDIS_URL quanto CACHE_REDIS_URL
    REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        # Fallback para SimpleCache se Redis não estiver disponível
        CACHE_TYPE = "SimpleCache"

    # Configurações de pool de conexões para PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # Número de conexões no pool
        'pool_timeout': 20,  # Timeout para obter conexão do pool
        'pool_recycle': 3600,  # Reciclar conexões a cada 1 hora
        'pool_pre_ping': True,  # Verificar conexão antes de usar
        'max_overflow': 20,  # Máximo de conexões extras
    }


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""

    DEBUG = True

    # Configuração do banco de dados com suporte a SSL para PostgreSQL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Fallback para PostgreSQL em desenvolvimento se DATABASE_URL não estiver definida
        database_url = "postgresql://postgres:edu123cs@localhost:5432/swiss_db"

    # Garante que a URL use postgresql:// ao invés de postgres:// (para PostgreSQL)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url


class LocalConfig(Config):
    """Configuração para desenvolvimento local com PostgreSQL."""

    DEBUG = True

    # Configuração do banco de dados local (PostgreSQL via Docker)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # URL padrão para PostgreSQL local
        database_url = "postgresql://postgres:postgres123@localhost:5432/relatorios_dev"

    # Garante que a URL use postgresql:// ao invés de postgres:// (para PostgreSQL)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url

    # Configuração do cache local
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 3600

    # Configuração do cache - usa Redis se disponível, senão SimpleCache
    REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
        CACHE_DEFAULT_TIMEOUT = 3600  # 1 hora
    else:
        # Fallback para SimpleCache se Redis não estiver disponível
        CACHE_TYPE = "SimpleCache"
        CACHE_DEFAULT_TIMEOUT = 3600  # 1 hora


class TestingConfig(Config):
    """Configuração de teste."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    # CORREÇÃO: Mude de 'NullCache' para 'SimpleCache'
    # SimpleCache funciona em memória e é perfeito para testes.
    CACHE_TYPE = "SimpleCache"

    RATELIMIT_ENABLED = False
    # Adicione SERVER_NAME para que url_for funcione fora de um request
    SERVER_NAME = "localhost.local"


class ProductionConfig(Config):
    """Configuração de produção. Use sempre variáveis de ambiente para segredos!"""

    DEBUG = False

    # Configuração do banco de dados com suporte a SSL para PostgreSQL.
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL deve ser definida em produção!")
    
    # Garante que a URL use postgresql:// ao invés de postgres:// (para PostgreSQL)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Adiciona parâmetros SSL para PostgreSQL no Render
    if "render.com" in database_url or "onrender.com" in database_url:
        # Configurações específicas para Render
        if "?" not in database_url:
            database_url += "?sslmode=require"
        else:
            database_url += "&sslmode=require"
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Configurações de pool mais conservadoras para produção
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,  # Menos conexões para economizar recursos
        'pool_timeout': 30,  # Timeout maior para produção
        'pool_recycle': 1800,  # Reciclar a cada 30 minutos
        'pool_pre_ping': True,  # Verificar conexão antes de usar
        'max_overflow': 10,  # Menos overflow para produção
        'connect_args': {
            'connect_timeout': 10,  # Timeout de conexão
            'application_name': 'gestao_seguranca_app',  # Nome da aplicação
        }
    }
    
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
