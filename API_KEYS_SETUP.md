# Configuração das API Keys Gemini

## 📋 Variáveis de Ambiente Necessárias

### Para Desenvolvimento Local (.env)
```env
# API Keys para fallback automático
GOOGLE_API_KEY_1=AIzaSyA...SuaKeyPrincipal
GOOGLE_API_KEY_2=AIzaSyB...KeyDeBackup

# Outras configurações
FLASK_ENV=development
FLASK_DEBUG=True
```

### Para Produção (Render)
Configure no painel do Render as seguintes variáveis:
- `GOOGLE_API_KEY_1` = Sua API Key principal
- `GOOGLE_API_KEY_2` = API Key de backup/colega

## 🔄 Como Funciona o Fallback

1. **Primeira tentativa**: Usa `GOOGLE_API_KEY_1`
2. **Se falhar** (quota excedida, erro 429, etc): Tenta `GOOGLE_API_KEY_2`
3. **Se ambas falharem**: Mostra erro detalhado

## 📝 Logs Esperados

### Sucesso com primeira API:
```
Usando GOOGLE_API_KEY_1 para chamada Gemini.
```

### Fallback para segunda API:
```
Erro ao tentar GOOGLE_API_KEY_1: 429 You exceeded your current quota
Usando GOOGLE_API_KEY_2 para chamada Gemini.
```

### Todas falharam:
```
Todas as APIs Gemini falharam. Último erro: 429 You exceeded your current quota
```

## 🚀 Como Configurar

### 1. Desenvolvimento Local
1. Crie arquivo `.env` na raiz do projeto
2. Adicione suas API Keys
3. Reinicie a aplicação

### 2. Produção (Render)
1. Acesse o painel do Render
2. Vá em Environment
3. Adicione as variáveis `GOOGLE_API_KEY_1` e `GOOGLE_API_KEY_2`
4. O deploy será automático

## ⚠️ Importante
- Nunca comite o arquivo `.env` (já está no .gitignore)
- Use API Keys diferentes para ter mais cota
- O sistema funciona automaticamente sem intervenção manual 