# 📚 Guia de Organização TypeScript

## ✅ Boas Práticas para Projetos TypeScript

### 1. **Consistência de Linguagem**
- ✅ **Use apenas TypeScript** para arquivos `.ts` e `.tsx`
- ❌ **Evite misturar** JavaScript e TypeScript no mesmo projeto
- ✅ **Converta gradualmente** arquivos JS para TS quando necessário

### 2. **Estrutura de Pastas Recomendada**
```
src/
├── components/          # Componentes React (.tsx)
├── pages/              # Páginas da aplicação (.tsx)
├── hooks/              # Custom hooks (.ts)
├── utils/              # Utilitários e helpers (.ts)
├── services/           # Serviços de API (.ts)
├── store/              # Redux store (.ts)
├── types/              # Definições de tipos (.ts)
└── assets/             # Imagens, ícones, etc.
```

### 3. **Convenções de Nomenclatura**
- **Arquivos**: `camelCase.ts` ou `PascalCase.tsx` (para componentes)
- **Interfaces**: `PascalCase` (ex: `UserData`, `ApiResponse`)
- **Tipos**: `PascalCase` (ex: `ThemeType`, `AuthState`)
- **Funções**: `camelCase` (ex: `getUserData`, `clearAuthData`)

### 4. **Organização de Tipos**
```typescript
// types/index.ts
export interface User {
  id: number;
  name: string;
  email: string;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

export type ThemeType = 'light' | 'dark';
```

### 5. **Utilitários TypeScript**
```typescript
// utils/authUtils.ts
export interface AuthData {
  token: string | null;
  user: User | null;
}

export const getAuthData = (): AuthData => {
  // Implementação tipada
};

export const isAuthenticated = (): boolean => {
  // Verificação tipada
};
```

## 🔄 Migração de JavaScript para TypeScript

### Passo 1: Renomear Arquivos
```bash
# Renomear .js para .ts
mv arquivo.js arquivo.ts

# Renomear .jsx para .tsx
mv componente.jsx componente.tsx
```

### Passo 2: Adicionar Tipos
```typescript
// Antes (JavaScript)
function getUser(id) {
  return fetch(`/api/users/${id}`);
}

// Depois (TypeScript)
interface User {
  id: number;
  name: string;
  email: string;
}

async function getUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

### Passo 3: Configurar TypeScript
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": false, // Não permitir arquivos JS
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "exclude": ["node_modules", "static"] // Excluir pasta static
}
```

## 🚫 O que Evitar

### ❌ Misturar JS e TS
```typescript
// ❌ Ruim - Misturando JS e TS
import { getUser } from './userService.js'; // Arquivo JS
import { User } from './types.ts'; // Arquivo TS

// ✅ Bom - Apenas TypeScript
import { getUser } from './userService.ts';
import { User } from './types.ts';
```

### ❌ Tipos Any
```typescript
// ❌ Ruim
const data: any = localStorage.getItem('user');

// ✅ Bom
interface User {
  id: number;
  name: string;
}

const userStr = localStorage.getItem('user');
const user: User | null = userStr ? JSON.parse(userStr) : null;
```

### ❌ Ignorar Erros de Tipo
```typescript
// ❌ Ruim
// @ts-ignore
const result = someFunction();

// ✅ Bom
const result = someFunction() as ExpectedType;
```

## 🛠️ Ferramentas Recomendadas

### 1. **ESLint + TypeScript**
```bash
npm install --save-dev @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

### 2. **Prettier**
```bash
npm install --save-dev prettier
```

### 3. **TypeScript Path Mapping**
```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@components/*": ["components/*"],
      "@utils/*": ["utils/*"]
    }
  }
}
```

## 📝 Checklist de Migração

- [ ] Renomear todos os arquivos `.js` para `.ts`
- [ ] Renomear todos os arquivos `.jsx` para `.tsx`
- [ ] Adicionar tipos para todas as funções
- [ ] Criar interfaces para todos os objetos
- [ ] Configurar `tsconfig.json` adequadamente
- [ ] Atualizar imports para usar extensões `.ts`
- [ ] Remover comentários `@ts-ignore` desnecessários
- [ ] Testar se tudo compila sem erros
- [ ] Verificar se o ESLint está configurado para TypeScript

## 🎯 Benefícios da Migração

1. **Detecção de Erros**: Erros encontrados em tempo de compilação
2. **Melhor IntelliSense**: Autocomplete mais preciso
3. **Refatoração Segura**: Mudanças automáticas e seguras
4. **Documentação**: Tipos servem como documentação
5. **Manutenibilidade**: Código mais fácil de manter
6. **Colaboração**: Equipe trabalha com mais confiança 