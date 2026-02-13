import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

import type { User } from '../../types';
import { userService } from '../../services/api';

interface UserManagementState {
    users: User[];
    currentUser: User | null;
    pagination: {
        total: number;
        page: number;
        per_page: number;
        pages: number;
    };
    loading: boolean;
    error: string | null;
    filters: {
        search: string;
        status: string;
        role: string;
    };
}

const initialState: UserManagementState = {
    users: [],
    currentUser: null,
    pagination: {
        total: 0,
        page: 1,
        per_page: 10,
        pages: 0,
    },
    loading: false,
    error: null,
    filters: {
        search: '',
        status: '',
        role: '',
    },
};

export const fetchUsers = createAsyncThunk(
    'userManagement/fetchUsers',
    async ({ filters }: { filters?: any }, { rejectWithValue }) => {
        try {
            const response = await userService.list(filters);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao carregar usuários');
        }
    }
);

export const updateUserStatus = createAsyncThunk(
    'userManagement/updateUserStatus',
    async ({ userId, isApproved }: { userId: number; isApproved: boolean }, { rejectWithValue }) => {
        try {
            const response = await userService.updateStatus(userId, isApproved);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao atualizar status do usuário');
        }
    }
);

export const approveUser = createAsyncThunk(
    'userManagement/approveUser',
    async (userId: number, { rejectWithValue }) => {
        try {
            const response = await userService.updateStatus(userId, true);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao aprovar usuário');
        }
    }
);

export const revokeUser = createAsyncThunk(
    'userManagement/revokeUser',
    async (userId: number, { rejectWithValue }) => {
        try {
            const response = await userService.updateStatus(userId, false);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao revogar usuário');
        }
    }
);

export const toggleAdmin = createAsyncThunk(
    'userManagement/toggleAdmin',
    async (userId: number, { rejectWithValue }) => {
        try {
            const response = await userService.toggleAdmin(userId);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao alterar status de admin');
        }
    }
);

export const toggleSupervisor = createAsyncThunk(
    'userManagement/toggleSupervisor',
    async (userId: number, { rejectWithValue }) => {
        try {
            const response = await userService.toggleSupervisor(userId);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao alterar status de supervisor');
        }
    }
);

export const deleteUser = createAsyncThunk(
    'userManagement/deleteUser',
    async (userId: number, { rejectWithValue }) => {
        try {
            await userService.delete(userId);
            return userId;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Erro ao deletar usuário');
        }
    }
);

const userManagementSlice = createSlice({
    name: 'userManagement',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        clearCurrentUser: (state) => {
            state.currentUser = null;
        },
        setFilters: (state, action) => {
            state.filters = { ...state.filters, ...action.payload };
        },
        clearFilters: (state) => {
            state.filters = {
                search: '',
                status: '',
                role: '',
            };
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchUsers.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchUsers.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload && action.payload.users) {
                    state.users = action.payload.users as any;
                    if (action.payload.pagination) {
                        state.pagination = {
                            total: action.payload.pagination.total || 0,
                            page: action.payload.pagination.page || 1,
                            per_page: action.payload.pagination.per_page || 10,
                            pages: action.payload.pagination.pages || 0,
                        };
                    }
                }
                state.error = null;
            })
            .addCase(fetchUsers.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(updateUserStatus.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateUserStatus.fulfilled, (state, action) => {
                state.loading = false;
                const updatedUser = action.payload;
                const index = state.users.findIndex(user => user.id === updatedUser.id);
                if (index !== -1) {
                    state.users[index] = updatedUser as any;
                }
                state.error = null;
            })
            .addCase(updateUserStatus.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(approveUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(approveUser.fulfilled, (state, action) => {
                state.loading = false;
                const updatedUser = action.payload;
                const index = state.users.findIndex(user => user.id === updatedUser.id);
                if (index !== -1) {
                    state.users[index] = updatedUser as any;
                }
                state.error = null;
            })
            .addCase(approveUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(revokeUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(revokeUser.fulfilled, (state, action) => {
                state.loading = false;
                const updatedUser = action.payload;
                const index = state.users.findIndex(user => user.id === updatedUser.id);
                if (index !== -1) {
                    state.users[index] = updatedUser as any;
                }
                state.error = null;
            })
            .addCase(revokeUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(toggleAdmin.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(toggleAdmin.fulfilled, (state, action) => {
                state.loading = false;
                const updatedUser = action.payload;
                const index = state.users.findIndex(user => user.id === updatedUser.id);
                if (index !== -1) {
                    state.users[index] = updatedUser as any;
                }
                state.error = null;
            })
            .addCase(toggleAdmin.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(toggleSupervisor.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(toggleSupervisor.fulfilled, (state, action) => {
                state.loading = false;
                const updatedUser = action.payload;
                const index = state.users.findIndex(user => user.id === updatedUser.id);
                if (index !== -1) {
                    state.users[index] = updatedUser as any;
                }
                state.error = null;
            })
            .addCase(toggleSupervisor.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            .addCase(deleteUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(deleteUser.fulfilled, (state, action) => {
                state.loading = false;
                const deletedUserId = action.payload;
                state.users = state.users.filter(user => user.id !== deletedUserId);
                state.error = null;
            })
            .addCase(deleteUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearError, clearCurrentUser, setFilters, clearFilters } = userManagementSlice.actions;
export default userManagementSlice.reducer; 