// Utilitários para gerenciamento de autenticação

export interface AuthData {
  token: string | null;
  user: any | null;
}

/**
 * Obtém os dados de autenticação do localStorage
 */
export const getAuthData = (): AuthData => {
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');
  
  let user = null;
  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch (error) {
      console.error('Erro ao parsear usuário do localStorage:', error);
    }
  }
  
  return { token, user };
};

/**
 * Limpa todos os dados de autenticação do localStorage
 */
export const clearAuthData = (): void => {
  console.log('=== LIMPANDO DADOS DE AUTENTICAÇÃO ===');
  
  const { token, user } = getAuthData();
  console.log('Token atual:', token ? `${token.substring(0, 20)}...` : 'null');
  console.log('Usuário atual:', user ? 'presente' : 'null');
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  
  console.log('Dados de autenticação removidos!');
  console.log('Token após limpeza:', localStorage.getItem('access_token'));
  console.log('Usuário após limpeza:', localStorage.getItem('user'));
};

/**
 * Verifica se o usuário está autenticado
 */
export const isAuthenticated = (): boolean => {
  const { token, user } = getAuthData();
  return !!(token && user);
};

/**
 * Limpa autenticação e recarrega a página
 */
export const clearAuthAndReload = (): void => {
  clearAuthData();
  console.log('Recarregando página...');
  window.location.reload();
};

/**
 * Função para ser executada no console do navegador
 * Copie e cole no console: clearAuthAndReload()
 */
if (typeof window !== 'undefined') {
  (window as any).clearAuthAndReload = clearAuthAndReload;
  (window as any).getAuthData = getAuthData;
  (window as any).clearAuthData = clearAuthData;
  (window as any).isAuthenticated = isAuthenticated;
} 