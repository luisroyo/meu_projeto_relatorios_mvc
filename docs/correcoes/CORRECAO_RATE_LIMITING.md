# Correção de Rate Limiting - Erro 429

## Problema Identificado

O sistema estava apresentando erro 429 (Too Many Requests) devido a múltiplas requisições automáticas geradas pelo frontend durante a busca de colaboradores em tempo real.

### Causa Raiz

1. **Busca sem debounce**: Cada caractere digitado no campo de busca disparava uma nova requisição para a API
2. **Redirecionamentos em cascata**: Usuários não logados eram redirecionados para `/login`, multiplicando o número de requisições
3. **Rate limiting muito restritivo**: O endpoint de login tinha limite de apenas 10 requisições por minuto

## Soluções Implementadas

### 1. Frontend - Debounce na Busca

**Arquivo**: `frontend/static/js/admin_justificativas.js`

- Adicionado sistema de debounce com delay de 300ms
- Evita múltiplas requisições durante a digitação
- Só faz a busca após o usuário parar de digitar

```javascript
// Variáveis para controle de debounce
let searchTimeout = null;
const SEARCH_DELAY = 300; // 300ms de delay entre buscas

// Limpar timeout anterior se existir
if (searchTimeout) {
    clearTimeout(searchTimeout);
}

// Configurar novo timeout para debounce
searchTimeout = setTimeout(async () => {
    // Lógica de busca aqui
}, SEARCH_DELAY);
```

### 2. Backend - Rate Limiting nas Rotas de Busca

**Arquivo**: `backend/app/blueprints/admin/routes_colaborador.py`
- Adicionado `@limiter.limit("30 per minute")` na rota `/api/colaboradores/search`

**Arquivo**: `backend/app/blueprints/api/admin_routes.py`
- Adicionado `@limiter.limit("30 per minute")` na rota `/colaboradores/search`

### 3. Configuração de Rate Limiting

- **Login**: 10 requisições por minuto (mantido)
- **Busca de colaboradores**: 30 requisições por minuto (novo)
- **Rotas principais**: 200 requisições por hora (mantido)

## Benefícios da Correção

1. **Redução de requisições**: O debounce elimina requisições desnecessárias
2. **Melhor experiência do usuário**: Busca mais responsiva e sem erros 429
3. **Proteção contra abuso**: Rate limiting adequado para cada tipo de operação
4. **Performance**: Menos carga no servidor e banco de dados

## Como Testar

1. Acesse a página de gerador de justificativas
2. Digite rapidamente no campo de busca de colaboradores
3. Verifique que não há múltiplas requisições simultâneas
4. Confirme que a busca funciona normalmente após parar de digitar

## Monitoramento

Os logs agora devem mostrar:
- Menos requisições para `/admin/api/colaboradores/search`
- Redução significativa de redirecionamentos para `/login`
- Ausência de erros 429 durante o uso normal

## Próximos Passos

1. Monitorar os logs para confirmar a redução de requisições
2. Considerar implementar debounce em outros campos de busca do sistema
3. Avaliar se outros endpoints precisam de ajustes no rate limiting
