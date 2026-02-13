import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { EscalaMensal, EscalaFormData } from '../../types';
import { escalaService } from '../../services/api';

interface EscalaState {
    escalas: EscalaMensal[];
    currentEscala: EscalaMensal | null;
    loading: boolean;
    error: string | null;
}

const initialState: EscalaState = {
    escalas: [],
    currentEscala: null,
    loading: false,
    error: null,
};

export const fetchEscalas = createAsyncThunk(
    'escala/fetchEscalas',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await escalaService.list(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar escalas');
        }
    }
);

export const createEscala = createAsyncThunk(
    'escala/createEscala',
    async (escalaData: EscalaFormData, { rejectWithValue }) => {
        try {
            const response = await escalaService.create(escalaData);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao criar escala');
        }
    }
);

export const updateEscala = createAsyncThunk(
    'escala/updateEscala',
    async ({ id, data }: { id: number; data: EscalaFormData }, { rejectWithValue }) => {
        try {
            const response = await escalaService.update(id, data);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao atualizar escala');
        }
    }
);

const escalaSlice = createSlice({
    name: 'escala',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        clearCurrentEscala: (state) => {
            state.currentEscala = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchEscalas.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchEscalas.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    state.escalas = action.payload;
                }
                state.error = null;
            })
            .addCase(fetchEscalas.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(createEscala.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createEscala.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    state.escalas.unshift(action.payload);
                }
                state.error = null;
            })
            .addCase(createEscala.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(updateEscala.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateEscala.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    const index = state.escalas.findIndex(e => e.id === action.payload.id);
                    if (index !== -1) {
                        state.escalas[index] = action.payload;
                    }
                }
                state.error = null;
            })
            .addCase(updateEscala.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearError, clearCurrentEscala } = escalaSlice.actions;
export default escalaSlice.reducer; 