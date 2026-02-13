# 🚀 Guia de Integração da API com Frontend

## 📋 Visão Geral

Este documento descreve como configurar e integrar a API REST do sistema de gestão de segurança com o frontend, garantindo funcionamento perfeito e performance otimizada.

## 🏗️ Estrutura da API

### **Blueprint Principal**
- **URL Base**: `/api`
- **Blueprint**: `api_bp` em `backend/app/blueprints/api/__init__.py`
- **Módulos**: 9 módulos especializados

### **Módulos Disponíveis**
1. **`auth_routes.py`** - Autenticação JWT
2. **`ocorrencia_routes.py`** - Gestão de ocorrências
3. **`ronda_routes.py`** - Gestão de rondas
4. **`admin_routes.py`** - Administração do sistema
5. **`dashboard_routes.py`** - Dashboards e relatórios
6. **`ronda_tempo_real_routes.py`** - Rondas em tempo real
7. **`ronda_esporadica_routes.py`** - Rondas esporádicas
8. **`analisador_routes.py`** - Análise com IA
9. **`config_routes.py`** - Configurações do sistema

## 🔐 Configuração de Autenticação

### **JWT Token**
```javascript
// Frontend: Armazenar token após login
const token = response.data.access_token;
localStorage.setItem('jwt_token', token);

// Frontend: Incluir em todas as requisições
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

### **Refresh Token (Recomendado)**
```javascript
// Interceptor para renovar token automaticamente
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.status === 401) {
      // Tentar renovar token
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return axios.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

## 🌐 Configuração CORS

### **Backend (já configurado)**
```python
# backend/app/__init__.py
allowed_origins = [
    "http://localhost:5173", "http://localhost:5174",
    "http://localhost:8081", "http://localhost:3000",
    "http://127.0.0.1:5173", "http://127.0.0.1:5174",
    "https://processador-relatorios-ia.onrender.com",
    "https://ocorrencias-master-app.onrender.com"
]

CORS(app, origins=allowed_origins, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
```

### **Frontend: Configuração Axios**
```javascript
// config/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false // Importante para CORS
});

export default api;
```

## 📡 Endpoints Principais

### **1. Autenticação**
```javascript
// Login
POST /api/auth/login
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}

// Resposta
{
  "access_token": "jwt_token_aqui",
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@exemplo.com",
    "is_admin": false,
    "is_supervisor": true,
    "is_approved": true
  }
}
```

### **2. Ocorrências**
```javascript
// Listar com filtros
GET /api/ocorrencias?page=1&per_page=10&status=Registrada&condominio_id=1

// Criar nova
POST /api/ocorrencias
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

### **3. Rondas**
```javascript
// Listar rondas
GET /api/rondas?page=1&per_page=10&condominio_id=1

// Processar arquivo WhatsApp
POST /api/rondas/process-whatsapp
// FormData com arquivo
```

### **4. Dashboard**
```javascript
// Estatísticas gerais
GET /api/dashboard/stats

// Ocorrências recentes
GET /api/dashboard/recent-ocorrencias

// Rondas recentes
GET /api/dashboard/recent-rondas
```

## 🔧 Configurações de Frontend

### **1. Variáveis de Ambiente**
```bash
# .env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_APP_NAME=Sistema de Gestão de Segurança
REACT_APP_VERSION=1.0.0
```

### **2. Interceptors para Tratamento de Erros**
```javascript
// services/apiService.js
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirecionar para login
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    }
    
    if (error.response?.status === 403) {
      // Usuário sem permissão
      toast.error('Acesso negado');
    }
    
    if (error.response?.status === 500) {
      // Erro interno do servidor
      toast.error('Erro interno do servidor');
    }
    
    return Promise.reject(error);
  }
);
```

### **3. Hook para Autenticação**
```javascript
// hooks/useAuth.js
import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('jwt_token'));

  useEffect(() => {
    if (token) {
      // Verificar token
      api.get('/auth/profile')
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('jwt_token');
          setToken(null);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user } = response.data;
    
    localStorage.setItem('jwt_token', access_token);
    setToken(access_token);
    setUser(user);
    
    return user;
  };

  const logout = () => {
    localStorage.removeItem('jwt_token');
    setToken(null);
    setUser(null);
  };

  return { user, loading, login, logout, isAuthenticated: !!user };
};
```

## 📊 Tratamento de Dados

### **1. Paginação Padrão**
```javascript
// Todas as listas seguem este padrão
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

### **2. Filtros Dinâmicos**
```javascript
// Exemplo de filtros para ocorrências
const filters = {
  status: 'Registrada',
  condominio_id: 1,
  supervisor_id: 2,
  tipo_id: 3,
  data_inicio: '2024-01-01',
  data_fim: '2024-12-31',
  texto_relatorio: 'busca'
};

const queryString = new URLSearchParams(filters).toString();
const response = await api.get(`/ocorrencias?${queryString}`);
```

### **3. Upload de Arquivos**
```javascript
// Para processamento de rondas
const formData = new FormData();
formData.append('file', file);

const response = await api.post('/rondas/process-whatsapp', formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});
```

## 🚀 Otimizações de Performance

### **1. Cache de Dados**
```javascript
// services/cacheService.js
class CacheService {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5 minutos
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
}
```

### **2. Debounce para Filtros**
```javascript
// hooks/useDebounce.js
import { useState, useEffect } from 'react';

export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};
```

### **3. Lazy Loading de Componentes**
```javascript
// App.js
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Ocorrencias = lazy(() => import('./pages/Ocorrencias'));

function App() {
  return (
    <Suspense fallback={<div>Carregando...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/ocorrencias" element={<Ocorrencias />} />
      </Routes>
    </Suspense>
  );
}
```

## 🔒 Segurança

### **1. Validação de Dados**
```javascript
// utils/validation.js
export const validateOcorrencia = (data) => {
  const errors = {};
  
  if (!data.relatorio_final?.trim()) {
    errors.relatorio_final = 'Relatório é obrigatório';
  }
  
  if (!data.condominio_id) {
    errors.condominio_id = 'Condomínio é obrigatório';
  }
  
  if (!data.ocorrencia_tipo_id) {
    errors.ocorrencia_tipo_id = 'Tipo de ocorrência é obrigatório';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
```

### **2. Sanitização de Inputs**
```javascript
// utils/sanitization.js
export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .trim();
};
```

## 📱 Responsividade e UX

### **1. Loading States**
```javascript
// Componente de loading
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);
```

### **2. Error Boundaries**
```javascript
// ErrorBoundary.js
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center p-8">
          <h2>Algo deu errado</h2>
          <button onClick={() => window.location.reload()}>
            Recarregar página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### **3. Toast Notifications**
```javascript
// services/notificationService.js
import { toast } from 'react-toastify';

export const showSuccess = (message) => {
  toast.success(message, {
    position: "top-right",
    autoClose: 3000,
  });
};

export const showError = (message) => {
  toast.error(message, {
    position: "top-right",
    autoClose: 5000,
  });
};
```

## 🧪 Testes

### **1. Testes de API**
```javascript
// tests/api.test.js
import api from '../services/api';

describe('API Tests', () => {
  test('should authenticate user', async () => {
    const response = await api.post('/auth/login', {
      email: 'test@example.com',
      password: 'password123'
    });
    
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('access_token');
  });
});
```

### **2. Mock Service Worker**
```javascript
// mocks/handlers.js
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/ocorrencias', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        data: mockOcorrencias,
        pagination: {
          page: 1,
          pages: 1,
          per_page: 10,
          total: mockOcorrencias.length,
          has_next: false,
          has_prev: false
        }
      })
    );
  }),
];
```

## 📋 Checklist de Implementação

### **Backend (✅ Já configurado)**
- [x] CORS configurado
- [x] JWT implementado
- [x] Rotas da API criadas
- [x] Validação de dados
- [x] Tratamento de erros
- [x] Logging configurado

### **Frontend (Para implementar)**
- [ ] Configuração do Axios
- [ ] Interceptors de autenticação
- [ ] Hook de autenticação
- [ ] Tratamento de erros global
- [ ] Loading states
- [ ] Cache de dados
- [ ] Validação de formulários
- [ ] Testes unitários
- [ ] Error boundaries
- [ ] Toast notifications

## 🎯 Próximos Passos

1. **Implementar frontend** seguindo este guia
2. **Configurar variáveis de ambiente**
3. **Implementar autenticação JWT**
4. **Criar componentes reutilizáveis**
5. **Implementar cache e otimizações**
6. **Adicionar testes**
7. **Configurar CI/CD**

## 📞 Suporte

Para dúvidas ou problemas:
- **Documentação da API**: `backend/app/blueprints/api/API_DOCUMENTATION.md`
- **Logs**: Verificar `backend/logs/`
- **Issues**: Criar issue no repositório

---

**Versão**: 1.0.0  
**Última atualização**: Agosto 2025  
**Autor**: Sistema de Gestão de Segurança
