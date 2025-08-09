# Meu Projeto Relatórios MVC

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-xx%25-blue)](https://github.com/luisroyo/meu_projeto_relatorios_mvc/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Descrição do Projeto

**Meu Projeto Relatórios MVC** é uma aplicação web robusta e modular para gerenciar, analisar e relatar eventos de segurança e operacionais (rondas, ocorrências, colaboradores, etc.) em ambientes residenciais ou corporativos. O sistema utiliza tecnologias web Python modernas e integra-se com IA generativa para auxiliar na análise e formatação de relatórios, fornecendo uma plataforma segura, escalável e amigável para administradores, supervisores e funcionários.

## Screenshots

<!-- Adicione aqui imagens/gifs do sistema rodando -->
<!-- Exemplo: -->
<!-- ![Dashboard](docs/screenshot_dashboard.png) -->

## Pilha de Tecnologia

- Backend: Python 3, Flask 3.x (com Blueprints, Padrão de Fábrica)
- Banco de Dados: SQLAlchemy ORM, Flask-Migrate (suporta SQLite, PostgreSQL, etc.)
- Autenticação: Flask-Login, decoradores de administrador personalizados
- Formulários e Validação: Flask-WTF, WTForms
- Limitação de Taxa e Segurança: Flask-Limiter, Flask-WTF CSRF, hashing de senha (Werkzeug)
- Cache: Flask-Caching (com suporte para Redis, SimpleCache, etc.)
- Integração com IA: Google Generative AI (API Gemini)
- Arquivos Estáticos: WhiteNoise
- Testes: Pytest
- Ferramentas CLI: Flask CLI, Click
- Outros: Logging, dotenv, validação de e-mail

## Configuração e Instalação

### Pré-requisitos

- Python 3.8+
- (Recomendado) Poetry ou pipenv para ambientes virtuais, ou use venv
- (Opcional) PostgreSQL ou outro banco de dados pronto para produção

### 1. Clonar o Repositório

git clone https://github.com/luisroyo/meu_projeto_relatorios_mvc.git
cd meu_projeto_relatorios_mvc

### 2. Criar e Ativar um Ambiente Virtual

python -m venv venv
source venv/bin/activate    # No Windows: venv\Scripts\activate

### 3. Instalar Dependências

pip install -r requirements.txt

Observação: o `requirements.txt` da raiz inclui `backend/requirements.txt`. Em plataformas como Render, mantenha o comando de build como `pip install -r requirements.txt`.

### 4. Definir Variáveis de Ambiente

Crie um arquivo .env na raiz do projeto (nunca comite este arquivo):

```env
SECRET_KEY=sua-chave-muito-secreta
DATABASE_URL=sqlite:///dev.db    # Ou sua URI PostgreSQL
FLASK_DEBUG=True

# API Keys para fallback automático (veja API_KEYS_SETUP.md para detalhes)
GOOGLE_API_KEY_1=sua-chave-google-generative-ai-principal
GOOGLE_API_KEY_2=sua-chave-google-generative-ai-backup

# Redis (opcional - para cache em produção)
REDIS_URL=redis://usuario:senha@host:porta/0
```

**📋 Para configuração detalhada das API Keys, consulte [API_KEYS_SETUP.md](API_KEYS_SETUP.md)**

### 5. Configurar Redis (Opcional)

O sistema usa cache para otimizar as respostas da API Gemini. Por padrão, usa cache em memória (SimpleCache).

**Para usar Redis em produção:**
1. Configure `REDIS_URL` nas variáveis de ambiente
2. Execute o teste: `python test_redis.py`
3. O sistema automaticamente detecta e usa Redis se disponível

**Para desenvolvimento local:** SimpleCache é suficiente e não requer configuração adicional.

### 6. Inicializar o Banco de Dados

flask db upgrade
flask seed-db    # Cria usuários admin/supervisor iniciais (apenas para desenvolvimento)

### 7. Executar a Aplicação

flask run

O aplicativo estará disponível em http://localhost:5000.

## Visão Geral de Uso e Recursos

### Papéis de Usuário

- Admin: Acesso total ao gerenciamento de usuários, dashboards e ferramentas do sistema.
- Supervisor: Pode gerenciar e supervisionar relatórios e eventos.
- Usuário Regular: Pode enviar e analisar relatórios, visualizar seu próprio histórico.

### Principais Recursos

- Autenticação e Autorização: Login seguro, registro (com aprovação do administrador) e acesso baseado em funções.
- Dashboard: Métricas visuais para usuários, logins, relatórios e KPIs operacionais.
- Rondas: Registrar, listar e analisar registros de patrulha.
- Ocorrências: Registrar, classificar e gerenciar incidentes com análise assistida por IA.
- Colaboradores: Gerenciar registros e atribuições de pessoal.
- Analisador de Relatórios AI: Cole relatórios brutos e receba versões formatadas e corrigidas geradas por IA.
- Ferramentas de Administração: Aprovar usuários, gerenciar funções, excluir usuários e muito mais.
- Limitação de Taxa (Rate Limiting): Previne ataques de força bruta e abuso em logins e endpoints sensíveis.
- Log (Registro): Logs detalhados para auditoria e depuração.
- UI Responsiva: Interface moderna e amigável para dispositivos móveis (baseada em Bootstrap).

## Documentação da API

<!-- Se você expõe endpoints de API, documente-os aqui ou adicione um link para Swagger/Postman/etc. -->
<!-- Exemplo: -->
<!-- Veja a documentação completa da API em [docs/api.md](docs/api.md) -->

## API RESTful

Agora o projeto segue o padrão RESTful para integração com front-end web/mobile:

- Todas as rotas de API usam o prefixo `/api/`.
- Exemplo de endpoint:
  - `POST /api/ocorrencias/analisar-relatorio` — para análise automática de relatórios de ocorrência.
- As rotas de API têm CORS habilitado e CSRF desabilitado.
- As rotas antigas continuam funcionando temporariamente para compatibilidade.

Para consumir a API, envie requisições para `/api/ocorrencias/analisar-relatorio` com o corpo JSON:
```json
{
  "texto_relatorio": "...texto do relatório..."
}
```
A resposta será:
```json
{
  "sucesso": true,
  "dados": { ...campos extraídos... }
}
```

## Instruções de Teste

### Testes Unitários

1. Executar Todos os Testes:

pytest

### Scripts de Monitoramento

Para testar e monitorar o Redis e cache:

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

**📋 Para mais detalhes sobre os scripts, consulte [scripts/README.md](scripts/README.md)**

2. Estrutura de Teste:
- Os testes estão localizados no diretório tests/, organizados por recurso e serviço.
- Utiliza um banco de dados SQLite em memória para isolamento.
- Adicione novos testes no módulo ou subpasta de serviço apropriado.

3. Configuração:
- pytest.ini garante o caminho Python correto.
- A configuração de teste desabilita o CSRF e usa SimpleCache.

4. Cobertura de Testes:
- Para gerar um relatório de cobertura, instale o pytest-cov (se ainda não tiver):

pip install pytest-cov

- Execute:

pytest --cov=app

- O badge de coverage é atualizado manualmente. Use o valor do relatório para atualizar o badge no topo deste README.

## Considerações de Segurança

- Segredos: Nunca comite .env ou chaves sensíveis. Sempre defina SECRET_KEY e GOOGLE_API_KEY via variáveis de ambiente.
- Armazenamento de Senhas: Senhas são armazenadas com hash de forma segura usando Werkzeug.
- Proteção CSRF: Habilitada em todos os formulários.
- Limitação de Taxa: Login e outros endpoints sensíveis são limitados por taxa.
- Segurança de Sessão: Para produção, defina SESSION_COOKIE_SECURE=True e SESSION_COOKIE_HTTPONLY=True.
- Aprovação de Usuário: Novos usuários exigem aprovação do administrador antes de acessar o sistema.
- Acesso de Administrador: Todas as rotas de administração são protegidas por um decorador admin_required personalizado.
- Log (Registro): Evite registrar dados sensíveis (por exemplo, senhas, e-mails completos) em logs de produção.

## Boas Práticas e Recomendações

- Separação de Ambiente: Use diferentes classes de configuração para desenvolvimento, teste e produção.
- Backups de Banco de Dados: Faça backup regularmente do seu banco de dados de produção.
- Atualizações de Dependências: Mantenha as dependências atualizadas e monitore avisos de segurança.
- Documentação: Documente quaisquer comandos CLI personalizados e fluxos de trabalho de administração.
- Testes: Busque alta cobertura de testes, especialmente para lógica de negócios e recursos de segurança.
- Arquivos Estáticos e de Mídia: Use um CDN ou armazenamento de objetos para arquivos enviados por usuários em produção.
- Monitoramento: Configure monitoramento de erros e alertas para implantações em produção.
- Acessibilidade: Garanta que os componentes da UI sejam acessíveis (rótulos ARIA, navegação por teclado, etc.).

## Contribuição

Pull requests e issues são bem-vindos! Por favor, abra uma issue para discutir grandes mudanças antes de enviar um PR.
Consulte o guia de contribuição em [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes sobre o processo.

## Licença

[MIT License](LICENSE) (ou sua licença escolhida)

Para dúvidas ou suporte, entre em contato com [luisroyo25@gmail.com].
