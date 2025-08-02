# 📚 Documentação das APIs

## 🔐 Autenticação

### POST `/api/auth/login`
**Login e obtenção de token JWT**

**Request Body:**
```json
{
  "email": "luisroyo25@gmail.com",
  "password": "dev123"
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
    "total_condominios": 8,
    "rondas_em_andamento": 3,
    "ocorrencias_ultimo_mes": 25,
    "rondas_ultimo_mes": 45
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
      "observacoes": "Ronda iniciada",
      "tempo_decorrido": "45min"
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

## 🚨 Ocorrências

### GET `/api/ocorrencias`
**Listar ocorrências**

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `per_page`: Itens por página (padrão: 10)
- `condominio_id`: Filtrar por condomínio
- `tipo_id`: Filtrar por tipo de ocorrência

**Response (200):**
```json
{
  "ocorrencias": [...],
  "pagination": {
    "page": 1,
    "pages": 5,
    "total": 50,
    "per_page": 10
  }
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

## 🚀 Próximos Endpoints a Implementar

1. **APIs de Admin** (`/api/admin/*`)
2. **APIs de Ocorrências** (`/api/ocorrencias/*`)
3. **APIs de Relatórios** (`/api/relatorios/*`)
4. **APIs de Usuários** (`/api/users/*`) 