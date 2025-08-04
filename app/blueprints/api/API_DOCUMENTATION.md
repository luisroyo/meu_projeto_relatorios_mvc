# Documentação da API REST

Esta documentação descreve todas as rotas da API REST disponíveis no sistema de gestão de segurança.

## Autenticação

A API utiliza JWT (JSON Web Tokens) para autenticação. Para acessar endpoints protegidos, inclua o token no header:

```
Authorization: Bearer <seu_token_jwt>
```

## Estrutura de Resposta Padrão

### Sucesso
```json
{
  "message": "Operação realizada com sucesso",
  "data": {...}
}
```

### Erro
```json
{
  "error": "Descrição do erro"
}
```

### Paginação
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 10,
    "total": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

## Endpoints

### Autenticação (`/api/auth`)

#### POST `/api/auth/login`
Login de usuário.
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

#### POST `/api/auth/register`
Registro de novo usuário.
```json
{
  "username": "usuario",
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

#### GET `/api/auth/profile`
Obter perfil do usuário logado.

#### POST `/api/auth/logout`
Logout do usuário.

#### POST `/api/auth/refresh`
Renovar token JWT.

### Dashboard (`/api/dashboard`)

#### GET `/api/dashboard/stats`
Obter estatísticas gerais do dashboard.

#### GET `/api/dashboard/recent-ocorrencias`
Obter ocorrências recentes.

#### GET `/api/dashboard/recent-rondas`
Obter rondas recentes.

### Ocorrências (`/api/ocorrencias`)

#### GET `/api/ocorrencias`
Listar ocorrências com filtros e paginação.
**Parâmetros:**
- `page`: Página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)
- `status`: Status da ocorrência
- `condominio_id`: ID do condomínio
- `supervisor_id`: ID do supervisor
- `tipo_id`: ID do tipo de ocorrência
- `data_inicio`: Data de início (YYYY-MM-DD)
- `data_fim`: Data de fim (YYYY-MM-DD)
- `texto_relatorio`: Busca no relatório

#### GET `/api/ocorrencias/<id>`
Obter detalhes de uma ocorrência específica.

#### POST `/api/ocorrencias`
Criar nova ocorrência.
```json
{
  "relatorio_final": "Descrição da ocorrência",
  "ocorrencia_tipo_id": 1,
  "condominio_id": 1,
  "supervisor_id": 1,
  "turno": "Noturno",
  "status": "Registrada",
  "endereco_especifico": "Endereço específico"
}
```

#### PUT `/api/ocorrencias/<id>`
Atualizar ocorrência.

#### DELETE `/api/ocorrencias/<id>`
Deletar ocorrência.

#### POST `/api/ocorrencias/<id>/approve`
Aprovar ocorrência.

#### POST `/api/ocorrencias/<id>/reject`
Rejeitar ocorrência.

#### POST `/api/ocorrencias/analyze-report`
Analisar relatório usando IA.
```json
{
  "relatorio_bruto": "Texto do relatório bruto"
}
```

#### GET `/api/ocorrencias/tipos`
Listar tipos de ocorrência.

#### GET `/api/ocorrencias/condominios`
Listar condomínios.

### Rondas (`/api/rondas`)

#### GET `/api/rondas`
Listar rondas com filtros e paginação.
**Parâmetros:**
- `page`: Página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)
- `status`: Status da ronda
- `condominio_id`: ID do condomínio
- `supervisor_id`: ID do supervisor
- `data_inicio`: Data de início (YYYY-MM-DD)
- `data_fim`: Data de fim (YYYY-MM-DD)

#### GET `/api/rondas/<id>`
Obter detalhes de uma ronda específica.

#### POST `/api/rondas`
Criar nova ronda.
```json
{
  "condominio_id": 1,
  "data_plantao_ronda": "2024-01-15T08:00:00",
  "escala_plantao": "Diurno",
  "log_ronda_bruto": "Log da ronda",
  "supervisor_id": 1,
  "relatorio_processado": "Relatório processado"
}
```

#### PUT `/api/rondas/<id>`
Atualizar ronda.

#### DELETE `/api/rondas/<id>`
Deletar ronda.

#### POST `/api/rondas/process-whatsapp`
Processar arquivo WhatsApp.
**Form Data:**
- `file`: Arquivo WhatsApp

#### POST `/api/rondas/upload-process`
Upload e processamento de arquivo de ronda.
**Form Data:**
- `file`: Arquivo de ronda

#### GET `/api/rondas/tempo-real`
Obter rondas em tempo real.

#### GET `/api/rondas/tempo-real/hora-atual`
Obter hora atual do servidor.

#### GET `/api/rondas/condominios`
Listar condomínios para rondas.

### Administração (`/api/admin`)

#### Gerenciamento de Usuários

##### GET `/api/admin/users`
Listar usuários com paginação.

##### POST `/api/admin/users/<id>/approve`
Aprovar usuário.

##### POST `/api/admin/users/<id>/revoke`
Revogar aprovação de usuário.

##### POST `/api/admin/users/<id>/toggle-admin`
Alternar status de administrador.

##### POST `/api/admin/users/<id>/toggle-supervisor`
Alternar status de supervisor.

##### DELETE `/api/admin/users/<id>`
Deletar usuário.

#### Gerenciamento de Colaboradores

##### GET `/api/admin/colaboradores`
Listar colaboradores com paginação.

##### POST `/api/admin/colaboradores`
Criar novo colaborador.
```json
{
  "nome_completo": "Nome Completo",
  "cargo": "Cargo",
  "matricula": "12345",
  "data_admissao": "2024-01-15",
  "status": "Ativo"
}
```

##### GET `/api/admin/colaboradores/<id>`
Obter detalhes de colaborador.

##### PUT `/api/admin/colaboradores/<id>`
Atualizar colaborador.

##### DELETE `/api/admin/colaboradores/<id>`
Deletar colaborador.

#### Gerenciamento de Escalas

##### GET `/api/admin/escalas`
Obter escalas mensais.
**Parâmetros:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

##### POST `/api/admin/escalas`
Salvar escalas mensais.
```json
{
  "ano": 2024,
  "mes": 1,
  "escalas": {...}
}
```

#### Ferramentas Administrativas

##### POST `/api/admin/tools/justificativa-atestado`
Gerar justificativa de atestado médico.
```json
{
  "texto_atestado": "Texto do atestado"
}
```

##### POST `/api/admin/tools/justificativa-troca-plantao`
Gerar justificativa de troca de plantão.
```json
{
  "dados_troca": "Dados da troca"
}
```

##### POST `/api/admin/tools/formatar-email`
Formatar email profissional.
```json
{
  "conteudo": "Conteúdo do email"
}
```

#### Dashboards Específicos

##### GET `/api/admin/dashboard/comparativo`
Obter dados do dashboard comparativo.
**Parâmetros:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

##### GET `/api/admin/dashboard/ocorrencias`
Obter dados do dashboard de ocorrências.
**Parâmetros:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

##### GET `/api/admin/dashboard/rondas`
Obter dados do dashboard de rondas.
**Parâmetros:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

### Analisador (`/api/analisador`)

#### POST `/api/analisador/processar-relatorio`
Processar relatório usando IA.
```json
{
  "relatorio_bruto": "Texto do relatório bruto"
}
```

#### GET `/api/analisador/historico`
Obter histórico de processamentos do usuário.
**Parâmetros:**
- `page`: Página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)

## Códigos de Status HTTP

- `200`: Sucesso
- `201`: Criado com sucesso
- `400`: Requisição inválida
- `401`: Não autorizado
- `403`: Acesso negado
- `404`: Não encontrado
- `409`: Conflito
- `500`: Erro interno do servidor

## Exemplos de Uso

### Login e Obter Token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@exemplo.com", "password": "senha123"}'
```

### Listar Ocorrências
```bash
curl -X GET "http://localhost:5000/api/ocorrencias?page=1&per_page=10" \
  -H "Authorization: Bearer <seu_token>"
```

### Criar Nova Ocorrência
```bash
curl -X POST http://localhost:5000/api/ocorrencias \
  -H "Authorization: Bearer <seu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "relatorio_final": "Ocorrência registrada",
    "ocorrencia_tipo_id": 1,
    "condominio_id": 1,
    "turno": "Noturno",
    "status": "Registrada"
  }'
```

### Processar Relatório com IA
```bash
curl -X POST http://localhost:5000/api/analisador/processar-relatorio \
  -H "Authorization: Bearer <seu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "relatorio_bruto": "Texto do relatório bruto para análise"
  }'
``` 