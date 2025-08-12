# 📚 Documentação das APIs - Sistema de Gestão de Segurança

## 🔐 Autenticação

### POST `/api/auth/login`
**Login e obtenção de token JWT**

**Request Body:**
```json
{
  "email": "luisroyo25@gmail.com",
  "password": "edu123csS"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "Luis Royo",
    "email": "luisroyo25@gmail.com",
    "is_admin": true,
    "is_supervisor": true,
    "is_approved": true
  }
}
```

### POST `/api/auth/register`
**Registro de novo usuário**

**Request Body:**
```json
{
  "username": "Novo Usuário",
  "email": "novo@email.com",
  "password": "senha123"
}
```

**Response (201):**
```json
{
  "message": "Usuário registrado com sucesso. Aguarde aprovação do administrador.",
  "user_id": 5
}
```

### GET `/api/auth/profile`
**Obter perfil do usuário logado**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "username": "Luis Royo",
  "email": "luisroyo25@gmail.com",
  "is_admin": true,
  "is_supervisor": true,
  "is_approved": true,
  "date_registered": "2025-01-01T00:00:00",
  "last_login": "2025-08-02T19:00:00"
}
```

### POST `/api/auth/logout`
**Logout (cliente deve remover o token)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

### POST `/api/auth/refresh`
**Renovar token**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 📊 Dashboard

### GET `/api/dashboard/stats`
**Obter estatísticas do dashboard**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "stats": {
    "total_ocorrencias": 150,
    "total_rondas": 89,
    "total_condominios": 12,
    "rondas_em_andamento": 3,
    "ocorrencias_ultimo_mes": 45,
    "rondas_ultimo_mes": 67
  },
  "user": {
    "id": 1,
    "username": "Luis Royo",
    "is_admin": true,
    "is_supervisor": true
  }
}
```

### GET `/api/dashboard/recent-ocorrencias`
**Obter ocorrências recentes**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "ocorrencias": [
    {
      "id": 1,
      "tipo": "Furto",
      "condominio": "ZERMATT",
      "data": "2025-08-02T15:30:00",
      "descricao": "Furto de bicicleta no estacionamento..."
    }
  ]
}
```

### GET `/api/dashboard/recent-rondas`
**Obter rondas recentes**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "rondas": [
    {
      "id": 1,
      "condominio": "ZERMATT",
      "data_plantao": "2025-08-02",
      "escala_plantao": "06h às 18h",
      "status": "finalizada",
      "total_rondas": 8
    }
  ]
}
```

### GET `/api/dashboard/condominios`
**Obter lista de condomínios**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT"
    },
    {
      "id": 2,
      "nome": "RESIDENCIAL VILLA VERDE"
    }
  ]
}
```

## 🔄 Rondas em Tempo Real

### GET `/api/ronda-tempo-real/condominios`
**Obter condomínios disponíveis para rondas**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT"
    },
    {
      "id": 2,
      "nome": "RESIDENCIAL VILLA VERDE"
    }
  ]
}
```

### GET `/api/ronda-tempo-real/em-andamento`
**Obter rondas em andamento**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "rondas": [
    {
      "id": 1,
      "condominio": "ZERMATT",
      "hora_entrada": "18:30:00",
      "data_inicio": "2025-08-02T18:30:00",
      "observacoes": "Ronda iniciada",
      "status": "em_andamento"
    }
  ]
}
```

### POST `/api/ronda-tempo-real/iniciar`
**Iniciar nova ronda**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "condominio_id": 1,
  "hora_entrada": "18:30:00",
  "observacoes": "Iniciando ronda"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Ronda iniciada com sucesso",
  "ronda": {
    "id": 1,
    "condominio": "ZERMATT",
    "hora_entrada": "18:30:00",
    "status": "em_andamento"
  }
}
```

### POST `/api/ronda-tempo-real/finalizar/<ronda_id>`
**Finalizar ronda**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "hora_saida": "19:15:00",
  "observacoes": "Ronda finalizada"
}
```

**Response (200):**
```json
{
  "message": "Ronda finalizada com sucesso",
  "ronda": {
    "id": 1,
    "status": "finalizada",
    "hora_saida": "19:15:00"
  }
}
```

### POST `/api/ronda-tempo-real/cancelar/<ronda_id>`
**Cancelar ronda em andamento**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Ronda cancelada com sucesso"
}
```

### GET `/api/ronda-tempo-real/estatisticas`
**Obter estatísticas das rondas em tempo real**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_rondas": 89,
  "rondas_em_andamento": 3,
  "rondas_concluidas": 86,
  "tempo_medio": 45
}
```

### GET `/api/ronda-tempo-real/hora-atual`
**Obter hora atual do servidor**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "hora_atual": "18:30:00"
}
```

### GET `/api/ronda-tempo-real/condominios-com-ronda-em-andamento`
**Obter condomínios com ronda em andamento**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT",
      "ronda_id": 1,
      "hora_entrada": "18:30:00"
    }
  ]
}
```

### GET `/api/ronda-tempo-real/condominios-com-ronda-realizada`
**Obter condomínios com ronda realizada**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 2,
      "nome": "RESIDENCIAL VILLA VERDE",
      "ultima_ronda": "2025-08-02T17:00:00",
      "total_rondas": 5
    }
  ]
}
```

### GET `/api/ronda-tempo-real/rondas-condominio/<condominio_id>`
**Obter rondas de um condomínio específico**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "rondas": [
    {
      "id": 1,
      "data_inicio": "2025-08-02T18:30:00",
      "hora_entrada": "18:30:00",
      "status": "finalizada"
    }
  ]
}
```

## 🚨 Ocorrências

### GET `/api/ocorrencias`
**Listar ocorrências com paginação e filtros**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)
- `status`: Status da ocorrência
- `condominio_id`: ID do condomínio
- `supervisor_id`: ID do supervisor
- `tipo_id`: ID do tipo de ocorrência
- `data_inicio`: Data de início (YYYY-MM-DD)
- `data_fim`: Data de fim (YYYY-MM-DD)
- `texto_relatorio`: Busca no relatório

**Response (200):**
```json
{
  "ocorrencias": [
    {
      "id": 1,
      "tipo": "Furto",
      "condominio": "ZERMATT",
      "data_ocorrencia": "2025-08-02T15:30:00",
      "hora_ocorrencia": "15:30:00",
      "descricao": "Furto de bicicleta...",
      "local": "Estacionamento",
      "envolvidos": "João Silva",
      "acoes_tomadas": "Registrado BO",
      "status": "pendente",
      "registrado_por": "Luis Royo",
      "data_registro": "2025-08-02T15:35:00"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "total": 50,
    "per_page": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

### GET `/api/ocorrencias/<id>`
**Obter detalhes de uma ocorrência específica**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "tipo": {
    "id": 1,
    "nome": "Furto"
  },
  "condominio": {
    "id": 1,
    "nome": "ZERMATT"
  },
  "data_ocorrencia": "2025-08-02T15:30:00",
  "hora_ocorrencia": "15:30:00",
  "descricao": "Furto de bicicleta no estacionamento",
  "local": "Estacionamento",
  "envolvidos": "João Silva",
  "acoes_tomadas": "Registrado BO",
  "status": "pendente",
  "registrado_por": {
    "id": 1,
    "username": "Luis Royo"
  },
  "data_registro": "2025-08-02T15:35:00"
}
```

### POST `/api/ocorrencias`
**Criar nova ocorrência**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "tipo_ocorrencia_id": 1,
  "condominio_id": 1,
  "data_ocorrencia": "2025-08-02",
  "hora_ocorrencia": "15:30:00",
  "descricao": "Furto de bicicleta no estacionamento",
  "local": "Estacionamento",
  "envolvidos": "João Silva",
  "acoes_tomadas": "Registrado BO",
  "status": "pendente"
}
```

**Response (201):**
```json
{
  "message": "Ocorrência criada com sucesso",
  "ocorrencia_id": 1
}
```

### PUT `/api/ocorrencias/<id>`
**Atualizar ocorrência existente**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "status": "finalizada",
  "acoes_tomadas": "Registrado BO e recuperado o bem"
}
```

**Response (200):**
```json
{
  "message": "Ocorrência atualizada com sucesso"
}
```

### DELETE `/api/ocorrencias/<id>`
**Deletar ocorrência (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Ocorrência deletada com sucesso"
}
```

### POST `/api/ocorrencias/<id>/approve`
**Aprovar ocorrência**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Ocorrência aprovada com sucesso"
}
```

### POST `/api/ocorrencias/<id>/reject`
**Rejeitar ocorrência**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "motivo": "Informações insuficientes"
}
```

**Response (200):**
```json
{
  "message": "Ocorrência rejeitada"
}
```

### POST `/api/ocorrencias/analyze-report`
**Analisar relatório usando IA**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "relatorio_bruto": "Texto do relatório bruto"
}
```

**Response (200):**
```json
{
  "analise": {
    "tipo_sugerido": "Furto",
    "confianca": 0.85,
    "entidades_identificadas": ["João Silva", "Estacionamento"],
    "resumo": "Relatório analisado com sucesso"
  }
}
```

### GET `/api/ocorrencias/tipos`
**Listar tipos de ocorrência**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "tipos": [
    {
      "id": 1,
      "nome": "Furto",
      "descricao": "Furto de bens"
    }
  ]
}
```

### GET `/api/ocorrencias/condominios`
**Listar condomínios para filtros**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT"
    }
  ]
}
```

## 🔄 Rondas

### GET `/api/rondas`
**Listar rondas com paginação e filtros**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)
- `status`: Status da ronda
- `condominio_id`: ID do condomínio
- `supervisor_id`: ID do supervisor
- `data_inicio`: Data de início (YYYY-MM-DD)
- `data_fim`: Data de fim (YYYY-MM-DD)

**Response (200):**
```json
{
  "rondas": [
    {
      "id": 1,
      "condominio": "ZERMATT",
      "data_plantao": "2025-08-02",
      "escala_plantao": "06h às 18h",
      "status": "finalizada",
      "supervisor": "Luis Royo"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "total": 50,
    "per_page": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

### GET `/api/rondas/<id>`
**Obter detalhes de uma ronda específica**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "condominio": {
    "id": 1,
    "nome": "ZERMATT"
  },
  "data_plantao": "2025-08-02",
  "escala_plantao": "06h às 18h",
  "status": "finalizada",
  "supervisor": {
    "id": 1,
    "username": "Luis Royo"
  },
  "log_ronda_bruto": "Log da ronda...",
  "relatorio_processado": "Relatório processado..."
}
```

### POST `/api/rondas`
**Criar nova ronda**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "condominio_id": 1,
  "data_plantao_ronda": "2025-08-02T08:00:00",
  "escala_plantao": "06h às 18h",
  "log_ronda_bruto": "Log da ronda",
  "supervisor_id": 1,
  "relatorio_processado": "Relatório processado"
}
```

**Response (201):**
```json
{
  "message": "Ronda criada com sucesso",
  "ronda_id": 1
}
```

### PUT `/api/rondas/<id>`
**Atualizar ronda**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "status": "finalizada",
  "relatorio_processado": "Relatório atualizado"
}
```

**Response (200):**
```json
{
  "message": "Ronda atualizada com sucesso"
}
```

### DELETE `/api/rondas/<id>`
**Deletar ronda (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Ronda deletada com sucesso"
}
```

### POST `/api/rondas/process-whatsapp`
**Processar arquivo WhatsApp**

**Headers:** `Authorization: Bearer <token>`

**Form Data:**
- `file`: Arquivo WhatsApp

**Response (200):**
```json
{
  "message": "Arquivo processado com sucesso",
  "ronda_id": 1
}
```

### POST `/api/rondas/upload-process`
**Upload e processamento de arquivo de ronda**

**Headers:** `Authorization: Bearer <token>`

**Form Data:**
- `file`: Arquivo de ronda

**Response (200):**
```json
{
  "message": "Arquivo processado com sucesso",
  "ronda_id": 1
}
```

### GET `/api/rondas/condominios`
**Listar condomínios para rondas**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT"
    }
  ]
}
```

## 👨‍💼 Admin

### GET `/api/admin/users`
**Listar usuários com paginação (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "Luis Royo",
      "email": "luisroyo25@gmail.com",
      "is_admin": true,
      "is_supervisor": true,
      "is_approved": true,
      "date_registered": "2025-01-01T00:00:00",
      "last_login": "2025-08-02T19:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 1,
    "total": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

### POST `/api/admin/users/<id>/approve`
**Aprovar usuário (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Usuário aprovado com sucesso"
}
```

### POST `/api/admin/users/<id>/revoke`
**Revogar aprovação de usuário (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Aprovação do usuário revogada"
}
```

### POST `/api/admin/users/<id>/toggle-admin`
**Alternar status de administrador (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Status de administrador alterado"
}
```

### POST `/api/admin/users/<id>/toggle-supervisor`
**Alternar status de supervisor (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Status de supervisor alterado"
}
```

### DELETE `/api/admin/users/<id>`
**Deletar usuário (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Usuário deletado com sucesso"
}
```

### GET `/api/admin/colaboradores`
**Listar colaboradores (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)

**Response (200):**
```json
{
  "colaboradores": [
    {
      "id": 1,
      "nome_completo": "João Silva",
      "cargo": "Segurança",
      "matricula": "001",
      "data_admissao": "2025-01-01",
      "status": "Ativo"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 1,
    "total": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

### POST `/api/admin/colaboradores`
**Criar novo colaborador (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "nome_completo": "João Silva",
  "cargo": "Segurança",
  "matricula": "001",
  "data_admissao": "2025-01-01",
  "status": "Ativo"
}
```

**Response (201):**
```json
{
  "message": "Colaborador criado com sucesso",
  "colaborador_id": 1
}
```

### GET `/api/admin/colaboradores/<id>`
**Obter detalhes de colaborador (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "nome_completo": "João Silva",
  "cargo": "Segurança",
  "matricula": "001",
  "data_admissao": "2025-01-01",
  "status": "Ativo"
}
```

### PUT `/api/admin/colaboradores/<id>`
**Atualizar colaborador (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "nome_completo": "João Silva Santos",
  "cargo": "Supervisor de Segurança"
}
```

**Response (200):**
```json
{
  "message": "Colaborador atualizado com sucesso"
}
```

### DELETE `/api/admin/colaboradores/<id>`
**Deletar colaborador (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Colaborador deletado com sucesso"
}
```

### GET `/api/admin/escalas`
**Obter escalas mensais (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

**Response (200):**
```json
{
  "ano": 2025,
  "mes": 8,
  "escalas": {
    "condominios": [
      {
        "id": 1,
        "nome": "ZERMATT",
        "plantoes": {
          "diurno": ["João Silva", "Maria Santos"],
          "noturno": ["Pedro Costa", "Ana Lima"]
        }
      }
    ]
  }
}
```

### POST `/api/admin/escalas`
**Salvar escalas mensais (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "ano": 2025,
  "mes": 8,
  "escalas": {
    "condominios": [
      {
        "id": 1,
        "plantoes": {
          "diurno": ["João Silva", "Maria Santos"],
          "noturno": ["Pedro Costa", "Ana Lima"]
        }
      }
    ]
  }
}
```

**Response (200):**
```json
{
  "message": "Escalas salvas com sucesso"
}
```

### POST `/api/admin/tools/justificativa-atestado`
**Gerar justificativa de atestado médico (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "texto_atestado": "Texto do atestado médico"
}
```

**Response (200):**
```json
{
  "justificativa": "Justificativa formatada...",
  "formato": "profissional"
}
```

### POST `/api/admin/tools/justificativa-troca-plantao`
**Gerar justificativa de troca de plantão (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "dados_troca": "Dados da troca de plantão"
}
```

**Response (200):**
```json
{
  "justificativa": "Justificativa formatada...",
  "formato": "profissional"
}
```

### POST `/api/admin/tools/formatar-email`
**Formatar email profissional (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "conteudo": "Conteúdo do email"
}
```

**Response (200):**
```json
{
  "email_formatado": "Email formatado profissionalmente..."
}
```

### GET `/api/admin/dashboard/comparativo`
**Obter dados do dashboard comparativo (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

**Response (200):**
```json
{
  "ano": 2025,
  "mes": 8,
  "dados": {
    "periodo_atual": {
      "ocorrencias": 45,
      "rondas": 67
    },
    "periodo_anterior": {
      "ocorrencias": 38,
      "rondas": 59
    },
    "variacao": {
      "ocorrencias": 18.4,
      "rondas": 13.6
    }
  }
}
```

### GET `/api/admin/dashboard/ocorrencias`
**Obter dados do dashboard de ocorrências (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

**Response (200):**
```json
{
  "ano": 2025,
  "mes": 8,
  "dados": {
    "total_ocorrencias": 45,
    "ocorrencias_por_tipo": [
      {
        "tipo": "Furto",
        "quantidade": 15,
        "percentual": 33.3
      }
    ],
    "ocorrencias_por_condominio": [
      {
        "condominio": "ZERMATT",
        "quantidade": 20,
        "percentual": 44.4
      }
    ]
  }
}
```

### GET `/api/admin/dashboard/rondas`
**Obter dados do dashboard de rondas (apenas admin)**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `ano`: Ano (padrão: ano atual)
- `mes`: Mês (padrão: mês atual)

**Response (200):**
```json
{
  "ano": 2025,
  "mes": 8,
  "dados": {
    "total_rondas": 67,
    "rondas_por_condominio": [
      {
        "condominio": "ZERMATT",
        "quantidade": 30,
        "percentual": 44.8
      }
    ],
    "rondas_por_status": [
      {
        "status": "finalizada",
        "quantidade": 60,
        "percentual": 89.6
      }
    ]
  }
}
```

## 🤖 Analisador IA

### POST `/api/analisador/processar-relatorio`
**Processar relatório usando IA**

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "relatorio_bruto": "Texto do relatório bruto para análise"
}
```

**Response (200):**
```json
{
  "analise": {
    "tipo_sugerido": "Furto",
    "confianca": 0.92,
    "entidades_identificadas": ["João Silva", "Estacionamento"],
    "resumo": "Relatório analisado com sucesso pela IA"
  }
}
```

### GET `/api/analisador/historico`
**Obter histórico de processamentos do usuário**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)

**Response (200):**
```json
{
  "historico": [
    {
      "id": 1,
      "data_processamento": "2025-08-02T15:30:00",
      "relatorio_original": "Texto original...",
      "resultado": "Análise concluída",
      "confianca": 0.92
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 1,
    "total": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

## 🛠️ Utilitários

### GET `/api/users`
**Listar usuários para filtros**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "Luis Royo",
      "email": "luisroyo25@gmail.com",
      "is_supervisor": true,
      "is_admin": true,
      "is_approved": true
    }
  ]
}
```

### GET `/api/condominios`
**Listar condomínios para filtros**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "condominios": [
    {
      "id": 1,
      "nome": "ZERMATT"
    }
  ]
}
```

### GET `/api/colaboradores`
**Listar colaboradores para filtros**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `nome`: Filtrar por nome (opcional)

**Response (200):**
```json
{
  "colaboradores": [
    {
      "id": 1,
      "nome_completo": "João Silva",
      "cargo": "Segurança",
      "matricula": "001"
    }
  ]
}
```

### GET `/api/logradouros_view`
**Listar logradouros para filtros**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `nome`: Filtrar por nome (opcional)

**Response (200):**
```json
{
  "logradouros": [
    {
      "id": 1,
      "nome": "Rua das Flores"
    }
  ]
}
```

## 🔧 Configuração

### Headers Necessários
Para todas as APIs protegidas, incluir:
```
Authorization: Bearer <seu_token_jwt>
Content-Type: application/json
```

### CORS
O backend está configurado para aceitar requisições de:
- `http://localhost:3000` (React)
- `http://localhost:8080` (Vue)
- `http://127.0.0.1:3000`

### Tratamento de Erros
Todas as APIs retornam erros no formato:
```json
{
  "error": "Mensagem de erro",
  "code": "codigo_erro" // opcional
}
```

**Códigos de Status:**
- `200`: Sucesso
- `201`: Criado
- `400`: Bad Request
- `401`: Não autorizado
- `403`: Proibido
- `404`: Não encontrado
- `409`: Conflito
- `500`: Erro interno do servidor

## 📊 Estrutura de Resposta Padrão

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

## 🚀 Exemplos de Uso

### Login e Obter Token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "luisroyo25@gmail.com", "password": "dev123"}'
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
    "tipo_ocorrencia_id": 1,
    "condominio_id": 1,
    "data_ocorrencia": "2025-08-02",
    "hora_ocorrencia": "15:30:00",
    "descricao": "Ocorrência registrada",
    "status": "pendente"
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

### Iniciar Ronda em Tempo Real
```bash
curl -X POST http://localhost:5000/api/ronda-tempo-real/iniciar \
  -H "Authorization: Bearer <seu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "condominio_id": 1,
    "hora_entrada": "18:30:00",
    "observacoes": "Iniciando ronda"
  }'
```

---

**Documento atualizado em:** {{ new Date().toLocaleDateString('pt-BR') }}  
**Versão:** 2.0.0  
**Status:** 100% Sincronizado com a API Flask  
**Próxima atualização:** Após mudanças na API 