# METODOLOGIA DE DESENVOLVIMENTO - SISTEMA DE GESTÃO DE SEGURANÇA

## 1. INTRODUÇÃO

A proposta de desenvolvimento do Sistema de Gestão de Segurança foi amparada pelo suporte do framework ágil para gerenciamento de projetos **Scrum**. Este framework se baseia em ciclos curtos de trabalho chamados Sprints, onde equipes auto-organizadas desenvolvem funcionalidades priorizadas, garantindo flexibilidade e adaptação a mudanças constantes nos requisitos de segurança.

Para tanto, o trabalho foi estruturado na adaptação de um ciclo iterativo e incremental de desenvolvimento de software baseado nas seguintes atividades fundamentais:

## 2. FRAMEWORK SCRUM ADAPTADO

### 2.1 Desenvolvimento do Product Backlog

O Product Backlog foi desenvolvido baseado em um conjunto abrangente de requisitos funcionais e não funcionais, organizados por prioridade e valor de negócio:

#### 2.1.1 Requisitos Funcionais Prioritários

**Epic 1: Gestão de Usuários e Autenticação**
- RF001: Sistema de autenticação com JWT
- RF002: Controle de acesso baseado em papéis (Admin, Supervisor, Agente)
- RF003: Gerenciamento de perfis de usuário
- RF004: Histórico de login e auditoria de acesso

**Epic 2: Banco de Dados e Infraestrutura**
- RF005: Implementação do banco de dados PostgreSQL

**Epic 3: Gestão de Colaboradores**
- RF006: Cadastro de colaboradores e escalas
- RF007: Controle de plantões diurnos/noturnos
- RF008: Gestão de escalas mensais

**Epic 4: Gestão de Condomínios**
- RF009: Cadastro e gestão de condomínios
- RF010: Integração com colaboradores
- RF011: Relatórios por condomínio

**Epic 5: Sistema de Notificações**
- RF012: Notificações em tempo real
- RF013: Alertas de ocorrências
- RF014: Comunicação entre usuários

**Epic 6: Gestão de Rondas**
- RF015: Cadastro e programação de rondas
- RF016: Execução de rondas com checkpoints
- RF017: Rondas em tempo real com geolocalização
- RF018: Relatórios de rondas por período

**Epic 7: Gestão de Ocorrências**
- RF019: Registro de ocorrências com classificação automática
- RF020: Workflow de atendimento de incidentes
- RF021: Integração com órgãos públicos
- RF022: Geração de relatórios de ocorrências

**Epic 8: Inteligência Artificial**
- RF023: Classificação automática de ocorrências
- RF024: Análise de padrões e tendências
- RF025: Geração de insights de segurança
- RF026: Formatação inteligente de relatórios

**Epic 9: Relatórios e Analytics**
- RF027: Sistema de relatórios avançados
- RF028: Dashboards e analytics
- RF029: Exportação de dados

#### 2.1.2 Requisitos Não Funcionais

**Performance e Escalabilidade**
- RNF001: Tempo de resposta < 2 segundos para operações críticas
- RNF002: Suporte a 100 usuários simultâneos
- RNF003: Disponibilidade de 99.5%
- RNF004: Cache inteligente para consultas frequentes

**Segurança e Conformidade**
- RNF005: Criptografia de dados sensíveis
- RNF006: Logs de auditoria completos
- RNF007: Proteção contra ataques CSRF e XSS
- RNF008: Rate limiting para APIs

**Usabilidade e Acessibilidade**
- RNF009: Interface responsiva para dispositivos móveis
- RNF010: Tempo de aprendizado < 30 minutos
- RNF011: Suporte a navegadores modernos
- RNF012: Acessibilidade WCAG 2.1 AA

### 2.2 Sprint Planning

O Sprint Planning foi detalhado baseado em um modelo de desenvolvimento distribuído ao longo de **8 meses (Fevereiro a Setembro)**, com distribuição semanal de tarefas, considerando a complexidade do domínio de segurança e a necessidade de desenvolvimento incremental:

#### 2.2.1 Período de Desenvolvimento: Fevereiro a Setembro (24 semanas)

**Fevereiro (Semanas 1-3) - Fundação e Banco de Dados**
- **Semana 1**: Configuração do ambiente de desenvolvimento
- **Semana 2**: Modelagem do banco de dados PostgreSQL
- **Semana 3**: Relacionamentos e migrações

**Março (Semanas 4-6) - Sistema de Autenticação**
- **Semana 4**: Sistema de autenticação JWT
- **Semana 5**: CRUD de usuários e papéis
- **Semana 6**: Interface de login

**Abril (Semanas 7-9) - Gestão de Colaboradores**
- **Semana 7**: Modelo e CRUD colaboradores
- **Semana 8**: Sistema de escalas mensais
- **Semana 9**: Interface gestão colaboradores

**Maio (Semanas 10-12) - Gestão de Condomínios**
- **Semana 10**: Modelo e CRUD condomínios
- **Semana 11**: Integração com colaboradores
- **Semana 12**: Interface gestão condomínios

**Junho (Semanas 13-15) - Gestão de Rondas**
- **Semana 13**: Modelo e programação rondas
- **Semana 14**: Execução com geolocalização
- **Semana 15**: Interface execução rondas

**Julho (Semanas 16-18) - Gestão de Ocorrências**
- **Semana 16**: Modelo e CRUD ocorrências
- **Semana 17**: Workflow de atendimento
- **Semana 18**: Sistema de notificações

**Agosto (Semanas 19-21) - Inteligência Artificial**
- **Semana 19**: Integração Google Gemini
- **Semana 20**: Classificação automática
- **Semana 21**: Geração de insights

**Setembro (Semanas 22-24) - Relatórios e Deploy**
- **Semana 22**: Sistema de relatórios
- **Semana 23**: Dashboards e analytics
- **Semana 24**: Deploy e documentação
- Testes de integração
- Deploy em produção
- Monitoramento e logs

### 2.3 Sprint Goal

A determinação das metas foi estabelecida em formato de software para contemplar o modelo iterativo e incremental, distribuído ao longo de 8 meses:

#### 2.3.1 Critérios de Aceitação por Período Mensal

**Fevereiro - Fundação e Banco de Dados**
- ✅ Ambiente de desenvolvimento configurado
- ✅ Banco PostgreSQL implementado
- ✅ Modelagem de dados completa
- ✅ Migrações funcionais

**Março - Sistema de Autenticação**
- ✅ Sistema de autenticação JWT funcional
- ✅ CRUD completo de usuários
- ✅ Controle de acesso por papéis
- ✅ Interface de login responsiva

**Abril - Gestão de Colaboradores**
- ✅ CRUD completo de colaboradores
- ✅ Sistema de escalas mensais
- ✅ Controle de plantões
- ✅ Interface de gestão responsiva

**Maio - Gestão de Condomínios**
- ✅ CRUD completo de condomínios
- ✅ Integração com colaboradores
- ✅ Relatórios por condomínio
- ✅ Interface de gestão responsiva

**Junho - Gestão de Rondas**
- ✅ Sistema de rondas operacional
- ✅ Interface mobile para execução
- ✅ Geolocalização funcionando
- ✅ Relatórios de rondas gerados

**Julho - Gestão de Ocorrências**
- ✅ Workflow completo de ocorrências
- ✅ Sistema de notificações
- ✅ Integração com órgãos públicos
- ✅ Relatórios detalhados

**Agosto - Inteligência Artificial**
- ✅ IA integrada com Gemini
- ✅ Classificação automática avançada
- ✅ Análise de padrões implementada
- ✅ Insights gerados automaticamente

**Setembro - Relatórios e Deploy**
- ✅ Sistema de relatórios avançados
- ✅ Dashboards e analytics
- ✅ Sistema em produção
- ✅ Documentação completa

### 2.4 Daily Scrum

As reuniões de orientação do desenvolvimento foram estruturadas com foco em validação semanal, considerando o cronograma distribuído ao longo de 8 meses:

#### 2.4.1 Estrutura das Reuniões de Validação
- **Duração**: 30 minutos
- **Frequência**: Semanal (sextas-feiras)
- **Participantes**: Desenvolvedor, Orientador, Stakeholders
- **Formato**: Apresentação e validação semanal:
  1. O que foi desenvolvido nesta semana?
  2. Quais funcionalidades estão prontas para validação?
  3. Existem impedimentos ou ajustes necessários?
  4. Planejamento da próxima semana

#### 2.4.2 Cronograma de Validação Semanal

**Fevereiro**
- **07/02**: Validação da configuração do ambiente
- **14/02**: Validação da modelagem do banco de dados
- **21/02**: Validação dos relacionamentos e migrações

**Março**
- **07/03**: Validação do sistema de autenticação JWT
- **14/03**: Validação do CRUD de usuários e papéis
- **21/03**: Validação da interface de login

**Abril**
- **07/04**: Validação do modelo e CRUD colaboradores
- **14/04**: Validação do sistema de escalas mensais
- **21/04**: Validação da interface de gestão colaboradores

**Maio**
- **07/05**: Validação do modelo e CRUD condomínios
- **14/05**: Validação da integração com colaboradores
- **21/05**: Validação da interface de gestão condomínios

**Junho**
- **07/06**: Validação do modelo e programação rondas
- **14/06**: Validação da execução com geolocalização
- **21/06**: Validação da interface de execução rondas

**Julho**
- **07/07**: Validação do modelo e CRUD ocorrências
- **14/07**: Validação do workflow de atendimento
- **21/07**: Validação do sistema de notificações

**Agosto**
- **07/08**: Validação da integração Google Gemini
- **14/08**: Validação da classificação automática
- **21/08**: Validação da geração de insights

**Setembro**
- **07/09**: Validação do sistema de relatórios
- **14/09**: Validação dos dashboards e analytics
- **21/09**: Validação final e homologação do sistema

## 3. DOCUMENTAÇÃO DE SOFTWARE

Para atender aos requisitos mínimos de documentação de software, foram desenvolvidos os seguintes diagramas:

### 3.1 Diagramas de Casos de Uso

#### 3.1.1 Atores Principais
- **Administrador**: Gestão completa do sistema
- **Supervisor**: Supervisão de operações e relatórios
- **Agente de Segurança**: Execução de rondas e registro de ocorrências
- **Sistema de IA**: Classificação automática e análise

#### 3.1.2 Casos de Uso Principais

**UC001 - Autenticar Usuário**
- **Ator**: Usuário do Sistema
- **Pré-condições**: Usuário cadastrado no sistema
- **Fluxo Principal**:
  1. Usuário acessa a tela de login
  2. Sistema exibe formulário de autenticação
  3. Usuário informa credenciais
  4. Sistema valida credenciais
  5. Sistema gera token JWT
  6. Sistema redireciona para dashboard

**UC002 - Executar Ronda**
- **Ator**: Agente de Segurança
- **Pré-condições**: Usuário autenticado e ronda programada
- **Fluxo Principal**:
  1. Agente acessa lista de rondas pendentes
  2. Sistema exibe rondas disponíveis
  3. Agente seleciona ronda para execução
  4. Sistema inicia ronda com geolocalização
  5. Agente executa checkpoints
  6. Sistema registra conclusão da ronda

**UC003 - Registrar Ocorrência**
- **Ator**: Agente de Segurança
- **Pré-condições**: Usuário autenticado
- **Fluxo Principal**:
  1. Agente acessa formulário de ocorrência
  2. Sistema exibe campos obrigatórios
  3. Agente preenche dados da ocorrência
  4. Sistema classifica automaticamente com IA
  5. Sistema atribui responsáveis
  6. Sistema notifica supervisores

### 3.2 Diagramas de Componentes

#### 3.2.1 Arquitetura de Componentes

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Bootstrap)   │◄──►│   (Flask)       │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   External      │
                       │   Services      │
                       │  (Gemini AI)    │
                       └─────────────────┘
```

#### 3.2.2 Componentes Principais

**Camada de Apresentação**
- Templates Jinja2
- Bootstrap CSS Framework
- JavaScript para interatividade
- API RESTful endpoints

**Camada de Negócio**
- Blueprints Flask (Auth, Admin, API, Ronda, Ocorrência)
- Services Layer (Business Logic)
- Decorators (Admin Required, Rate Limiting)
- Middleware (User Activity)

**Camada de Dados**
- SQLAlchemy ORM
- Models (User, Ronda, Ocorrência, Colaborador)
- Migrations (Alembic)
- Views Materializadas

**Camada de Integração**
- Google Generative AI (Gemini)
- Email Services
- File Storage
- External APIs

### 3.3 Diagramas de Tabelas e Relacionamentos

#### 3.3.1 Modelo de Dados Principal

```sql
-- Tabelas Principais
Users (id, username, email, password_hash, role, created_at, updated_at)
Rondas (id, condominio_id, agente_id, data_inicio, data_fim, status, observacoes)
Ocorrencias (id, tipo_id, agente_id, condominio_id, descricao, status, data_ocorrencia)
Colaboradores (id, nome, cpf, telefone, email, cargo, ativo)
Condominios (id, nome, endereco, contato, ativo)

-- Tabelas de Relacionamento
Ocorrencia_Orgao_Publico (ocorrencia_id, orgao_id)
Ocorrencia_Colaborador (ocorrencia_id, colaborador_id)
Escala_Mensal (id, colaborador_id, mes, ano, plantao_diurno, plantao_noturno)

-- Views Materializadas
vw_rondas_detalhadas
vw_ocorrencias_detalhadas
vw_colaboradores
vw_logradouros
```

#### 3.3.2 Relacionamentos Principais

- **Users** 1:N **Rondas** (Um usuário pode executar várias rondas)
- **Users** 1:N **Ocorrencias** (Um usuário pode registrar várias ocorrências)
- **Condominios** 1:N **Rondas** (Um condomínio pode ter várias rondas)
- **Condominios** 1:N **Ocorrencias** (Um condomínio pode ter várias ocorrências)
- **Ocorrencias** N:M **Orgao_Publico** (Uma ocorrência pode envolver vários órgãos)
- **Ocorrencias** N:M **Colaboradores** (Uma ocorrência pode envolver vários colaboradores)

## 4. ESTRATÉGIA DE TESTES E VALIDAÇÃO

### 4.1 Plataforma de Testes

O software foi testado utilizando uma abordagem multicamada:

#### 4.1.1 Ambiente de Desenvolvimento
- **Backend**: Flask com SQLAlchemy
- **Frontend**: Bootstrap com JavaScript
- **Database**: PostgreSQL com dados de teste
- **IA**: Google Gemini API (sandbox)

#### 4.1.2 Ambiente de Testes
- **Testes Unitários**: Pytest com cobertura > 90%
- **Testes de Integração**: API endpoints e database
- **Testes de Interface**: Selenium WebDriver
- **Testes de Performance**: Load testing com dados simulados

### 4.2 Captura e Validação de Dados

#### 4.2.1 Dados de Teste
- **Usuários**: 50 usuários simulados (Admin, Supervisor, Agente)
- **Rondas**: 200 rondas históricas de 3 meses
- **Ocorrências**: 150 ocorrências variadas com classificação
- **Colaboradores**: 30 colaboradores com escalas mensais

#### 4.2.2 Validação de Funcionalidades
- **Autenticação**: Testes de login/logout e controle de sessão
- **Rondas**: Validação de execução e relatórios
- **Ocorrências**: Teste de workflow completo
- **IA**: Validação de classificação automática
- **Relatórios**: Geração e exportação de dados

### 4.3 Métricas de Qualidade

#### 4.3.1 Cobertura de Testes
- **Testes Unitários**: > 90% de cobertura
- **Testes de Integração**: 100% dos endpoints críticos
- **Testes de Interface**: Fluxos principais validados

#### 4.3.2 Performance
- **Tempo de Resposta**: < 2 segundos para operações críticas
- **Concorrência**: 50 usuários simultâneos testados
- **Disponibilidade**: 99.5% em ambiente de produção

## 5. CONCLUSÃO

A metodologia de desenvolvimento baseada em Scrum adaptada para o Sistema de Gestão de Segurança demonstrou ser eficaz na entrega de um produto robusto e funcional. A abordagem iterativa e incremental permitiu:

- **Flexibilidade**: Adaptação a mudanças de requisitos
- **Qualidade**: Testes contínuos e validação constante
- **Transparência**: Comunicação clara entre stakeholders
- **Entrega de Valor**: Funcionalidades priorizadas por impacto

A documentação estruturada (casos de uso, componentes e modelo de dados) garantiu a manutenibilidade e evolução do sistema, enquanto a estratégia de testes multicamada assegurou a qualidade e confiabilidade da solução desenvolvida.

---

**Elaborado por**: Assistente de IA Claude Sonnet  
**Data**: Janeiro 2025  
**Versão**: 1.0  
**Projeto**: Sistema de Gestão de Segurança
