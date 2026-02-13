import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

import type { Ocorrencia } from '../../types';
import { ocorrenciaService } from '../../services/api';

interface OcorrenciaState {
    items: Ocorrencia[];
    currentItem: Ocorrencia | null;
    pagination: {
        total: number;
        page: number;
        per_page: number;
        pages: number;
    };
    loading: boolean;
    error: string | null;
}

const initialState: OcorrenciaState = {
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

export const fetchOcorrencias = createAsyncThunk(
    'ocorrencia/fetchOcorrencias',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await ocorrenciaService.list(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar ocorrências');
        }
    }
);

export const fetchOcorrenciaById = createAsyncThunk(
    'ocorrencia/fetchOcorrenciaById',
    async (id: number, { rejectWithValue }) => {
        try {
            const response = await ocorrenciaService.getById(id);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar ocorrência');
        }
    }
);

const ocorrenciaSlice = createSlice({
    name: 'ocorrencia',
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
            .addCase(fetchOcorrencias.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchOcorrencias.fulfilled, (state, action) => {
                state.loading = false;
                // Handle response
                if (action.payload.ocorrencias) {
                    state.items = action.payload.ocorrencias as any;
                    state.pagination = {
                        total: action.payload.pagination.total,
                        page: action.payload.pagination.page,
                        per_page: action.payload.pagination.per_page,
                        pages: action.payload.pagination.pages,
                    };
                }
                state.error = null;
            })
            .addCase(fetchOcorrencias.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchOcorrenciaById.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchOcorrenciaById.fulfilled, (state, action) => {
                state.loading = false;
                state.currentItem = action.payload;
                state.error = null;
            })
            .addCase(fetchOcorrenciaById.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearError, clearCurrentItem } = ocorrenciaSlice.actions;
export default ocorrenciaSlice.reducer; 