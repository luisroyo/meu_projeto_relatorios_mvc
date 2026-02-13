// Configuração da API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || (
    process.env.NODE_ENV === 'development'
        ? '/api'  // URL relativa para usar o proxy do Vercel
        : '/api'  // URL relativa para usar o proxy do Vercel
);

const IS_PRODUCTION = process.env.NODE_ENV === 'production';

if (!IS_PRODUCTION) {
    console.log('[API] NODE_ENV:', process.env.NODE_ENV);
    console.log('[API] REACT_APP_API_BASE_URL:', process.env.REACT_APP_API_BASE_URL);
    console.log('[API] Usando API_BASE_URL:', API_BASE_URL);
}

export async function apiFetch(endpoint: string, options: RequestInit = {}, token?: string): Promise<any> {
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    };

    if (!IS_PRODUCTION) {
        console.log('Headers finais:', {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token.substring(0, 10)}...` : 'None'
        });
        console.log(`API Request: ${API_BASE_URL}${endpoint}`, {
            headers: { 'Content-Type': 'application/json', Authorization: token ? `Bearer ${token.substring(0, 10)}...` : 'None' },
            options
        });
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!IS_PRODUCTION) {
        console.log(`API Response:`, { status: response.status, ok: response.ok, url: response.url });
    }

    if (response.status === 401) {
        if (!IS_PRODUCTION) console.warn('API 401 - Não autorizado. Redirecionando para tela inicial.');
        // Força retorno à tela inicial (tela inicial) – App exige tela inicial sempre
        try { window.location.assign('/'); } catch { /* noop */ }
        throw new Error('Não autorizado');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        if (!IS_PRODUCTION) {
            console.error('API Error:', error);
            console.error('Response status:', response.status);
        }

        // Criar um erro que preserve o status HTTP
        const httpError = new Error(error.message || 'Erro na requisição');
        (httpError as any).status = response.status;
        (httpError as any).statusText = response.statusText;
        (httpError as any).originalError = error;

        throw httpError;
    }

    return response.json();
}

// Função para fazer autenticação real
export async function loginUser(email: string, password: string): Promise<any> {
    try {
        console.log('[API] Iniciando autenticação para:', email);
        console.log('[API] URL da API:', `${API_BASE_URL}/api/auth/login`);
        console.log('[API] NODE_ENV:', process.env.NODE_ENV);
        console.log('[API] API_BASE_URL:', API_BASE_URL);

        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        console.log('[API] Status da resposta:', response.status);
        console.log('[API] Response ok?', response.ok);
        console.log('[API] Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            console.error('[API] Erro na resposta:', error);
            throw new Error(error.message || 'Credenciais inválidas');
        }

        const data = await response.json();
        console.log('[API] Dados da resposta COMPLETOS:', JSON.stringify(data, null, 2));
        console.log('[API] Estrutura da resposta:', {
            hasSuccess: 'success' in data,
            hasData: 'data' in data,
            hasMessage: 'message' in data,
            dataKeys: data.data ? Object.keys(data.data) : [],
            hasAccessToken: data.data?.access_token ? true : false,
            responseType: typeof data,
            isArray: Array.isArray(data)
        });

        return data;
    } catch (error: any) {
        console.error('[API] Erro na autenticação:', error);
        throw error;
    }
} 