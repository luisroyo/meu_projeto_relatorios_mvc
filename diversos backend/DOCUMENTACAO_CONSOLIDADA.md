# 📚 Documentação Consolidada - Sistema de Relatórios MVC

## 🎯 Visão Geral do Projeto

Sistema completo de gerenciamento de relatórios, ocorrências e rondas com arquitetura MVC, API REST e interface web moderna.

### **Tecnologias Principais:**
- **Backend**: Flask (Python)
- **Frontend**: HTML/CSS/JavaScript
- **Banco**: PostgreSQL/SQLite
- **Cache**: Redis
- **Deploy**: Render.com

---

## 🚀 Como Executar o Backend

### **1. Configuração Local**
```bash
# Clonar repositório
git clone <url-do-repositorio>
cd meu_projeto_relatorios_mvc

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar migrações
flask db upgrade

# Iniciar servidor
python run.py
```

### **2. Scripts de Inicialização**
- `start_backend.bat` - Windows
- `start_backend.ps1` - PowerShell
- `entrypoint.sh` - Linux/Mac

---

## 🔧 Configuração CORS (Corrigido)

### **Problema Original:**
```
Requisição cross-origin bloqueada: A diretiva Same Origin (mesma origem) não permite a leitura do recurso remoto em https://processador-relatorios-ia.onrender.com/api/login
```

### **Causa Raiz:**
- Erro 500 durante requisições OPTIONS (preflight CORS)
- `AttributeError: 'Request' object has no attribute '__name__'` no CSRF

### **Solução Implementada:**
```python
# app/__init__.py
# CORS configurado corretamente
allowed_origins = [
    "http://localhost:5173", "http://localhost:5174",
    "https://processador-relatorios-ia.onrender.com",
    "https://ocorrencias-master-app.onrender.com"
]

# Handler OPTIONS simplificado
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_api_options(path):
    return '', 204
```

### **Status:** ✅ **CORRIGIDO E FUNCIONANDO**

---

## 📊 API Documentation

### **Endpoints Principais:**

#### **Autenticação:**
- `POST /api/login` - Login de usuário
- `POST /api/logout` - Logout de usuário

#### **Ocorrências:**
- `GET /api/ocorrencias` - Listar ocorrências
- `POST /api/ocorrencias` - Criar ocorrência
- `GET /api/ocorrencias/<id>` - Detalhes da ocorrência
- `PUT /api/ocorrencias/<id>` - Atualizar ocorrência

#### **Rondas:**
- `GET /api/rondas` - Listar rondas
- `POST /api/rondas` - Criar ronda
- `GET /api/rondas/<id>` - Detalhes da ronda
- `POST /api/rondas/upload` - Upload de arquivo de ronda

#### **Dashboard:**
- `GET /api/dashboard` - Dados do dashboard
- `GET /api/dashboard/comparativo` - Dashboard comparativo

### **Autenticação:**
- JWT Token no header: `Authorization: Bearer <token>`
- CORS configurado para origens permitidas

---

## 🏗️ Arquitetura do Sistema

### **Estrutura MVC:**
```
app/
├── blueprints/          # Rotas organizadas por módulo
│   ├── auth/           # Autenticação
│   ├── api/            # API REST
│   ├── admin/          # Painel administrativo
│   └── main/           # Rotas principais
├── models/             # Modelos de dados
├── services/           # Lógica de negócio
├── forms/              # Formulários
├── templates/          # Templates HTML
└── static/             # Arquivos estáticos
```

### **Serviços Principais:**
- **Dashboard Service**: Geração de relatórios e métricas
- **Ronda Service**: Processamento de arquivos de ronda
- **Ocorrência Service**: Gerenciamento de ocorrências
- **Email Service**: Formatação e envio de emails

---

## 🔍 Monitoramento e Debug

### **Scripts Disponíveis:**
- `scripts/monitor_db_connection.py` - Monitora conexão com banco
- `scripts/monitor_api_usage.py` - Monitora uso da API
- `scripts/manage_local_db.py` - Gerenciamento de banco local

### **Logs:**
- Localização: `logs/assistente_ia_seg.log`
- Rotação automática de arquivos
- Níveis: DEBUG, INFO, WARNING, ERROR

---

## 🚨 Solução de Problemas

### **Erro SSL:**
```
SSL connection has been closed
```
**Solução**: Reconexão automática implementada no código.

### **Erro CORS:**
```
Requisição cross-origin bloqueada
```
**Solução**: Configuração CORS corrigida em `app/__init__.py`.

### **Erro de Banco:**
```
OperationalError: connection to server at
```
**Solução**: Pool de conexões e reconexão automática.

---

## 📈 Deploy e Produção

### **Render.com:**
- **Backend**: `https://processador-relatorios-ia.onrender.com`
- **Frontend**: `https://ocorrencias-master-app.onrender.com`
- **Deploy automático** via Git

### **Variáveis de Ambiente:**
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
```

---

## 🧪 Testes

### **Executar Testes:**
```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_auth.py
pytest tests/test_api.py

# Com cobertura
pytest --cov=app
```

### **Estrutura de Testes:**
```
tests/
├── conftest.py          # Configuração de testes
├── test_auth.py         # Testes de autenticação
├── test_api.py          # Testes da API
└── services/            # Testes de serviços
```

---

## 🔧 Configurações de Desenvolvimento

### **VS Code/Cursor:**
- Configurações em `.vscode/settings.json`
- Python 3.13 como interpretador
- Ambiente virtual ativado automaticamente
- Formatação com Black
- Linting com Pylint e Flake8

### **Git:**
- `.gitignore` configurado para Python/Flask
- Commits organizados com emojis
- Branch principal: `main`

---

## 📝 Changelog

### **Versão Atual:**
- ✅ CORS corrigido e funcionando
- ✅ API REST completa
- ✅ Dashboard com métricas
- ✅ Sistema de autenticação JWT
- ✅ Upload e processamento de rondas
- ✅ Relatórios em PDF
- ✅ Cache Redis implementado

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs em `logs/`
2. Consultar documentação da API
3. Executar scripts de monitoramento
4. Verificar configurações de ambiente

---

*Última atualização: $(date)*
