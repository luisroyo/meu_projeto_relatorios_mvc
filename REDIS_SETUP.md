# Configuração do Redis

## 📋 Visão Geral

O sistema usa cache para otimizar as respostas da API Gemini, evitando chamadas desnecessárias para a mesma consulta. O cache pode ser configurado de duas formas:

1. **SimpleCache** (padrão): Cache em memória local
2. **RedisCache**: Cache distribuído usando Redis

## 🔧 Configuração

### Desenvolvimento Local

Para desenvolvimento local, o **SimpleCache** é usado automaticamente e não requer configuração adicional.

### Produção (Render/Heroku)

Para usar Redis em produção:

1. **Configure uma das variáveis de ambiente:**
   ```env
   # Opção 1 (padrão)
   REDIS_URL=redis://usuario:senha@host:porta/0
   
   # Opção 2 (alternativa)
   CACHE_REDIS_URL=redis://usuario:senha@host:porta/0
   ```

2. **No Render:**
   - Vá para as configurações do seu serviço
   - Adicione a variável `REDIS_URL` ou `CACHE_REDIS_URL` com a URL do seu Redis
   - Exemplo: `rediss://default:senha@host.upstash.io:porta/0`
   - **Nota**: O sistema detecta automaticamente qual variável está configurada

3. **Teste a conexão:**
   ```bash
   python test_redis.py
   ```

## 🚀 Como Funciona

### Detecção Automática

O sistema detecta automaticamente se o Redis está disponível:

```python
# Suporta tanto REDIS_URL quanto CACHE_REDIS_URL
REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
if REDIS_URL:
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
else:
    # Fallback para SimpleCache
    CACHE_TYPE = "SimpleCache"
```

### Uso no Código

O cache é usado principalmente no serviço de IA:

```python
@cache.memoize()
def _call_generative_model(self, prompt_final: str) -> str:
    # Esta função é cacheada automaticamente
    # Respostas idênticas são retornadas do cache
```

## 📊 Benefícios do Redis

### Com Redis:
- ✅ Cache persistente entre reinicializações
- ✅ Cache compartilhado entre múltiplas instâncias
- ✅ Melhor performance em produção
- ✅ Economia de chamadas para API Gemini

### Sem Redis (SimpleCache):
- ✅ Simples de configurar
- ✅ Funciona imediatamente
- ❌ Cache perdido ao reiniciar
- ❌ Não compartilhado entre instâncias

## 🔍 Solução de Problemas

### Redis Inativo no Upstash

Se você receber aviso de Redis inativo:

1. **Verifique se está configurado:**
   ```bash
   python test_redis.py
   ```

2. **Configure no Render:**
   - Adicione `REDIS_URL` nas variáveis de ambiente
   - Reinicie a aplicação

3. **Teste o uso:**
   - Faça algumas consultas na aplicação
   - O Redis será usado automaticamente

### Erros de Conexão

Se houver erros de conexão:

1. **Verifique a URL do Redis**
2. **Teste com o script:**
   ```bash
   python test_redis.py
   ```
3. **Verifique logs da aplicação**

## 💡 Dicas

- **Desenvolvimento**: Use SimpleCache (padrão)
- **Produção**: Configure Redis para melhor performance
- **Teste**: Sempre teste com `python test_redis.py`
- **Logs**: Monitore os logs para ver se o cache está funcionando

## 🔄 Migração

### De SimpleCache para Redis

1. Configure `REDIS_URL` nas variáveis de ambiente
2. Reinicie a aplicação
3. O sistema automaticamente migra para Redis

### De Redis para SimpleCache

1. Remova `REDIS_URL` das variáveis de ambiente
2. Reinicie a aplicação
3. O sistema automaticamente volta para SimpleCache 