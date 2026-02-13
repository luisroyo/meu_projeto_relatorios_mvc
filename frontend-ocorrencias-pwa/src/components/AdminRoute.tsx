import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAdminCheck } from '../hooks/useAdminCheck';

interface AdminRouteProps {
    children: React.ReactNode;
    token: string | null;
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children, token }) => {
    const { isAdmin, loading } = useAdminCheck(token);

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh',
                fontSize: '18px',
                color: '#666'
            }}>
                Verificando permissões...
            </div>
        );
    }

    if (!isAdmin) {
        return <Navigate to="/relatorio" replace />;
    }

    return <>{children}</>;
}; 