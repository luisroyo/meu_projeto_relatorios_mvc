# Scripts Utilitários

Este diretório contém scripts utilitários para desenvolvimento, teste e monitoramento do projeto.

## 📁 Estrutura

```
scripts/
├── README.md                    # Esta documentação
├── __init__.py                  # Pacote Python
├── test_cache.py               # Teste completo do cache (integração)
└── monitoring/                 # Scripts de monitoramento
    ├── __init__.py             # Pacote Python
    ├── test_redis.py           # Teste básico de conexão Redis
    ├── simple_cache_test.py    # Teste simples de cache
    └── generate_redis_traffic.py # Gerador de tráfego contínuo
```

## 🧪 Scripts de Teste

### `test_cache.py`
**Localização**: `scripts/test_cache.py`
**Propósito**: Teste completo de integração do cache
**Uso**: `python scripts/test_cache.py`
**Descrição**: Testa o cache com a aplicação Flask completa, incluindo o serviço de IA.

## 📊 Scripts de Monitoramento

### `test_redis.py`
**Localização**: `scripts/monitoring/test_redis.py`
**Propósito**: Teste básico de conexão com Redis
**Uso**: `python scripts/monitoring/test_redis.py`
**Descrição**: Verifica se o Redis está configurado e funcionando.

### `simple_cache_test.py`
**Localização**: `scripts/monitoring/simple_cache_test.py`
**Propósito**: Teste simples de cache sem carregar a aplicação
**Uso**: `python scripts/monitoring/simple_cache_test.py`
**Descrição**: Testa operações básicas do Redis e simula o padrão de cache da aplicação.

### `generate_redis_traffic.py`
**Localização**: `scripts/monitoring/generate_redis_traffic.py`
**Propósito**: Gerar tráfego contínuo no Redis
**Uso**: `python scripts/monitoring/generate_redis_traffic.py`
**Descrição**: Mantém o Redis ativo gerando operações contínuas (útil para evitar inatividade).

## 🚀 Como Usar

### Desenvolvimento Local
```bash
# Testar conexão Redis
python scripts/monitoring/test_redis.py

# Testar cache simples
python scripts/monitoring/simple_cache_test.py

# Testar cache completo
python scripts/test_cache.py
```

### Monitoramento Contínuo
```bash
# Gerar tráfego para manter Redis ativo
python scripts/monitoring/generate_redis_traffic.py
```

### Verificação Rápida
```bash
# Verificar se tudo está funcionando
python scripts/monitoring/test_redis.py && python scripts/monitoring/simple_cache_test.py
```

## 💡 Dicas

1. **Para desenvolvimento**: Use `simple_cache_test.py` para testes rápidos
2. **Para integração**: Use `test_cache.py` para testes completos
3. **Para monitoramento**: Use `generate_redis_traffic.py` para manter Redis ativo
4. **Para debug**: Use `test_redis.py` para verificar configuração

## 🔧 Configuração

Todos os scripts usam as mesmas variáveis de ambiente:
- `REDIS_URL` ou `CACHE_REDIS_URL` para conexão Redis
- `GOOGLE_API_KEY_1` e `GOOGLE_API_KEY_2` para API Gemini

Certifique-se de que o arquivo `.env` está configurado corretamente. 