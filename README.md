# 🛡️ Sistema de Gestão de Segurança Inteligente

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-xx%25-blue)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![AI Powered](https://img.shields.io/badge/AI-Gemini-orange.svg)](https://ai.google.dev)

## 📋 Descrição do Projeto

**Sistema de Gestão de Segurança Inteligente** é uma plataforma web completa e moderna para gerenciamento de operações de segurança em condomínios e ambientes corporativos. O sistema oferece controle total sobre rondas de patrulha, registro de ocorrências, gestão de colaboradores e análise inteligente de dados através de IA generativa.

### 🎯 Principais Benefícios

- **🤖 Análise Inteligente**: IA integrada para processamento automático de relatórios
- **📊 Dashboards Avançados**: Métricas em tempo real com KPIs personalizados
- **🔄 Sistema de Turnos**: Lógica inteligente para jornada 12x36
- **📱 Interface Responsiva**: Acesso completo via desktop e mobile
- **🔒 Segurança Robusta**: Autenticação multi-nível e proteção contra ataques
- **📈 Relatórios PDF**: Exportação profissional de dados e métricas

## 🖼️ Screenshots

<!-- Adicione aqui imagens/gifs do sistema rodando -->
<!-- Exemplo: -->
<!-- ![Dashboard](docs/screenshot_dashboard.png) -->

## 🛠️ Stack Tecnológica

### Backend
- **🐍 Python 3.8+** - Linguagem principal
- **🌶️ Flask 3.x** - Framework web com Blueprints e Padrão de Fábrica
- **🗄️ SQLAlchemy ORM** - Mapeamento objeto-relacional
- **🔄 Flask-Migrate** - Controle de versão do banco de dados
- **🔐 Flask-Login** - Sistema de autenticação
- **📝 Flask-WTF** - Formulários e validação
- **⚡ Flask-Limiter** - Rate limiting e segurança
- **💾 Flask-Caching** - Cache com suporte Redis/SimpleCache

### Banco de Dados
- **SQLite** (desenvolvimento) / **PostgreSQL** (produção)
- **Migrations** automáticas com Alembic

### IA e Processamento
- **🤖 Google Generative AI (Gemini)** - Análise inteligente de relatórios
- **📊 ReportLab** - Geração de relatórios PDF
- **⏰ pytz** - Manipulação de timezones e turnos

### Frontend
- **🎨 Bootstrap 5** - Framework CSS responsivo
- **📱 Design Mobile-First** - Interface otimizada para dispositivos móveis
- **⚡ JavaScript Vanilla** - Interatividade sem dependências externas

### DevOps e Qualidade
- **🧪 Pytest** - Framework de testes
- **📊 Coverage** - Análise de cobertura de código
- **🔧 Flask CLI** - Comandos personalizados
- **📝 Logging** - Sistema de logs estruturado

## 🚀 Instalação e Configuração

### 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Git** para clonagem do repositório
- **PostgreSQL** (opcional, para produção)

### ⚡ Instalação Rápida

```bash
# 1. Clonar o repositório
git clone https://github.com/luisroyo/meu_projeto_relatorios_mvc.git
cd meu_projeto_relatorios_mvc

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 6. Inicializar banco de dados
flask db upgrade
flask seed-db

# 7. Executar aplicação
flask run
```

### 🔧 Configuração Detalhada

#### Variáveis de Ambiente (.env)

```env
# Configurações básicas
SECRET_KEY=sua-chave-muito-secreta-aqui
DATABASE_URL=sqlite:///dev.db
FLASK_DEBUG=True
FLASK_ENV=development

# API Keys do Google Gemini (obrigatório)
GOOGLE_API_KEY_1=sua-chave-google-generative-ai-principal
GOOGLE_API_KEY_2=sua-chave-google-generative-ai-backup

# Redis (opcional - para cache em produção)
REDIS_URL=redis://usuario:senha@host:porta/0

# Configurações de produção
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

#### 🗄️ Configuração do Banco de Dados

**Desenvolvimento (SQLite):**
```env
DATABASE_URL=sqlite:///dev.db
```

**Produção (PostgreSQL):**
```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

#### 🤖 Configuração da IA

1. Obtenha uma API Key do [Google AI Studio](https://aistudio.google.com/)
2. Configure as chaves no arquivo `.env`
3. O sistema usa fallback automático entre múltiplas chaves

#### 💾 Cache (Opcional)

**Desenvolvimento:** SimpleCache (automático)
**Produção:** Redis (configure `REDIS_URL`)

### 🎯 Primeiro Acesso

Após executar `flask seed-db`, você terá:
- **Admin:** `admin@exemplo.com` / `admin123`
- **Supervisor:** `supervisor@exemplo.com` / `supervisor123`

**⚠️ Importante:** Altere essas credenciais em produção!

## 🎯 Funcionalidades Principais

### 👥 Sistema de Usuários e Permissões

| Papel | Permissões |
|-------|------------|
| **🔑 Administrador** | Acesso total ao sistema, gestão de usuários, configurações |
| **👨‍💼 Supervisor** | Gestão de rondas e ocorrências, relatórios, aprovação de eventos |
| **👤 Usuário Regular** | Registro de ocorrências, visualização de histórico pessoal |

### 🛡️ Módulos Principais

#### 🔍 **Gestão de Rondas**
- ✅ Registro de patrulhas com logs detalhados
- 📊 Análise de frequência e cobertura
- ⏰ Sistema inteligente de turnos (12x36)
- 📈 Métricas por supervisor e período
- 📄 Relatórios PDF automatizados

#### 🚨 **Gestão de Ocorrências**
- 📝 Registro detalhado de incidentes
- 🤖 Análise automática por IA (Gemini)
- 🏷️ Classificação inteligente por tipo e turno
- 🔗 Vinculação com órgãos públicos e colaboradores
- 📊 Dashboard de estatísticas em tempo real

#### 👥 **Gestão de Colaboradores**
- 📋 Cadastro completo de funcionários
- 🏢 Vinculação com condomínios
- 📊 Histórico de participação em eventos
- 🔄 Controle de escalas e plantões

#### 📊 **Dashboards Inteligentes**
- 📈 KPIs personalizados por supervisor
- 📅 Análise temporal com comparações
- 🎯 Métricas de eficiência operacional
- 📱 Interface responsiva para mobile

#### 🤖 **IA Generativa Integrada**
- ✍️ Processamento automático de relatórios
- 🔍 Extração inteligente de dados
- 📝 Formatação e correção de textos
- ⚡ Cache inteligente para otimização

### 🔒 Recursos de Segurança

- **🔐 Autenticação Multi-nível** com Flask-Login
- **🛡️ Proteção CSRF** em todos os formulários
- **⚡ Rate Limiting** contra ataques de força bruta
- **🔑 Hash Seguro** de senhas com Werkzeug
- **👤 Aprovação Manual** de novos usuários
- **📝 Logs de Auditoria** detalhados

## 🔌 API RESTful

O sistema oferece uma API RESTful completa para integração com aplicações web e mobile.

### 📡 Endpoints Principais

#### 🤖 Análise de Relatórios
```http
POST /api/ocorrencias/analisar-relatorio
Content-Type: application/json

{
  "texto_relatorio": "Relatório de ocorrência em texto livre..."
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "dados": {
    "tipo_ocorrencia": "Furto",
    "endereco": "Rua das Flores, 123",
    "data_hora": "2024-01-15 14:30:00",
    "descricao_processada": "Relatório formatado..."
  }
}
```

#### 📊 Dashboards e KPIs
```http
GET /api/dashboard/metricas?supervisor_id=1&periodo=30
GET /api/dashboard/kpis?condominio_id=1&data_inicio=2024-01-01
```

#### 🔍 Consultas de Dados
```http
GET /api/ocorrencias?page=1&per_page=20&status=Registrada
GET /api/rondas?supervisor_id=1&data_inicio=2024-01-01
GET /api/colaboradores?condominio_id=1
```

### 🔧 Configuração da API

- **CORS:** Habilitado para integração frontend
- **CSRF:** Desabilitado para APIs (usar tokens JWT)
- **Rate Limiting:** Configurado por endpoint
- **Autenticação:** JWT ou sessão Flask-Login

### 📚 Documentação Completa

Consulte a documentação detalhada da API:
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [API_FRONTEND_INTEGRATION_GUIDE.md](API_FRONTEND_INTEGRATION_GUIDE.md)

## ⚙️ Funcionalidades Avançadas

### 🔄 Sistema de Turnos Inteligente (12x36)

O sistema implementa lógica avançada para classificação automática de ocorrências baseada na jornada de trabalho:

#### 📅 Lógica de Classificação
- **🌅 Turnos Diurnos (6h-18h)**: Ocorrências atribuídas ao mesmo dia
- **🌙 Turnos Noturnos (18h-6h)**: 
  - **18h-23h59**: Ocorrências do mesmo dia
  - **00h-05h59**: Ocorrências do dia anterior (plantão iniciado no dia anterior)

#### 💡 Exemplo Prático
```
Supervisor inicia plantão: 31/08 às 18h
Ocorrência atendida: 01/09 às 03h
✅ Sistema atribui ao plantão de 31/08
```

### 📊 Métricas Inteligentes por Supervisor

#### 🎯 Cálculos Precisos
- **📈 Médias**: Baseadas apenas nos dias trabalhados (jornada 12x36)
- **📅 Comparações**: Períodos anteriores do mesmo supervisor
- **📄 Relatórios PDF**: Métricas precisas considerando dias trabalhados
- **📱 Dashboard**: Exibe "Dias Trabalhados" e "Cobertura Trabalhada"

#### 🔍 KPIs Disponíveis
- Taxa de ocorrências por dia trabalhado
- Eficiência de rondas por período
- Tempo médio de resposta
- Cobertura de área por supervisor

### 🛠️ Comandos CLI Avançados

```bash
# Testar lógica de turnos
flask test-shift-logic

# Verificar escala de supervisor
flask check-supervisor-escala

# Testar métricas de residenciais
flask test-residencial-metrics

# Testar comparação de períodos
flask test-period-comparison

# Testar exportação PDF
flask test-ronda-pdf-export

# Debug de cache Redis
python scripts/monitoring/test_redis.py

# Gerar dados de teste
flask seed-db --sample-data
```

## 🧪 Testes e Qualidade

### 🚀 Execução de Testes

```bash
# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_auth.py
pytest tests/services/
```

### 📊 Estrutura de Testes

```
tests/
├── conftest.py              # Configuração global
├── test_auth.py             # Testes de autenticação
├── test_forms.py            # Testes de formulários
├── test_main_routes.py      # Testes de rotas principais
├── test_ocorrencia_routes.py # Testes de ocorrências
├── test_ronda_routes.py     # Testes de rondas
└── services/                # Testes de serviços
    └── test_base_generative_service.py
```

### 🔧 Configuração de Testes

- **Banco de Dados**: SQLite em memória para isolamento
- **Cache**: SimpleCache para testes rápidos
- **CSRF**: Desabilitado em ambiente de teste
- **Configuração**: `pytest.ini` com caminhos Python corretos

### 📈 Monitoramento e Debug

```bash
# Testar conexão Redis
python scripts/monitoring/test_redis.py

# Testar cache simples
python scripts/monitoring/simple_cache_test.py

# Testar cache completo (integração)
python scripts/test_cache.py

# Gerar tráfego contínuo (manter Redis ativo)
python scripts/monitoring/generate_redis_traffic.py
```

### 📋 Cobertura de Código

```bash
# Instalar dependência de cobertura
pip install pytest-cov

# Executar com relatório HTML
pytest --cov=app --cov-report=html

# Visualizar relatório
open htmlcov/index.html
```

**📚 Para mais detalhes:** [scripts/README.md](scripts/README.md)

## 🔒 Segurança e Boas Práticas

### 🛡️ Medidas de Segurança Implementadas

#### 🔐 Autenticação e Autorização
- **🔑 Hash Seguro**: Senhas protegidas com Werkzeug
- **👤 Aprovação Manual**: Novos usuários requerem aprovação do admin
- **🔒 Decoradores Personalizados**: Proteção de rotas administrativas
- **⏰ Rate Limiting**: Proteção contra ataques de força bruta

#### 🛡️ Proteção de Dados
- **🔒 CSRF Protection**: Habilitada em todos os formulários
- **🍪 Cookies Seguros**: Configuração para produção
- **📝 Logs Seguros**: Evita exposição de dados sensíveis
- **🔐 Variáveis de Ambiente**: Segredos nunca commitados

#### 🌐 Segurança Web
- **🔒 HTTPS**: Configuração para produção
- **🛡️ Headers de Segurança**: Proteção contra ataques comuns
- **📊 Monitoramento**: Logs de auditoria detalhados

### 📋 Checklist de Produção

#### ⚙️ Configurações Obrigatórias
```env
# Produção
FLASK_ENV=production
SECRET_KEY=chave-super-secreta-256-bits
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

#### 🔧 Configurações Recomendadas
- **🗄️ PostgreSQL** para banco de dados
- **💾 Redis** para cache e sessões
- **🌐 HTTPS** com certificado SSL válido
- **📊 Monitoramento** de erros e performance
- **🔄 Backups** automáticos do banco de dados

### 🚀 Deploy e Manutenção

#### 📦 Deploy
- **☁️ Plataformas**: Render, Heroku, AWS, DigitalOcean
- **🐳 Docker**: Containerização disponível
- **🔄 CI/CD**: GitHub Actions configurado

#### 🔄 Manutenção
- **📊 Monitoramento**: Logs estruturados
- **🔄 Atualizações**: Dependências mantidas atualizadas
- **📈 Performance**: Cache Redis para otimização
- **🧪 Testes**: Cobertura de código alta

## 🤝 Contribuição

### 📝 Como Contribuir

1. **🍴 Fork** o repositório
2. **🌿 Crie** uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. **💾 Commit** suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. **📤 Push** para a branch (`git push origin feature/nova-feature`)
5. **🔄 Abra** um Pull Request

### 📋 Padrões de Código

- **🐍 PEP 8**: Padrão Python
- **🧪 Testes**: Cobertura mínima de 80%
- **📝 Documentação**: Docstrings em português
- **🔍 Linting**: Black, Flake8 configurados

### 🐛 Reportar Bugs

Use o sistema de [Issues](https://github.com/luisroyo/meu_projeto_relatorios_mvc/issues) do GitHub com:
- Descrição detalhada do problema
- Passos para reproduzir
- Screenshots (se aplicável)
- Informações do ambiente

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## 📞 Suporte e Contato

- **📧 Email**: [luisroyo25@gmail.com](mailto:luisroyo25@gmail.com)
- **🐛 Issues**: [GitHub Issues](https://github.com/luisroyo/meu_projeto_relatorios_mvc/issues)
- **📚 Documentação**: Consulte os arquivos `.md` na raiz do projeto

---

<div align="center">

**🛡️ Sistema de Gestão de Segurança Inteligente**

*Desenvolvido com ❤️ para segurança e eficiência operacional*

[![GitHub stars](https://img.shields.io/github/stars/luisroyo/meu_projeto_relatorios_mvc?style=social)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/luisroyo/meu_projeto_relatorios_mvc?style=social)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/network)

</div>
