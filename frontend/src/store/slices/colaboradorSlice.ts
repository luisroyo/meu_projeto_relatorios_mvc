import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Colaborador, ColaboradoresPagination } from '../../types';
import { colaboradorService } from '../../services/api';

interface ColaboradorState {
    colaboradores: Colaborador[];
    currentColaborador: Colaborador | null;
    pagination: ColaboradoresPagination | null;
    loading: boolean;
    error: string | null;
}

const initialState: ColaboradorState = {
    colaboradores: [],
    currentColaborador: null,
    pagination: null,
    loading: false,
    error: null,
};

export const fetchColaboradores = createAsyncThunk(
    'colaborador/fetchColaboradores',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await colaboradorService.list(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar colaboradores');
        }
    }
);

export const createColaborador = createAsyncThunk(
    'colaborador/createColaborador',
    async (colaboradorData: any, { rejectWithValue }) => {
        try {
            const response = await colaboradorService.create(colaboradorData);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao criar colaborador');
        }
    }
);

export const updateColaborador = createAsyncThunk(
    'colaborador/updateColaborador',
    async ({ id, data }: { id: number; data: any }, { rejectWithValue }) => {
        try {
            const response = await colaboradorService.update(id, data);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao atualizar colaborador');
        }
    }
);

const colaboradorSlice = createSlice({
    name: 'colaborador',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        clearCurrentColaborador: (state) => {
            state.currentColaborador = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchColaboradores.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchColaboradores.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload && action.payload.colaboradores) {
                    state.colaboradores = action.payload.colaboradores as any;
                    state.pagination = action.payload as any;
                }
                state.error = null;
            })
            .addCase(fetchColaboradores.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(createColaborador.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createColaborador.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    state.colaboradores.unshift(action.payload as any);
                }
                state.error = null;
            })
            .addCase(createColaborador.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(updateColaborador.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateColaborador.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    const index = state.colaboradores.findIndex(c => c.id === action.payload.id);
                    if (index !== -1) {
                        state.colaboradores[index] = action.payload as any;
                    }
                }
                state.error = null;
            })
            .addCase(updateColaborador.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearError, clearCurrentColaborador } = colaboradorSlice.actions;
export default colaboradorSlice.reducer; 