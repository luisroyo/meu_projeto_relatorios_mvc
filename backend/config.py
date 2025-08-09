# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

# Carrega as variáveis do arquivo .env
load_dotenv()


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

    # Controle de recursos/DB
    USER_ACTIVITY_ENABLED = os.environ.get("USER_ACTIVITY_ENABLED", "false").lower() == "true"
    DB_CLOSE_ON_TEARDOWN = os.environ.get("DB_CLOSE_ON_TEARDOWN", "true").lower() == "true"
    SQLALCHEMY_USE_NULLPOOL = os.environ.get("SQLALCHEMY_USE_NULLPOOL", "false").lower() == "true"

    # Fuso horário padrão da aplicação
    DEFAULT_TIMEZONE = os.environ.get("DEFAULT_TIMEZONE", "America/Sao_Paulo")

    # Timeout de inatividade (minutos) para logout forçado
    INACTIVITY_TIMEOUT_MIN = int(os.environ.get("INACTIVITY_TIMEOUT_MIN", "5"))

    # Configuração do Redis - suporta tanto REDIS_URL quanto CACHE_REDIS_URL
    REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        # Fallback para SimpleCache se Redis não estiver disponível
        CACHE_TYPE = "SimpleCache"

    # Configurações padrão de pool para ambientes não-serverless
    if os.environ.get("SQLALCHEMY_USE_NULLPOOL", "false").lower() == "true":
        SQLALCHEMY_ENGINE_OPTIONS = {
            'poolclass': NullPool,
            'pool_pre_ping': True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_timeout': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 20,
        }


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""

    DEBUG = True

    # Usa a DATABASE_URL do arquivo .env
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        # Garante que a URL use postgresql:// ao invés de postgres://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Para desenvolvimento, não força SSL se for localhost
        if "localhost" in database_url or "127.0.0.1" in database_url:
            # Desenvolvimento local - não força SSL
            SQLALCHEMY_DATABASE_URI = database_url
        else:
            # Desenvolvimento remoto - adiciona SSL se necessário
            if "sslmode=require" not in database_url:
                if "?" not in database_url:
                    SQLALCHEMY_DATABASE_URI = database_url + "?sslmode=require"
                else:
                    SQLALCHEMY_DATABASE_URI = database_url + "&sslmode=require"
            else:
                SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback para SQLite se não encontrar DATABASE_URL
        SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'


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
    
    # Configurações específicas para Neon
    if "neon.tech" in database_url:
        # Configurações otimizadas para Neon (auto-suspension)
        if "?" not in database_url:
            database_url += "?sslmode=require"
        else:
            database_url += "&sslmode=require"
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Configurações de pool otimizadas para produção (honra SQLALCHEMY_USE_NULLPOOL)
    if os.environ.get("SQLALCHEMY_USE_NULLPOOL", "false").lower() == "true":
        SQLALCHEMY_ENGINE_OPTIONS = {
            'poolclass': NullPool,
            'pool_pre_ping': True,
            'connect_args': {
                'connect_timeout': 15,
                'application_name': 'gestao_seguranca_app_nullpool',
            }
        }
    elif "neon.tech" in database_url:
        # Configurações específicas para Neon (reduz conexões para facilitar auto-suspensão)
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 3,
            'pool_timeout': 45,
            'pool_recycle': 900,
            'pool_pre_ping': True,
            'max_overflow': 5,
            'connect_args': {
                'connect_timeout': 15,
                'application_name': 'gestao_seguranca_app_neon',
            }
        }
    else:
        # Configurações padrão para produção
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 5,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
            'max_overflow': 10,
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'gestao_seguranca_app',
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
