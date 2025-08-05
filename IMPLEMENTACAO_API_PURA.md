# 🔧 Implementação Prática: API Pura

## 🚀 Passo a Passo para Separar Backend/Frontend

### 1. Instalar Dependências JWT e CORS

```bash
pip install flask-jwt-extended flask-cors
```

### 2. Configurar JWT no Backend

#### 2.1 Criar arquivo de autenticação JWT
```python
# app/auth/jwt_auth.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.models.user import User

jwt = JWTManager()

def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {"error": "Token expirado"}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {"error": "Token inválido"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {"error": "Token não fornecido"}, 401
```

#### 2.2 Atualizar app/__init__.py
```python
# app/__init__.py (adicionar)
from flask_cors import CORS
from app.auth.jwt_auth import init_jwt

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    
    # Configurações existentes...
    
    # Inicializar JWT
    init_jwt(app)
    
    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
            "supports_credentials": True
        }
    })
    
    # Resto das configurações...
```

### 3. Criar APIs de Autenticação

#### 3.1 app/blueprints/api/auth_routes.py
```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_api_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login que retorna JWT token"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        if not user.is_approved:
            return jsonify({'error': 'Usuário não aprovado'}), 403
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor,
                'is_approved': user.is_approved
            }
        }), 200
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

@auth_api_bp.route('/register', methods=['POST'])
def register():
    """Endpoint de registro de usuário"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'error': 'Email, senha e username são obrigatórios'}), 400
    
    # Verificar se usuário já existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 409
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username já cadastrado'}), 409
    
    # Criar novo usuário
    new_user = User(
        username=data['username'],
        email=data['email'],
        is_approved=False,  # Precisa de aprovação do admin
        is_admin=False,
        is_supervisor=False
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário registrado com sucesso. Aguarde aprovação do administrador.',
            'user_id': new_user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao registrar usuário'}), 500

@auth_api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obter perfil do usuário logado"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_supervisor': user.is_supervisor,
        'is_approved': user.is_approved,
        'date_registered': user.date_registered.isoformat() if user.date_registered else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }), 200

@auth_api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout (cliente deve remover o token)"""
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

@auth_api_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Renovar token (opcional)"""
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': new_token
    }), 200
```

### 4. Registrar Blueprint de Autenticação

#### 4.1 Atualizar app/blueprints/__init__.py
```python
# app/blueprints/__init__.py (adicionar)
from .api.auth_routes import auth_api_bp

def register_blueprints(app):
    # Blueprints existentes...
    
    # API Blueprints
    app.register_blueprint(auth_api_bp)
    app.register_blueprint(api_bp)  # Blueprint API existente
```

### 5. Criar APIs de Dashboard

#### 5.1 app/blueprints/api/dashboard_routes.py
```python
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ocorrencia import Ocorrencia
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

@dashboard_api_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Obter estatísticas do dashboard"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Estatísticas gerais
    total_ocorrencias = Ocorrencia.query.count()
    total_rondas = RondaEsporadica.query.count()
    total_condominios = Condominio.query.count()
    
    # Rondas em andamento hoje
    hoje = datetime.now().date()
    rondas_em_andamento = RondaEsporadica.query.filter(
        RondaEsporadica.data_plantao == hoje,
        RondaEsporadica.status == 'em_andamento'
    ).count()
    
    # Ocorrências do último mês
    um_mes_atras = datetime.now() - timedelta(days=30)
    ocorrencias_ultimo_mes = Ocorrencia.query.filter(
        Ocorrencia.data_ocorrencia >= um_mes_atras
    ).count()
    
    # Rondas do último mês
    rondas_ultimo_mes = RondaEsporadica.query.filter(
        RondaEsporadica.data_plantao >= um_mes_atras
    ).count()
    
    return jsonify({
        'stats': {
            'total_ocorrencias': total_ocorrencias,
            'total_rondas': total_rondas,
            'total_condominios': total_condominios,
            'rondas_em_andamento': rondas_em_andamento,
            'ocorrencias_ultimo_mes': ocorrencias_ultimo_mes,
            'rondas_ultimo_mes': rondas_ultimo_mes
        },
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'is_supervisor': user.is_supervisor
        }
    }), 200

@dashboard_api_bp.route('/recent-ocorrencias', methods=['GET'])
@jwt_required()
def get_recent_ocorrencias():
    """Obter ocorrências recentes"""
    ocorrencias = Ocorrencia.query.order_by(
        Ocorrencia.data_ocorrencia.desc()
    ).limit(10).all()
    
    return jsonify({
        'ocorrencias': [{
            'id': o.id,
            'tipo': o.tipo_ocorrencia.nome if o.tipo_ocorrencia else 'N/A',
            'condominio': o.condominio.nome if o.condominio else 'N/A',
            'data': o.data_ocorrencia.isoformat() if o.data_ocorrencia else None,
            'descricao': o.descricao[:100] + '...' if len(o.descricao) > 100 else o.descricao
        } for o in ocorrencias]
    }), 200

@dashboard_api_bp.route('/recent-rondas', methods=['GET'])
@jwt_required()
def get_recent_rondas():
    """Obter rondas recentes"""
    rondas = RondaEsporadica.query.order_by(
        RondaEsporadica.data_plantao.desc()
    ).limit(10).all()
    
    return jsonify({
        'rondas': [{
            'id': r.id,
            'condominio': r.condominio.nome if r.condominio else 'N/A',
            'data_plantao': r.data_plantao.isoformat() if r.data_plantao else None,
            'escala_plantao': r.escala_plantao,
            'status': r.status,
            'total_rondas': r.total_rondas
        } for r in rondas]
    }), 200
```

### 6. Testar APIs

#### 6.1 Teste de Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "luisroyo25@gmail.com", "password": "dev123"}'
```

#### 6.2 Teste de Dashboard (com token)
```bash
curl -X GET http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 7. Estrutura Final do Backend

```
app/
├── auth/
│   └── jwt_auth.py          # ✅ Configuração JWT
├── blueprints/
│   ├── api/
│   │   ├── auth_routes.py   # ✅ APIs de autenticação
│   │   ├── dashboard_routes.py # ✅ APIs de dashboard
│   │   ├── ronda_tempo_real_routes.py # ✅ Já existe
│   │   ├── ocorrencia_routes.py # ✅ Já existe
│   │   └── admin_routes.py  # 🔄 Criar
│   ├── auth/                # ❌ Remover (substituído por API)
│   ├── admin/               # ❌ Remover (substituído por API)
│   ├── main/                # ❌ Remover (substituído por API)
│   ├── ronda/               # ❌ Remover (substituído por API)
│   └── ocorrencia/          # ❌ Remover (substituído por API)
├── services/                # ✅ Manter (lógica de negócio)
├── models/                  # ✅ Manter (modelos)
├── templates/               # ❌ Remover (frontend separado)
└── static/                  # ❌ Remover (frontend separado)
```

### 8. Próximos Passos

1. **Implementar as APIs acima**
2. **Testar endpoints de autenticação**
3. **Criar frontend básico (React/Vue)**
4. **Implementar login/logout no frontend**
5. **Criar dashboard no frontend**
6. **Migrar funcionalidades gradualmente**

### 9. Exemplo de Frontend Básico (React)

```bash
# Criar projeto React
npx create-react-app frontend-rondas
cd frontend-rondas
npm install axios react-router-dom
```

```javascript
// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const authAPI = {
    login: (email, password) => api.post('/auth/login', { email, password }),
    getProfile: () => api.get('/auth/profile'),
    logout: () => api.post('/auth/logout'),
};

export const dashboardAPI = {
    getStats: () => api.get('/dashboard/stats'),
    getRecentOcorrencias: () => api.get('/dashboard/recent-ocorrencias'),
    getRecentRondas: () => api.get('/dashboard/recent-rondas'),
};

export default api;
```

Esta é a base para começar a separação. Quer que eu implemente alguma parte específica ou tem alguma dúvida sobre o processo? 