import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import ocorrenciaReducer from './slices/ocorrenciaSlice';
import rondaReducer from './slices/rondaSlice';
import dashboardReducer from './slices/dashboardSlice';
import analisadorReducer from './slices/analisadorSlice';
import uiReducer from './slices/uiSlice';
import adminReducer from './slices/adminSlice';
import userManagementReducer from './slices/userManagementSlice';
import colaboradorReducer from './slices/colaboradorSlice';
import escalaReducer from './slices/escalaSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ocorrencia: ocorrenciaReducer,
    ronda: rondaReducer,
    dashboard: dashboardReducer,
    analisador: analisadorReducer,
    ui: uiReducer,
    admin: adminReducer,
    userManagement: userManagementReducer,
    colaborador: colaboradorReducer,
    escala: escalaReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignorar ações com timestamps
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['auth.user.created_at', 'auth.user.updated_at'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 