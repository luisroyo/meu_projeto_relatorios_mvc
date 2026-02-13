import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { RelatorioRequest } from '../../types';
import { analisadorService } from '../../services/api';

interface AnalisadorState {
  historico: any[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
  loading: boolean;
  error: string | null;
}

const initialState: AnalisadorState = {
  historico: [],
  pagination: {
    total: 0,
    page: 1,
    per_page: 10,
    pages: 0,
  },
  loading: false,
  error: null,
};

export const processarRelatorio = createAsyncThunk(
  'analisador/processarRelatorio',
  async (data: RelatorioRequest, { rejectWithValue }) => {
    try {
      const response = await analisadorService.analisarRelatorio(data.relatorio_bruto);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao processar relatório');
    }
  }
);

export const fetchHistorico = createAsyncThunk(
  'analisador/fetchHistorico',
  async ({ page = 1, per_page = 10 }: { page?: number; per_page?: number }, { rejectWithValue }) => {
    try {
      const response = await analisadorService.getHistorico(page, per_page);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar histórico');
    }
  }
);

const analisadorSlice = createSlice({
  name: 'analisador',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(processarRelatorio.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(processarRelatorio.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(processarRelatorio.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchHistorico.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHistorico.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload.historico) {
          state.historico = action.payload.historico;
          state.pagination = {
            total: action.payload.pagination.total,
            page: action.payload.pagination.page,
            per_page: action.payload.pagination.per_page,
            pages: action.payload.pagination.pages,
          };
        }
        state.error = null;
      })
      .addCase(fetchHistorico.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = analisadorSlice.actions;
export default analisadorSlice.reducer; 