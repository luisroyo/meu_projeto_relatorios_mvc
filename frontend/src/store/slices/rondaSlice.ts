import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

import type { Ronda } from '../../types';
import { rondaService } from '../../services/api';

interface RondaState {
  items: Ronda[];
  currentItem: Ronda | null;
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
  loading: boolean;
  error: string | null;
}

const initialState: RondaState = {
  items: [],
  currentItem: null,
  pagination: {
    total: 0,
    page: 1,
    per_page: 10,
    pages: 0,
  },
  loading: false,
  error: null,
};

export const fetchRondas = createAsyncThunk(
  'ronda/fetchRondas',
  async ({ filters }: { filters?: any }, { rejectWithValue }) => {
    try {
      const response = await rondaService.list(filters);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar rondas');
    }
  }
);

export const fetchRondaById = createAsyncThunk(
  'ronda/fetchRondaById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await rondaService.getById(id);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar ronda');
    }
  }
);

export const createRonda = createAsyncThunk(
  'ronda/createRonda',
  async (rondaData: any, { rejectWithValue }) => {
    try {
      const response = await rondaService.create(rondaData);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao criar ronda');
    }
  }
);

const rondaSlice = createSlice({
  name: 'ronda',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentItem: (state) => {
      state.currentItem = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRondas.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRondas.fulfilled, (state, action) => {
        state.loading = false;
        // Handle response
        if (action.payload.rondas) {
          state.items = action.payload.rondas as any;
          state.pagination = {
            total: action.payload.pagination.total,
            page: action.payload.pagination.page,
            per_page: action.payload.pagination.per_page,
            pages: action.payload.pagination.pages,
          };
        }
        state.error = null;
      })
      .addCase(fetchRondas.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchRondaById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRondaById.fulfilled, (state, action) => {
        state.loading = false;
        // Ensure the payload has all required Ronda properties
        const rondaData = action.payload as any;
        state.currentItem = {
          id: rondaData.id,
          data_hora_inicio: rondaData.data_hora_inicio || rondaData.data_inicio,
          data_hora_fim: rondaData.data_hora_fim || rondaData.data_fim,
          log_ronda_bruto: rondaData.log_ronda_bruto || '',
          relatorio_processado: rondaData.relatorio_processado,
          condominio_id: rondaData.condominio_id,
          user_id: rondaData.user_id || rondaData.supervisor_id,
          supervisor_id: rondaData.supervisor_id,
          turno_ronda: rondaData.turno_ronda,
          escala_plantao: rondaData.escala_plantao,
          data_plantao_ronda: rondaData.data_plantao_ronda,
          total_rondas_no_log: rondaData.total_rondas_no_log,
          primeiro_evento_log_dt: rondaData.primeiro_evento_log_dt,
          ultimo_evento_log_dt: rondaData.ultimo_evento_log_dt,
          duracao_total_rondas_minutos: rondaData.duracao_total_rondas_minutos,
          tipo: rondaData.tipo,
          condominio: rondaData.condominio,
          criador: rondaData.criador,
          supervisor: rondaData.supervisor,
        } as Ronda;
        state.error = null;
      })
      .addCase(fetchRondaById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(createRonda.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createRonda.fulfilled, (state, _action) => {
        state.loading = false;
        // state.items.unshift(action.payload); // Response only contains ID, need to fetch full object
        state.error = null;
      })
      .addCase(createRonda.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, clearCurrentItem } = rondaSlice.actions;
export default rondaSlice.reducer; 