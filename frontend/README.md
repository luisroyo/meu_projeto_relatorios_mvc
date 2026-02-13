# 🚀 Frontend React - Sistema de Gestão de Segurança

## 📋 Descrição

Frontend profissional do Sistema de Gestão de Segurança desenvolvido com **React 19**, **TypeScript**, **Material-UI** e **Redux Toolkit**. Interface moderna, responsiva e escalável que se integra perfeitamente com o backend Flask.

## 🛠️ Tecnologias

### **Core**
- **React 19** - Biblioteca JavaScript para interfaces
- **TypeScript** - Tipagem estática para JavaScript
- **Vite** - Build tool rápida e moderna

### **UI/UX**
- **Material-UI (MUI)** - Biblioteca de componentes React
- **Emotion** - CSS-in-JS para estilização
- **React Router DOM** - Roteamento da aplicação

### **Estado e Dados**
- **Redux Toolkit** - Gerenciamento de estado
- **React Redux** - Integração React-Redux
- **Axios** - Cliente HTTP para APIs

### **Formulários e Validação**
- **React Hook Form** - Gerenciamento de formulários
- **Yup** - Validação de schemas
- **@hookform/resolvers** - Integração Yup + React Hook Form

### **Notificações**
- **React Toastify** - Sistema de notificações

### **Utilitários**
- **date-fns** - Manipulação de datas

## 🚀 Como Executar

### **1. Instalar Dependências**
```bash
npm install
```

### **2. Configurar Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto:
```env
VITE_API_URL=http://localhost:5000/api
```

### **3. Executar em Desenvolvimento**
```bash
npm run dev
```

### **4. Build para Produção**
```bash
npm run build
```

### **5. Preview da Build**
```bash
npm run preview
```

## 📁 Estrutura do Projeto

```
src/
├── components/          # Componentes reutilizáveis
│   ├── Layout/         # Layout principal da aplicação
│   └── ProtectedRoute/ # Componente de rota protegida
├── pages/              # Páginas da aplicação
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   ├── AnalisadorPage.tsx
│   ├── OcorrenciasPage.tsx
│   └── RondasPage.tsx
├── store/              # Redux store
│   ├── index.ts        # Configuração do store
│   └── slices/         # Slices do Redux Toolkit
│       ├── authSlice.ts
│       ├── dashboardSlice.ts
│       ├── analisadorSlice.ts
│       ├── ocorrenciaSlice.ts
│       ├── rondaSlice.ts
│       └── uiSlice.ts
├── services/           # Serviços de API
│   └── api.ts         # Configuração Axios e serviços
├── hooks/              # Hooks customizados
│   ├── useAppDispatch.ts
│   ├── useAppSelector.ts
│   └── index.ts
├── types/              # Tipos TypeScript
│   └── index.ts       # Interfaces e tipos
├── utils/              # Utilitários
│   └── theme.ts       # Configuração do tema Material-UI
├── assets/             # Recursos estáticos
├── App.tsx            # Componente principal
└── main.tsx           # Ponto de entrada
```

## 🎨 Design System

### **Cores**
- **Primária**: `#2563eb` (Azul)
- **Secundária**: `#10b981` (Verde)
- **Sucesso**: `#198754`
- **Aviso**: `#ffc107`
- **Erro**: `#dc3545`
- **Info**: `#0dcaf0`

### **Tipografia**
- **Fonte Principal**: Inter (Google Fonts)
- **Hierarquia**: H1-H6 bem definida
- **Responsiva**: Adaptação automática

### **Componentes**
- **Cards**: Sombras suaves e bordas arredondadas
- **Botões**: Sem text-transform, com hover effects
- **Formulários**: Validação visual integrada
- **Navegação**: Responsiva e acessível

## 🔐 Autenticação

### **Fluxo de Autenticação**
1. **Login** - Validação com Yup + React Hook Form
2. **JWT** - Token armazenado no localStorage
3. **Proteção de Rotas** - Componente ProtectedRoute
4. **Auto-refresh** - Carregamento automático do perfil
5. **Logout** - Limpeza completa dos dados

### **Rotas Protegidas**
- `/dashboard` - Dashboard principal
- `/analisador` - Analisador de relatórios
- `/ocorrencias` - Gerenciamento de ocorrências
- `/rondas` - Gerenciamento de rondas

## 📊 Gerenciamento de Estado

### **Redux Toolkit Slices**
- **auth** - Autenticação e usuário
- **dashboard** - Estatísticas e dados do dashboard
- **analisador** - Processamento de relatórios
- **ocorrencia** - Gerenciamento de ocorrências
- **ronda** - Gerenciamento de rondas
- **ui** - Interface (tema, notificações, loading)

### **Hooks Customizados**
- `useAppDispatch()` - Dispatch tipado
- `useAppSelector()` - Selector tipado

## 🌐 Integração com API

### **Configuração Axios**
- **Base URL**: Configurável via variável de ambiente
- **Interceptors**: Token automático e tratamento de erros
- **Timeout**: 10 segundos
- **CORS**: Configurado no backend

### **Serviços Disponíveis**
- `authService` - Login, registro, perfil, logout
- `dashboardService` - Estatísticas, dados recentes
- `analisadorService` - Processamento de relatórios
- `ocorrenciaService` - CRUD de ocorrências
- `rondaService` - CRUD de rondas
- `condominioService` - Dados de condomínios

## 🎯 Funcionalidades

### **✅ Implementadas**
- ✅ **Autenticação JWT** completa
- ✅ **Dashboard** com estatísticas em tempo real
- ✅ **Analisador de Relatórios** com IA
- ✅ **Tema Escuro/Claro** automático
- ✅ **Formulários** com validação
- ✅ **Notificações** toast
- ✅ **Roteamento** protegido
- ✅ **Responsividade** completa

### **🔄 Em Desenvolvimento**
- 🔄 **Gerenciamento de Ocorrências** (CRUD completo)
- 🔄 **Gerenciamento de Rondas** (CRUD completo)
- 🔄 **Relatórios Avançados**
- 🔄 **Upload de Arquivos**
- 🔄 **Painel Administrativo**

## 📱 Responsividade

### **Breakpoints**
- **Mobile**: < 600px
- **Tablet**: 600px - 960px
- **Desktop**: > 960px

### **Características**
- **Mobile-first** design
- **Touch-friendly** interfaces
- **Navegação adaptativa**
- **Componentes flexíveis**

## 🎨 Tema

### **Tema Claro**
- Fundo: `#f5f7fa`
- Cards: `#ffffff`
- Texto: `#1e293b`
- Bordas: `#e2e8f0`

### **Tema Escuro**
- Fundo: `#111827`
- Cards: `#1f2937`
- Texto: `#f9fafb`
- Bordas: `#4b5563`

### **Detecção Automática**
- Baseada nas preferências do sistema
- Persistência no localStorage
- Transições suaves

## 🔧 Configuração

### **Variáveis de Ambiente**
```env
# URL da API do backend
VITE_API_URL=http://localhost:5000/api

# Modo de desenvolvimento
VITE_DEV_MODE=true
```

### **Personalização**
- **Cores**: Edite `src/utils/theme.ts`
- **Tema**: Modifique os objetos `lightTheme` e `darkTheme`
- **API**: Configure em `src/services/api.ts`

## 🚀 Deploy

### **Build de Produção**
```bash
npm run build
```

### **Servir Arquivos Estáticos**
```bash
# Usando serve
npx serve -s dist

# Usando nginx
location / {
    root /path/to/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

### **Configuração de Produção**
1. **API URL**: Configure `VITE_API_URL` para produção
2. **HTTPS**: Configure SSL para segurança
3. **CORS**: Verifique configuração no backend
4. **Cache**: Configure headers de cache

## 🧪 Testes

### **Executar Testes**
```bash
npm run test
```

### **Cobertura**
```bash
npm run test:coverage
```

## 📊 Performance

### **Otimizações**
- **Code Splitting** automático
- **Lazy Loading** de componentes
- **Tree Shaking** para reduzir bundle
- **Compressão** de assets
- **Cache** otimizado

### **Métricas**
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔒 Segurança

### **Medidas Implementadas**
- **HTTPS** obrigatório em produção
- **JWT** com expiração
- **XSS Protection** via React
- **CSRF Protection** via tokens
- **Input Validation** com Yup
- **Output Encoding** automático

## 🤝 Contribuição

### **Padrões de Código**
- **ESLint** configurado
- **Prettier** para formatação
- **TypeScript** strict mode
- **Conventional Commits**

### **Fluxo de Desenvolvimento**
1. **Fork** o projeto
2. **Crie** uma branch para sua feature
3. **Desenvolva** seguindo os padrões
4. **Teste** suas mudanças
5. **Commit** com mensagem descritiva
6. **Push** e abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma **Issue** no repositório
- Consulte a **documentação da API**
- Verifique os **logs do backend**

---

**Desenvolvido com ❤️ e tecnologias modernas para o Sistema de Gestão de Segurança**
