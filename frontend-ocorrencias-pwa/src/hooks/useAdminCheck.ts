import { useState, useEffect } from 'react';

export const useAdminCheck = (token: string | null) => {
    const [isAdmin, setIsAdmin] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const checkAdminStatus = async () => {
            if (!token) {
                setIsAdmin(false);
                setLoading(false);
                return;
            }

            try {
                // Verificar se está em ambiente de desenvolvimento
                const isDevelopment = process.env.NODE_ENV === 'development';

                if (isDevelopment) {
                    console.log('🔧 Ambiente de desenvolvimento - Permitindo acesso à tela de Ronda');
                    setIsAdmin(true);
                } else {
                    console.log('🚀 Ambiente de produção - Bloqueando acesso à tela de Ronda');
                    setIsAdmin(false);
                }
            } catch (error) {
                console.error('Erro ao verificar status de administrador:', error);
                setIsAdmin(false);
            } finally {
                setLoading(false);
            }
        };

        checkAdminStatus();
    }, [token]);

    return { isAdmin, loading };
}; 