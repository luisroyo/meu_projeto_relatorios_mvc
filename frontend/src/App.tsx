import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { store } from './store';
import { createAppTheme } from './utils/theme';
import { useAppSelector } from './hooks/useAppSelector';

// Componentes
import Layout from './components/Layout/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AnalisadorPage from './pages/AnalisadorPage';
import OcorrenciasPage from './pages/OcorrenciasPage';
import OcorrenciaDetailsPage from './pages/OcorrenciaDetailsPage';
import OcorrenciaEditPage from './pages/OcorrenciaEditPage';
import RondasPage from './pages/RondasPage';
import TestJwtPage from './pages/TestJwtPage';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';

// Páginas Administrativas
import MetricsDashboardPage from './pages/admin/MetricsDashboardPage';
import UserManagementPage from './pages/admin/UserManagementPage';
import RondaDashboardPage from './pages/admin/RondaDashboardPage';
import OcorrenciaDashboardPage from './pages/admin/OcorrenciaDashboardPage';
import ColaboradorManagementPage from './pages/admin/ColaboradorManagementPage';

// Componente principal da aplicação
const AppContent: React.FC = () => {
  const theme = useAppSelector((state) => state.ui.theme);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const user = useAppSelector((state) => state.auth.user);

  return (
    <ThemeProvider theme={createAppTheme(theme)}>
      <CssBaseline />
      <Router>
        <Routes>
          {/* Rotas públicas */}
          <Route path="/login" element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
          } />
          <Route path="/register" element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
          } />

          {/* Rotas protegidas - Estrutura simplificada */}
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="analisador" element={<AnalisadorPage />} />
            <Route path="ocorrencias" element={<OcorrenciasPage />} />
            <Route path="ocorrencias/nova" element={<OcorrenciaEditPage />} />
            <Route path="ocorrencias/:id/editar" element={<OcorrenciaEditPage />} />
            <Route path="ocorrencias/:id" element={<OcorrenciaDetailsPage />} />
            <Route path="rondas" element={<RondasPage />} />
            <Route path="test-jwt" element={<TestJwtPage />} />

            {/* Rotas Administrativas - Apenas para admins */}
            {user?.is_admin && (
              <>
                <Route path="admin">
                  <Route path="metrics" element={<MetricsDashboardPage />} />
                  <Route path="users" element={<UserManagementPage />} />
                  <Route path="rondas-dashboard" element={<RondaDashboardPage />} />
                  <Route path="ocorrencias-dashboard" element={<OcorrenciaDashboardPage />} />
                  <Route path="colaboradores" element={<ColaboradorManagementPage />} />
                </Route>
              </>
            )}
          </Route>

          {/* Rota 404 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>

      {/* Toast notifications */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme={theme}
      />
    </ThemeProvider>
  );
};

// Componente principal com Provider do Redux
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <AppContent />
      </Provider>
    </ErrorBoundary>
  );
};

export default App;
