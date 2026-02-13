import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
    DashboardMetrics,
    RondaDashboardData,
    OcorrenciaDashboardData,
    ComparativoDashboardData,
    GeminiDashboardData,
    OnlineUsersData
} from '../../types';
import { dashboardService } from '../../services/api';

interface AdminState {
    metrics: DashboardMetrics | null;
    rondaDashboard: RondaDashboardData | null;
    ocorrenciaDashboard: OcorrenciaDashboardData | null;
    comparativoDashboard: ComparativoDashboardData | null;
    geminiDashboard: GeminiDashboardData | null;
    onlineUsers: OnlineUsersData | null;
    loading: boolean;
    error: string | null;
    filters: {
        data_inicio?: string;
        data_fim?: string;
        condominio_id?: number;
        supervisor_id?: number;
        [key: string]: any;
    };
}

const initialState: AdminState = {
    metrics: null,
    rondaDashboard: null,
    ocorrenciaDashboard: null,
    comparativoDashboard: null,
    geminiDashboard: null,
    onlineUsers: null,
    loading: false,
    error: null,
    filters: {},
};

export const fetchMetrics = createAsyncThunk(
    'admin/fetchMetrics',
    async (_, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getMetrics();
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar métricas');
        }
    }
);

export const fetchRondaDashboard = createAsyncThunk(
    'admin/fetchRondaDashboard',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getRondaDashboard(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar dashboard de rondas');
        }
    }
);

export const fetchOcorrenciaDashboard = createAsyncThunk(
    'admin/fetchOcorrenciaDashboard',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getOcorrenciaDashboard(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar dashboard de ocorrências');
        }
    }
);

export const fetchComparativoDashboard = createAsyncThunk(
    'admin/fetchComparativoDashboard',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getComparativoDashboard(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar dashboard comparativo');
        }
    }
);

export const fetchGeminiDashboard = createAsyncThunk(
    'admin/fetchGeminiDashboard',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getGeminiDashboard(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar dashboard Gemini');
        }
    }
);

export const fetchOnlineUsers = createAsyncThunk(
    'admin/fetchOnlineUsers',
    async (_, { rejectWithValue }) => {
        try {
            const response = await dashboardService.getOnlineUsers();
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar usuários online');
        }
    }
);

const adminSlice = createSlice({
    name: 'admin',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        setFilters: (state, action) => {
            state.filters = { ...state.filters, ...action.payload };
        },
        clearFilters: (state) => {
            state.filters = {};
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchMetrics.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchMetrics.fulfilled, (state, action) => {
                state.loading = false;
                state.metrics = action.payload;
                state.error = null;
            })
            .addCase(fetchMetrics.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchRondaDashboard.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchRondaDashboard.fulfilled, (state, action) => {
                state.loading = false;
                state.rondaDashboard = action.payload;
                state.error = null;
            })
            .addCase(fetchRondaDashboard.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchOcorrenciaDashboard.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchOcorrenciaDashboard.fulfilled, (state, action) => {
                state.loading = false;
                state.ocorrenciaDashboard = action.payload;
                state.error = null;
            })
            .addCase(fetchOcorrenciaDashboard.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchComparativoDashboard.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchComparativoDashboard.fulfilled, (state, action) => {
                state.loading = false;
                state.comparativoDashboard = action.payload;
                state.error = null;
            })
            .addCase(fetchComparativoDashboard.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchGeminiDashboard.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchGeminiDashboard.fulfilled, (state, action) => {
                state.loading = false;
                state.geminiDashboard = action.payload;
                state.error = null;
            })
            .addCase(fetchGeminiDashboard.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(fetchOnlineUsers.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchOnlineUsers.fulfilled, (state, action) => {
                state.loading = false;
                state.onlineUsers = action.payload;
                state.error = null;
            })
            .addCase(fetchOnlineUsers.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearError, setFilters, clearFilters } = adminSlice.actions;
export default adminSlice.reducer; 