# Ocorrências Master App

Aplicativo PWA para geração de relatórios de ocorrências de segurança e registro de rondas.

## 🚀 Tecnologias

- **React 18** - Framework principal
- **TypeScript** - Tipagem estática
- **React Router DOM** - Navegação
- **Axios** - Requisições HTTP
- **Create React App** - Build e desenvolvimento

## 📱 Funcionalidades

### 🔐 Login
- Autenticação simples
- Interface limpa e responsiva

### 📋 Relatórios
- Geração de relatórios de ocorrências
- Formulário completo com validação
- Integração com API Flask

### 🚔 Rondas
- Registro de rondas de segurança
- Controle de horários e rotas
- Observações detalhadas

### 📊 Ocorrências
- Lista de ocorrências registradas
- Visualização detalhada
- Status e histórico

## 🛠️ Instalação

```bash
# Clone o repositório
git clone https://github.com/luisroyo/ocorrencias-master-app.git

# Entre na pasta
cd ocorrencias-master-app

# Instale as dependências
npm install

# Inicie o servidor de desenvolvimento
npm start
```

## 📦 Build

```bash
# Gera build de produção
npm run build

# Serve os arquivos estáticos
npx serve -s build
```

## 🌐 Deploy

O projeto está configurado para deploy no Render.com:

- **Build Command**: `npm install && npm run build`
- **Start Command**: `npx serve -s build -l $PORT`
- **Environment**: `NODE_ENV=production`

## 📁 Estrutura do Projeto

```
src/
├── components/
│   └── Layout.tsx          # Layout principal com navegação
├── pages/
│   ├── Login.tsx           # Página de login
│   ├── Relatorio.tsx       # Gerador de relatórios
│   ├── Ronda.tsx           # Registro de rondas
│   ├── OccurrencesList.tsx # Lista de ocorrências
│   └── OccurrenceDetail.tsx # Detalhes da ocorrência
├── App.tsx                 # Componente principal
├── index.tsx               # Ponto de entrada
└── index.css               # Estilos globais

public/
├── assets/                 # Ícones e imagens
├── index.html              # HTML principal
├── manifest.json           # Manifest PWA
└── sw.js                   # Service Worker
```

## 🔧 Configuração da API

O aplicativo se conecta com uma API Flask local:

- **URL Base**: `http://localhost:5000`
- **Endpoints**:
  - `POST /api/relatorio` - Gerar relatório
  - `POST /api/ronda` - Registrar ronda
  - `GET /api/ocorrencias` - Listar ocorrências
  - `GET /api/ocorrencias/:id` - Detalhes da ocorrência

## 📱 PWA

O aplicativo funciona como Progressive Web App (PWA):

- ✅ Instalável
- ✅ Offline capability
- ✅ Service Worker
- ✅ Manifest otimizado
- ✅ Ícones responsivos

## 🎨 Design

- Interface limpa e moderna
- Cores: Azul (#1e3a8a) como cor principal
- Responsivo para mobile e desktop
- Componentes reutilizáveis

## 📄 Licença

Este projeto é privado e de uso interno. 