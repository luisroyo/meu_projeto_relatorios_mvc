import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { colaboradorService } from '../../services/api';

interface Colaborador {
    id: number;
    nome_completo: string;
    cargo: string;
    matricula: string;
    data_admissao?: string;
    status: string;
}

interface ColaboradorState {
    colaboradores: Colaborador[];
    loading: boolean;
    error: string | null;
    pagination: {
        page: number;
        pages: number;
        total: number;
        per_page: number;
    };
    filters: {
        search: string;
        status: string;
    };
}

const initialState: ColaboradorState = {
    colaboradores: [],
    loading: false,
    error: null,
    pagination: {
        page: 1,
        pages: 1,
        total: 0,
        per_page: 10,
    },
    filters: {
        search: '',
        status: 'Ativo',
    },
};

export const fetchColaboradores = createAsyncThunk(
    'colaborador/fetchColaboradores',
    async (params: { page?: number; per_page?: number; search?: string; status?: string }, { rejectWithValue }) => {
        try {
            const response = await colaboradorService.list(params);
            return response;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Erro ao carregar colaboradores');
        }
    }
);

export const createColaborador = createAsyncThunk(
    'colaborador/createColaborador',
    async (data: any, { rejectWithValue, dispatch }) => {
        try {
            await colaboradorService.create(data);
            return;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Erro ao criar colaborador');
        }
    }
);

export const updateColaborador = createAsyncThunk(
    'colaborador/updateColaborador',
    async ({ id, data }: { id: number; data: any }, { rejectWithValue }) => {
        try {
            await colaboradorService.update(id, data);
            return;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Erro ao atualizar colaborador');
        }
    }
);

export const deleteColaborador = createAsyncThunk(
    'colaborador/deleteColaborador',
    async (id: number, { rejectWithValue }) => {
        try {
            await colaboradorService.delete(id);
            return id;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Erro ao excluir colaborador');
        }
    }
);

const colaboradorSlice = createSlice({
    name: 'colaborador',
    initialState,
    reducers: {
        setFilters: (state, action: PayloadAction<Partial<ColaboradorState['filters']>>) => {
            state.filters = { ...state.filters, ...action.payload };
            state.pagination.page = 1; // Reset page on filter change
        },
        clearFilters: (state) => {
            state.filters = initialState.filters;
            state.pagination.page = 1;
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch
            .addCase(fetchColaboradores.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchColaboradores.fulfilled, (state, action) => {
                state.loading = false;
                state.colaboradores = action.payload.colaboradores;
                state.pagination = action.payload.pagination;
            })
            .addCase(fetchColaboradores.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // Create
            .addCase(createColaborador.fulfilled, (state) => {
                // Nada específico além de parar loading se houvesse
            })
            // Update
            .addCase(updateColaborador.fulfilled, (state) => {
                // Nada específico
            })
            // Delete
            .addCase(deleteColaborador.fulfilled, (state, action) => {
                state.colaboradores = state.colaboradores.filter(c => c.id !== action.payload);
            });
    },
});

export const { setFilters, clearFilters } = colaboradorSlice.actions;
export default colaboradorSlice.reducer;