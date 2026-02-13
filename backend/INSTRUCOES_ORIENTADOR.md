# 📋 Instruções para o Orientador - Sistemas Inteligentes e Automação: Aplicação Web para Gestão Automatizada de Segurança com Inteligência Artificial

## 🎯 Visão Geral do Projeto

Este é um **Sistema de Gestão Automatizada de Segurança com Inteligência Artificial** desenvolvido como Trabalho de Conclusão de Curso (TCC). A aplicação oferece uma solução completa para gerenciamento automatizado de rondas, ocorrências e relatórios de segurança com integração avançada de **Inteligência Artificial**.

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.8 ou superior instalado
- Git (opcional, para clonagem)

### Passos para Execução

1. **Navegue até o diretório do projeto:**
   ```bash
   cd backend
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - **Windows:** `venv\Scripts\activate`
   - **Linux/Mac:** `source venv/bin/activate`

4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure as variáveis de ambiente:**
   Crie um arquivo `.env` na raiz do projeto com:
   ```env
   SECRET_KEY=chave-secreta-para-desenvolvimento
   DATABASE_URL=sqlite:///app.db
   FLASK_DEBUG=True
   GOOGLE_API_KEY=sua-chave-google-ai-opcional
   ```

6. **Inicialize o banco de dados:**
   ```bash
   flask db upgrade
   flask seed-db
   ```

7. **Execute a aplicação:**
   ```bash
   flask run
   ```

8. **Acesse no navegador:**
   - URL: http://localhost:5000
   - Usuário admin: `admin@example.com`
   - Senha: `admin123`

## 🔍 Funcionalidades para Demonstração

### 1. **Dashboard Principal**
- Métricas em tempo real
- Gráficos interativos
- KPIs de segurança

### 2. **Gestão de Usuários**
- Criação de novos usuários
- Controle de permissões
- Aprovação de cadastros

### 3. **Sistema de Rondas**
- Registro de patrulhas
- Controle de turnos
- Relatórios de cobertura

### 4. **Gestão de Ocorrências**
- Registro de incidentes
- Classificação automática
- Análise por IA

### 5. **Relatórios PDF**
- Exportação de dados
- Gráficos em PDF
- Métricas detalhadas

## 📊 Aspectos Técnicos Destacados

### **Arquitetura**
- Padrão MVC (Model-View-Controller)
- Blueprints para organização modular
- Separação clara de responsabilidades

### **Banco de Dados**
- SQLAlchemy ORM
- Migrações automáticas
- Relacionamentos bem definidos

### **Segurança**
- Autenticação JWT
- Proteção CSRF
- Rate limiting
- Hash seguro de senhas

### **Integração IA**
- Google Generative AI (Gemini)
- Cache inteligente
- Análise automática de relatórios

### **Frontend**
- Interface responsiva
- Bootstrap 5
- JavaScript moderno
- Gráficos interativos

## 🧪 Testes Automatizados

Execute os testes para verificar a qualidade do código:
```bash
pytest
```

Para relatório de cobertura:
```bash
pytest --cov=app
```

## 📚 Documentação Técnica

- **README Principal:** `README.md`
- **Código Backend:** `backend/`
- **Interface Frontend:** `frontend/`
- **Testes:** `tests/`
- **Licença:** `LICENSE`

## 🎓 Aspectos Acadêmicos

### **Objetivos Alcançados**
- ✅ Sistema funcional e completo
- ✅ Integração com IA
- ✅ Interface moderna e responsiva
- ✅ Testes automatizados
- ✅ Documentação completa
- ✅ Código limpo e organizado

### **Tecnologias Aplicadas**
- Python/Flask (Backend)
- SQLAlchemy (ORM)
- Bootstrap (Frontend)
- Google AI (IA)
- Pytest (Testes)

### **Padrões de Desenvolvimento**
- Clean Code
- SOLID Principles
- MVC Architecture
- RESTful API
- Responsive Design

## 🔧 Comandos Úteis

```bash
# Verificar status do banco
flask db current

# Criar nova migração
flask db migrate -m "descrição"

# Aplicar migrações
flask db upgrade

# Executar testes
pytest

# Limpar cache
flask cache clear
```

## 📞 Suporte

Para dúvidas técnicas sobre o projeto:
- **Email:** luis.royo@outlook.com.br
- **LinkedIn:** [Luis Eduardo Rodrigues Royo](https://www.linkedin.com/in/luis-eduardo-rodrigues-royo-791006171)
- **GitHub:** [luisroyo](https://github.com/luisroyo/meu_projeto_relatorios_mvc)
- **Documentação:** Consulte a pasta `docs/`
- **Código:** Comentários inline no código

---

*Projeto desenvolvido para fins acadêmicos - TCC 2025*
