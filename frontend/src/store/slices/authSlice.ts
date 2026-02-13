import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { User, LoginRequest, RegisterRequest } from '../../types';
import { authService } from '../../services/api';

// Estado inicial
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

// Função para verificar se há dados válidos no localStorage
const getInitialAuthState = (): AuthState => {
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');

  let user = null;
  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch (error) {
      console.error('Erro ao parsear usuário do localStorage:', error);
      localStorage.removeItem('user');
    }
  }

  // Só considerar autenticado se tiver tanto token quanto usuário
  const isAuthenticated = !!(token && user);

  console.log('AuthSlice - Estado inicial:', {
    hasToken: !!token,
    hasUser: !!user,
    isAuthenticated
  });

  return {
    user,
    token,
    isAuthenticated,
    loading: false,
    error: null,
  };
};

const initialState: AuthState = getInitialAuthState();

// Thunks assíncronos
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      console.log('Iniciando login com credenciais:', credentials);
      const response = await authService.login(credentials.email, credentials.password);
      console.log('Resposta do login:', response);
      console.log('Token recebido:', response.access_token);

      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      console.log('Token salvo no localStorage:', localStorage.getItem('access_token'));
      return response;
    } catch (error) {
      console.error('Erro no login:', error);
      return rejectWithValue(error instanceof Error ? error.message : 'Erro no login');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (userData: RegisterRequest, { rejectWithValue }) => {
    try {
      const response = await authService.register(userData.username, userData.email, userData.password);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro no registro');
    }
  }
);

export const getProfile = createAsyncThunk(
  'auth/getProfile',
  async (_, { rejectWithValue }) => {
    try {
      const user = await authService.getProfile();
      return user;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar perfil');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      return null;
    } catch (error) {
      // Mesmo com erro, limpar dados locais
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      return rejectWithValue(error instanceof Error ? error.message : 'Erro no logout');
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
        localStorage.setItem('user', JSON.stringify(state.user));
      }
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        state.error = null;
        // Salvar token e usuário no localStorage
        localStorage.setItem('access_token', action.payload.access_token);
        localStorage.setItem('user', JSON.stringify(action.payload.user));
        console.log('Login realizado com sucesso:', action.payload.user);
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Get Profile
    builder
      .addCase(getProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
        console.log('Perfil carregado com sucesso:', action.payload);
      })
      .addCase(getProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        console.log('getProfile rejeitado:', action.payload);
        // Se não conseguir carregar o perfil, limpar dados de autenticação
        console.log('Token inválido detectado, limpando estado');
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      });

    // Logout
    builder
      .addCase(logout.pending, (state) => {
        state.loading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        state.loading = false;
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.error = null;
      })
      .addCase(logout.rejected, (state) => {
        state.loading = false;
        // Mesmo com erro, limpar o estado
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError, setUser, updateUser } = authSlice.actions;
export default authSlice.reducer; 