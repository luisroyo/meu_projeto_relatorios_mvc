# 🚀 Plano de Separação Backend/Frontend

## 📊 Situação Atual

### ✅ Pontos Fortes
- **APIs já existentes**: `app/blueprints/api/` com endpoints robustos
- **Serviços bem estruturados**: `app/services/` com lógica de negócio separada
- **Modelos centralizados**: `app/models/` com SQLAlchemy
- **Autenticação configurada**: Flask-Login funcionando
- **CORS provavelmente configurado**

### 📁 Estrutura Atual
```
app/
├── blueprints/
│   ├── api/           # ✅ APIs já existem
│   ├── auth/          # 🔄 Precisa ser convertido para API
│   ├── admin/         # 🔄 Precisa ser convertido para API
│   ├── main/          # 🔄 Precisa ser convertido para API
│   ├── ronda/         # 🔄 Precisa ser convertido para API
│   └── ocorrencia/    # 🔄 Precisa ser convertido para API
├── templates/         # ❌ Será removido (frontend separado)
├── static/           # ❌ Será removido (frontend separado)
└── services/         # ✅ Manter (lógica de negócio)
```

## 🎯 Objetivos

1. **Backend puro**: Apenas APIs REST/JSON
2. **Frontend independente**: React/Vue/Angular ou PWA
3. **Autenticação JWT**: Substituir Flask-Login por tokens
4. **CORS configurado**: Permitir acesso do frontend
5. **Documentação OpenAPI**: Swagger/ReDoc

## 📋 Plano de Implementação

### Fase 1: Preparar Backend como API Pura

#### 1.1 Configurar Autenticação JWT
```python
# app/auth/jwt_auth.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import timedelta

jwt = JWTManager()

def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = 'sua-chave-secreta'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()
```

#### 1.2 Converter Rotas Web para APIs
```python
# app/blueprints/api/auth_routes.py
@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor
            }
        }), 200
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

@api_bp.route('/auth/register', methods=['POST'])
def register():
    # Lógica de registro
    pass

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_supervisor': user.is_supervisor
    })
```

#### 1.3 Converter Rotas de Dashboard
```python
# app/blueprints/api/dashboard_routes.py
@api_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    # Retornar estatísticas em JSON
    return jsonify({
        'total_ocorrencias': ocorrencias_count,
        'total_rondas': rondas_count,
        'rondas_em_andamento': rondas_em_andamento_count
    })

@api_bp.route('/dashboard/ocorrencias', methods=['GET'])
@jwt_required()
def get_ocorrencias_dashboard():
    # Retornar dados de ocorrências para dashboard
    pass
```

#### 1.4 Configurar CORS
```python
# app/__init__.py
from flask_cors import CORS

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    
    # Configurar CORS para frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
```

### Fase 2: Criar Frontend Independente

#### 2.1 Estrutura do Frontend
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── rondas/
│   │   ├── ocorrencias/
│   │   └── admin/
│   ├── services/
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── storage.js
│   ├── pages/
│   └── utils/
├── public/
└── package.json
```

#### 2.2 Serviço de API
```javascript
// frontend/src/services/api.js
const API_BASE_URL = 'http://localhost:5000/api';

class ApiService {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` }),
                ...options.headers
            },
            ...options
        };

        const response = await fetch(`${this.baseURL}${endpoint}`, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response.json();
    }

    // Auth endpoints
    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async getProfile() {
        return this.request('/auth/profile');
    }

    // Rondas endpoints
    async getRondasEmAndamento() {
        return this.request('/ronda-tempo-real/em-andamento');
    }

    async iniciarRonda(condominioId, horaEntrada, observacoes) {
        return this.request('/ronda-tempo-real/iniciar', {
            method: 'POST',
            body: JSON.stringify({
                condominio_id: condominioId,
                hora_entrada: horaEntrada,
                observacoes: observacoes
            })
        });
    }

    // Dashboard endpoints
    async getDashboardStats() {
        return this.request('/dashboard/stats');
    }
}

export default new ApiService();
```

#### 2.3 Componente de Login
```javascript
// frontend/src/components/auth/Login.js
import React, { useState } from 'react';
import apiService from '../../services/api';

const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            const response = await apiService.login(email, password);
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('user', JSON.stringify(response.user));
            onLogin(response.user);
        } catch (error) {
            setError('Credenciais inválidas');
        }
    };

    return (
        <div className="login-container">
            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <input
                    type="password"
                    placeholder="Senha"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                <button type="submit">Entrar</button>
                {error && <div className="error">{error}</div>}
            </form>
        </div>
    );
};

export default Login;
```

### Fase 3: Migração Gradual

#### 3.1 Estratégia de Migração
1. **Manter aplicação atual funcionando**
2. **Criar APIs paralelas** sem quebrar o frontend atual
3. **Desenvolver novo frontend** em paralelo
4. **Testar e validar** nova arquitetura
5. **Migrar gradualmente** funcionalidades

#### 3.2 Endpoints Prioritários
1. **Autenticação** (`/api/auth/*`)
2. **Rondas em Tempo Real** (`/api/ronda-tempo-real/*`)
3. **Dashboard** (`/api/dashboard/*`)
4. **Ocorrências** (`/api/ocorrencias/*`)
5. **Admin** (`/api/admin/*`)

## 🔧 Configurações Necessárias

### Backend (Flask)
```python
# requirements.txt (adicionar)
flask-jwt-extended==4.5.2
flask-cors==4.0.0
```

### Frontend (React/Vue)
```json
// package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.0"
  }
}
```

## 📊 Benefícios da Separação

### ✅ Vantagens
- **Reutilização**: Backend pode ser usado por múltiplos frontends
- **Escalabilidade**: Frontend e backend podem escalar independentemente
- **Manutenibilidade**: Código mais organizado e focado
- **Performance**: Frontend otimizado para interface
- **Flexibilidade**: Pode usar diferentes tecnologias frontend

### ⚠️ Considerações
- **Complexidade**: Mais arquitetura para gerenciar
- **CORS**: Configuração adicional necessária
- **Autenticação**: JWT mais complexo que sessões
- **Deploy**: Dois sistemas para deployar

## 🚀 Próximos Passos

1. **Implementar autenticação JWT**
2. **Converter rotas web para APIs**
3. **Configurar CORS**
4. **Criar estrutura do frontend**
5. **Desenvolver componentes principais**
6. **Testar integração**
7. **Migrar gradualmente**

## 📚 Recursos Úteis

- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
- [React Documentation](https://reactjs.org/docs/)
- [Vue.js Documentation](https://vuejs.org/guide/) 