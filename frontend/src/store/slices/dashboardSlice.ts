import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { DashboardStats, Ocorrencia, Ronda } from '../../types';
import { dashboardService } from '../../services/api';

interface DashboardState {
  stats: DashboardStats | null;
  recentOcorrencias: Ocorrencia[];
  recentRondas: Ronda[];
  loading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  stats: null,
  recentOcorrencias: [],
  recentRondas: [],
  loading: false,
  error: null,
};

export const fetchDashboardStats = createAsyncThunk(
  'dashboard/fetchDashboardStats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await dashboardService.getStats();
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar estatísticas');
    }
  }
);

export const fetchRecentOcorrencias = createAsyncThunk(
  'dashboard/fetchRecentOcorrencias',
  async (_, { rejectWithValue }) => {
    try {
      const response = await dashboardService.getRecentOcorrencias();
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar ocorrências recentes');
    }
  }
);

export const fetchRecentRondas = createAsyncThunk(
  'dashboard/fetchRecentRondas',
  async (_, { rejectWithValue }) => {
    try {
      const response = await dashboardService.getRecentRondas();
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar rondas recentes');
    }
  }
);

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action) => {
        state.loading = false;
        // Transform the API response to match DashboardStats structure
        if (action.payload && typeof action.payload === 'object') {
          state.stats = {
            stats: {
              total_ocorrencias: action.payload.total_ocorrencias || 0,
              total_rondas: action.payload.total_rondas || 0,
              total_condominios: 0, // Not provided by API
              rondas_em_andamento: 0, // Not provided by API
              ocorrencias_ultimo_mes: action.payload.ocorrencias_hoje || 0,
              rondas_ultimo_mes: action.payload.rondas_hoje || 0,
            },
            user: {
              id: 0,
              username: '',
              is_admin: false,
              is_supervisor: false,
            },
          };
        } else {
          state.stats = null;
        }
        state.error = null;
      })
      .addCase(fetchDashboardStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchRecentOcorrencias.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRecentOcorrencias.fulfilled, (state, action) => {
        state.loading = false;
        // Transform the API response to match Ocorrencia structure
        if (Array.isArray(action.payload)) {
          state.recentOcorrencias = action.payload.map((item: any) => ({
            id: item.id,
            tipo: item.tipo,
            condominio: item.condominio,
            data_hora_ocorrencia: item.data_hora_ocorrencia,
            descricao: '',
            status: item.status,
            endereco: '',
            data_criacao: '',
            registrado_por: '',
            supervisor: '',
            registrado_por_user_id: 0,
          }));
        } else {
          state.recentOcorrencias = [];
        }
        state.error = null;
      })
      .addCase(fetchRecentOcorrencias.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchRecentRondas.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRecentRondas.fulfilled, (state, action) => {
        state.loading = false;
        // Transform the API response to match Ronda structure
        if (Array.isArray(action.payload)) {
          state.recentRondas = action.payload.map((item: any) => ({
            id: item.id,
            data_hora_inicio: item.data_inicio,
            data_hora_fim: item.data_fim,
            log_ronda_bruto: '',
            condominio_id: 0,
            user_id: 0,
            status: item.status,
          }));
        } else {
          state.recentRondas = [];
        }
        state.error = null;
      })
      .addCase(fetchRecentRondas.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = dashboardSlice.actions;
export default dashboardSlice.reducer; 