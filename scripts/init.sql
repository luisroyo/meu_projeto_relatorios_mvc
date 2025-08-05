-- Script de inicialização do PostgreSQL local
-- Este arquivo é executado automaticamente quando o container é criado

-- Criar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Log de inicialização
SELECT 'PostgreSQL local inicializado com sucesso!' as status; 