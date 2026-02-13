import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { getProfile } from '../../store/slices/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading, user, error } = useAppSelector((state) => state.auth);
  const [isInitialized, setIsInitialized] = useState(false);
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    console.log('ProtectedRoute - Estado atual:', { isAuthenticated, loading, user: !!user, error, hasToken: !!token });

    // Se tem token mas não está autenticado, tentar carregar perfil
    if (token && !isAuthenticated && !user && !loading) {
      console.log('Token encontrado, carregando perfil do usuário...');
      dispatch(getProfile());
    }

    // Marcar como inicializado após um pequeno delay para evitar renderizações prematuras
    const timer = setTimeout(() => {
      setIsInitialized(true);
    }, 100);

    return () => clearTimeout(timer);
  }, [dispatch, isAuthenticated, user, token, loading]);

  // Se ainda não foi inicializado, mostrar loading
  if (!isInitialized) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.2rem'
      }}>
        Inicializando...
      </div>
    );
  }

  // Se está carregando, mostrar loading
  if (loading) {
    console.log('ProtectedRoute - Mostrando loading...');
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.2rem'
      }}>
        Carregando...
      </div>
    );
  }

  // Se não tem token ou não está autenticado, redirecionar para login
  if (!token || !isAuthenticated) {
    console.log('ProtectedRoute - Não autenticado, redirecionando para login');
    console.log('Token:', !!token, 'isAuthenticated:', isAuthenticated, 'user:', !!user);
    return <Navigate to="/login" replace />;
  }

  // Se há erro e não está autenticado, redirecionar para login
  if (error && !isAuthenticated) {
    console.log('ProtectedRoute - Erro detectado, redirecionando para login');
    return <Navigate to="/login" replace />;
  }

  // Se está autenticado, mostrar o conteúdo
  console.log('ProtectedRoute - Usuário autenticado, mostrando conteúdo');
  return <>{children}</>;
};

export default ProtectedRoute; 