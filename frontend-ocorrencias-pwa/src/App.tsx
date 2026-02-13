import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoginScreen } from './pages/Login';
import { RelatorioScreen } from './pages/Relatorio';
import { RondaScreen } from './pages/Ronda';
import { OcorrenciasListScreen } from './pages/OcorrenciasList';
import { OcorrenciaDetailScreen } from './pages/OcorrenciaDetail';
import Layout from './components/Layout';
import { AdminRoute } from './components/AdminRoute';
import { useAppUpdate } from './hooks/useAppUpdate';
import { UpdateNotification } from './components/UpdateNotification';

function App() {
    const [token, setToken] = useState<string | null>(null);
    const { hasUpdate, isUpdating, updateApp, forceUpdate } = useAppUpdate();

    console.log('Token atual:', token ? 'Presente' : 'Ausente');

    const handleLogin = (newToken: string) => {
        console.log('=== APP: handleLogin chamado ===');
        console.log('Token recebido:', newToken);
        console.log('Token é string?', typeof newToken === 'string');
        console.log('Token tem conteúdo?', newToken && newToken.length > 0);

        if (newToken && typeof newToken === 'string' && newToken.length > 0) {
            console.log('Definindo token no estado...');
            setToken(newToken);
            console.log('Token definido com sucesso');
        } else {
            console.error('Token inválido recebido:', newToken);
        }
    };

    const handleLogout = () => {
        console.log('Logout realizado');
        setToken(null);
        // Não remove do localStorage pois não salva
    };

    // Sempre mostra a tela de login se não estiver logado
    if (!token) {
        return (
            <>
                <LoginScreen onLogin={handleLogin} />
                <UpdateNotification
                    hasUpdate={hasUpdate}
                    isUpdating={isUpdating}
                    onUpdate={updateApp}
                    onForceUpdate={forceUpdate}
                />
            </>
        );
    }

    return (
        <div className="App">
            <UpdateNotification
                hasUpdate={hasUpdate}
                isUpdating={isUpdating}
                onUpdate={updateApp}
                onForceUpdate={forceUpdate}
            />
            <Routes>
                <Route path="/" element={<Layout onLogout={handleLogout} token={token} />}>
                    <Route index element={<RelatorioScreen token={token} />} />
                    <Route path="relatorio" element={<RelatorioScreen token={token} />} />
                    <Route path="ronda" element={
                        <AdminRoute token={token}>
                            <RondaScreen token={token} />
                        </AdminRoute>
                    } />
                    <Route path="ocorrencias" element={<OcorrenciasListScreen token={token} />} />
                    <Route path="ocorrencias/:id" element={<OcorrenciaDetailScreen token={token} />} />
                </Route>
            </Routes>
        </div>
    );
}

export default App; 