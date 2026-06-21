import axios, { AxiosError, type AxiosResponse } from 'axios';

// Configuração base do axios
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000' : ''),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true, // Importante para CORS com credenciais
});

// Configuração alternativa sem withCredentials (para teste)
const apiNoCredentials = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000' : ''),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  // Sem withCredentials
});

// Interceptor para apiNoCredentials (apenas para adicionar token quando necessário)
apiNoCredentials.interceptors.request.use((config) => {
  // Não adicionar token em requisições OPTIONS (preflight)
  if (config.method?.toLowerCase() !== 'options') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Token adicionado à requisição (noCredentials):', token.substring(0, 20) + '...');
    }
  }
  return config;
});

// Interceptor para adicionar token JWT
api.interceptors.request.use((config) => {
  // Não adicionar token em requisições OPTIONS (preflight)
  if (config.method?.toLowerCase() !== 'options') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Token adicionado à requisição:', token.substring(0, 20) + '...');
    }
  }
  return config;
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Funções auxiliares
const handleApiResponse = (response: AxiosResponse) => {
  const body = response.data;
  // Se a resposta seguir o padrão { success: true, data: ... }, retorna data
  if (body && body.success === true && body.data !== undefined) {
    return body.data;
  }
  return body;
};

const handleApiError = (error: AxiosError) => {
  if (error.response?.data && typeof error.response.data === 'object' && 'error' in error.response.data) {
    throw new Error((error.response.data as any).error);
  }
  throw new Error('Erro de comunicação com o servidor');
};

// Função para verificar estado da autenticação
export const checkAuthStatus = () => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

// Serviços de autenticação
export const authService = {
  login: async (email: string, password: string): Promise<{
    access_token: string;
    user: {
      id: number;
      username: string;
      email: string;
      is_admin: boolean;
      is_supervisor: boolean;
      is_approved: boolean;
    };
  }> => {
    try {
      console.log('🔐 AuthService.login - Iniciando...');
      console.log('📤 Dados recebidos:', { email, password });

      const requestData = { email, password };
      console.log('📦 Dados para envio:', JSON.stringify(requestData));

      // Usar apiNoCredentials para evitar problemas com withCredentials
      const response = await apiNoCredentials.post('/api/auth/login', requestData);
      console.log('✅ AuthService.login - Sucesso:', response.data);
      return handleApiResponse(response);
    } catch (error) {
      console.error('❌ AuthService.login - Erro:', error);
      throw handleApiError(error as AxiosError);
    }
  },

  register: async (username: string, email: string, password: string): Promise<{
    message: string;
    user_id: number;
  }> => {
    try {
      const response = await api.post('/api/auth/register', { username, email, password });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getProfile: async (): Promise<{
    id: number;
    username: string;
    email: string;
    is_admin: boolean;
    is_supervisor: boolean;
    is_approved: boolean;
    date_registered?: string;
    last_login?: string;
  }> => {
    try {
      const response = await api.get('/api/auth/profile');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  logout: async (): Promise<{ message: string }> => {
    try {
      const response = await api.post('/api/auth/logout');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  refresh: async (): Promise<{ access_token: string }> => {
    try {
      const response = await api.post('/api/auth/refresh');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de usuários
export const userService = {
  list: async (filters?: any): Promise<{
    users: Array<{
      id: number;
      username: string;
      email: string;
      is_supervisor: boolean;
      is_admin: boolean;
      is_approved: boolean;
    }>;
    pagination: {
      total: number;
      page: number;
      per_page: number;
      pages: number;
    };
  }> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/users?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  updateStatus: async (userId: number, isApproved: boolean): Promise<{
    id: number;
    username: string;
    email: string;
    is_supervisor: boolean;
    is_admin: boolean;
    is_approved: boolean;
  }> => {
    try {
      const response = await api.post(`/api/users/${userId}/status`, { is_approved: isApproved });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  toggleAdmin: async (userId: number): Promise<{
    id: number;
    username: string;
    email: string;
    is_supervisor: boolean;
    is_admin: boolean;
    is_approved: boolean;
  }> => {
    try {
      const response = await api.post(`/api/users/${userId}/toggle-admin`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  toggleSupervisor: async (userId: number): Promise<{
    id: number;
    username: string;
    email: string;
    is_supervisor: boolean;
    is_admin: boolean;
    is_approved: boolean;
  }> => {
    try {
      const response = await api.post(`/api/users/${userId}/toggle-supervisor`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (userId: number): Promise<void> => {
    try {
      await api.delete(`/api/users/${userId}`);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de condomínios
export const condominioService = {
  list: async (): Promise<{
    condominios: Array<{
      id: number;
      nome: string;
      endereco?: string;
      bairro?: string;
      cidade?: string;
      estado?: string;
      cep?: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/condominios');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getById: async (id: number): Promise<{
    id: number;
    nome: string;
    endereco?: string;
    bairro?: string;
    cidade?: string;
    estado?: string;
    cep?: string;
  }> => {
    try {
      const response = await api.get(`/api/condominios/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  create: async (data: {
    nome: string;
    endereco?: string;
    bairro?: string;
    cidade?: string;
    estado?: string;
    cep?: string;
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.post('/api/condominios', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  update: async (id: number, data: {
    nome?: string;
    endereco?: string;
    bairro?: string;
    cidade?: string;
    estado?: string;
    cep?: string;
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.put(`/api/condominios/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (id: number): Promise<{ message: string }> => {
    try {
      const response = await api.delete(`/api/condominios/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de ocorrências
export const ocorrenciaService = {
  list: async (filters: {
    page?: number;
    per_page?: number;
    status?: string;
    condominio_id?: number;
    supervisor_id?: number;
    tipo_id?: number;
    data_inicio?: string;
    data_fim?: string;
    texto_relatorio?: string;
  } = {}): Promise<{
    ocorrencias: Array<{
      id: number;
      tipo: string;
      condominio: string;
      data_hora_ocorrencia: string;
      descricao: string;
      status: string;
      endereco: string;
      turno: string;
      data_criacao: string;
      registrado_por: string;
      supervisor: string;
      registrado_por_user_id: number;
      supervisor_id: number;
      colaboradores_envolvidos?: Array<{ id: number, nome: string }>;
      orgaos_acionados?: Array<{ id: number, nome: string }>;
    }>;
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }> => {
    try {
      const response = await api.get('/api/ocorrencias', { params: filters });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getById: async (id: number): Promise<{
    id: number;
    tipo: string;
    condominio: string;
    data_hora_ocorrencia: string;
    descricao: string;
    status: string;
    endereco: string;
    turno: string;
    data_criacao: string;
    registrado_por: string;
    supervisor: string;
    registrado_por_user_id: number;
    supervisor_id: number;
    condominio_id?: number;
    ocorrencia_tipo_id?: number;
    relatorio_final?: string;
    endereco_especifico?: string;
    colaboradores_envolvidos?: Array<{ id: number, nome: string }>;
    orgaos_acionados?: Array<{ id: number, nome: string }>;
  }> => {
    try {
      const response = await api.get(`/api/ocorrencias/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  create: async (data: {
    relatorio_final: string;
    ocorrencia_tipo_id: number;
    condominio_id?: number;
    supervisor_id?: number;
    turno?: string;
    status?: string;
    endereco_especifico?: string;
    data_hora_ocorrencia?: string;
    colaboradores_envolvidos?: number[];
    orgaos_acionados?: number[];
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.post('/api/ocorrencias', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  update: async (id: number, data: {
    relatorio_final?: string;
    ocorrencia_tipo_id?: number;
    condominio_id?: number;
    supervisor_id?: number;
    turno?: string;
    status?: string;
    endereco_especifico?: string;
    data_hora_ocorrencia?: string;
    colaboradores_envolvidos?: number[];
    orgaos_acionados?: number[];
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.put(`/api/ocorrencias/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (id: number): Promise<{ message: string }> => {
    try {
      const response = await api.delete(`/api/ocorrencias/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getTipos: async (): Promise<{
    tipos: Array<{
      id: number;
      nome: string;
      descricao: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/tipos');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getCondominios: async (): Promise<{
    condominios: Array<{
      id: number;
      nome: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/condominios');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getColaboradores: async (): Promise<{
    colaboradores: Array<{
      id: number;
      nome: string;
      cargo: string;
      matricula: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/colaboradores');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getOrgaosPublicos: async (): Promise<{
    orgaos_publicos: Array<{
      id: number;
      nome: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/orgaos-publicos');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getSupervisores: async (): Promise<{
    supervisores: Array<{
      id: number;
      nome: string;
      email: string;
    }>;
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/supervisores');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getStatus: async (): Promise<{
    status: string[];
  }> => {
    try {
      const response = await api.get('/api/ocorrencias/status');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  // Análise de relatório usando IA (endpoint do analisador)
  analisarRelatorio: async (relatorioBruto: string): Promise<{
    sucesso: boolean;
    dados: {
      data_hora_ocorrencia?: string;
      turno?: string;
      endereco_especifico?: string;
      condominio_id?: number;
      ocorrencia_tipo_id?: number;
      colaboradores_envolvidos?: number[];
    };
    classificacao: string;
    relatorio_processado: string;
  }> => {
    try {
      const response = await api.post('/api/ocorrencias/analyze-report', {
        relatorio_bruto: relatorioBruto
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  exportarDocx: async (ocorrenciaIds: number[]): Promise<void> => {
    try {
      const response = await api.post('/api/ocorrencias/export/docx', {
        ocorrencia_ids: ocorrenciaIds
      }, {
        responseType: 'blob' // Importante para receber arquivo
      });
      
      // Criar link para download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extrair nome do arquivo do header content-disposition se possível
      let filename = 'Relatorio_consolidado.docx';
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço do analisador
export const analisadorService = {
  analisarRelatorio: async (relatorioBruto: string): Promise<{
    classificacao: string;
    relatorio_processado: string;
  }> => {
    try {
      const response = await api.post('/api/analisador/processar-relatorio', {
        relatorio_bruto: relatorioBruto
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getHistorico: async (page: number = 1, per_page: number = 10): Promise<{
    historico: Array<{
      id: number;
      tipo_processamento: string;
      sucesso: boolean;
      mensagem_erro?: string;
      data_processamento: string;
    }>;
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }> => {
    try {
      const response = await api.get('/api/analisador/historico', {
        params: { page, per_page }
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de dashboard
export const dashboardService = {
  getStats: async (): Promise<{
    total_ocorrencias: number;
    total_rondas: number;
    ocorrencias_hoje: number;
    rondas_hoje: number;
  }> => {
    try {
      const response = await api.get('/api/dashboard/stats');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getMetrics: async (): Promise<{
    total_usuarios: number;
    total_condominios: number;
    total_tipos_ocorrencia: number;
    total_colaboradores: number;
    usuarios_pendentes: number;
  }> => {
    try {
      // Usando o endpoint correto que existe no backend
      const response = await api.get('/api/dashboard/stats');
      const data = handleApiResponse(response);

      // Transformando a resposta para o formato esperado
      return {
        total_usuarios: 0, // Não disponível no endpoint atual
        total_condominios: data.stats?.total_condominios || 0,
        total_tipos_ocorrencia: 0, // Não disponível no endpoint atual
        total_colaboradores: 0, // Não disponível no endpoint atual
        usuarios_pendentes: 0, // Não disponível no endpoint atual
      };
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getRondaDashboard: async (filters?: any): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/admin/dashboard/rondas?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getOcorrenciaDashboard: async (filters?: any): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/admin/dashboard/ocorrencias?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getComparativoDashboard: async (filters?: any): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/admin/dashboard/comparativo?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getGeminiDashboard: async (filters?: any): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/admin/gemini-dashboard/api/stats?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getOnlineUsers: async (): Promise<any> => {
    try {
      const response = await api.get('/api/admin/online/api/online-users');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getRecentOcorrencias: async (): Promise<Array<{
    id: number;
    tipo: string;
    condominio: string;
    data_hora_ocorrencia: string;
    status: string;
  }>> => {
    try {
      const response = await api.get('/api/dashboard/recent-ocorrencias');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getRecentRondas: async (): Promise<Array<{
    id: number;
    condominio: string;
    data_inicio: string;
    data_fim: string;
    status: string;
  }>> => {
    try {
      const response = await api.get('/api/dashboard/recent-rondas');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de colaboradores
export const colaboradorService = {
  list: async (filters: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
  } = {}): Promise<{
    colaboradores: Array<{
      id: number;
      nome_completo: string;
      cargo: string;
      matricula: string;
      data_admissao?: string;
      status: string;
    }>;
    pagination: {
      page: number;
      pages: number;
      total: number;
      per_page: number;
    };
  }> => {
    try {
      const response = await api.get('/api/colaboradores', { params: filters });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getById: async (id: number): Promise<{
    id: number;
    nome_completo: string;
    cargo: string;
    matricula: string;
    data_admissao?: string;
    status: string;
  }> => {
    try {
      const response = await api.get(`/api/colaboradores/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  create: async (data: {
    nome_completo: string;
    cargo: string;
    matricula?: string;
    data_admissao?: string;
    status?: string;
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.post('/api/colaboradores', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  update: async (id: number, data: {
    nome_completo?: string;
    cargo?: string;
    matricula?: string;
    data_admissao?: string;
    status?: string;
  }): Promise<{
    message: string;
  }> => {
    try {
      const response = await api.put(`/api/colaboradores/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (id: number): Promise<{ message: string }> => {
    try {
      const response = await api.delete(`/api/colaboradores/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

// Serviço de rondas
export const rondaService = {
  list: async (filters: {
    page?: number;
    per_page?: number;
    status?: string;
    condominio_id?: number;
    supervisor_id?: number;
    data_inicio?: string;
    data_fim?: string;
  } = {}): Promise<{
    rondas: Array<{
      id: number;
      condominio: string;
      supervisor: string;
      data_inicio: string;
      data_fim: string;
      status: string;
      observacoes: string;
    }>;
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }> => {
    try {
      const response = await api.get('/api/rondas', { params: filters });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getById: async (id: number): Promise<{
    id: number;
    condominio: string;
    supervisor: string;
    data_inicio: string;
    data_fim: string;
    status: string;
    observacoes: string;
    condominio_id?: number;
    supervisor_id?: number;
  }> => {
    try {
      const response = await api.get(`/api/rondas/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  create: async (data: {
    condominio_id: number;
    supervisor_id: number;
    data_inicio: string;
    data_fim?: string;
    status?: string;
    observacoes?: string;
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.post('/api/rondas', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  update: async (id: number, data: {
    condominio_id?: number;
    supervisor_id?: number;
    data_inicio?: string;
    data_fim?: string;
    status?: string;
    observacoes?: string;
  }): Promise<{
    message: string;
    id: number;
  }> => {
    try {
      const response = await api.put(`/api/rondas/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (id: number): Promise<{ message: string }> => {
    try {
      const response = await api.delete(`/api/rondas/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  // Rondas em tempo real
  getEmAndamento: async (): Promise<Array<{
    id: number;
    condominio: string;
    supervisor: string;
    data_inicio: string;
    status: string;
  }>> => {
    try {
      const response = await api.get('/api/rondas/tempo-real/em-andamento');
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  iniciarTempoReal: async (data: {
    condominio_id: number;
    supervisor_id: number;
    observacoes?: string;
  }): Promise<{
    success: boolean;
    message: string;
    ronda: {
      id: number;
      condominio: string;
      supervisor: string;
      data_inicio: string;
      status: string;
    };
  }> => {
    try {
      const response = await api.post('/api/rondas/tempo-real/iniciar', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  finalizarTempoReal: async (id: number, data: {
    data_fim: string;
    observacoes?: string;
  }): Promise<{
    success: boolean;
    message: string;
  }> => {
    try {
      const response = await api.post(`/api/rondas/tempo-real/finalizar/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
  uploadRondaLog: async (file: File, month?: number, year?: number): Promise<{
    success: boolean;
    message: string;
    rondas_criadas?: number;
    erros?: string[];
  }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (month) formData.append('month', month.toString());
      if (year) formData.append('year', year.toString());

      const response = await api.post('/api/rondas/upload-process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  uploadRondaFromGoogleDrive: async (fileId: string, accessToken: string, fileName: string, month?: number, year?: number): Promise<{
    success: boolean;
    message: string;
    rondas_criadas?: number;
    erros?: string[];
  }> => {
    try {
      const formData = new FormData();
      formData.append('google_file_id', fileId);
      formData.append('google_access_token', accessToken);
      formData.append('google_file_name', fileName);
      if (month) formData.append('month', month.toString());
      if (year) formData.append('year', year.toString());

      const response = await api.post('/api/rondas/upload-process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
  processarWhatsApp: async (data: {
    condominio_id: number;
    data_inicio: string;
    data_fim: string;
  }): Promise<{
    success: boolean;
    relatorio_processado: string;
    log_bruto: string;
    message?: string;
  }> => {
    try {
      const response = await api.post('/api/whatsapp/process', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};


// Serviço de escalas
export const escalaService = {
  list: async (filters?: any): Promise<Array<{
    id: number;
    ano: number;
    mes: number;
    turno: string;
    supervisor_id: number;
    supervisor_nome: string;
  }>> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/admin/escalas?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  create: async (data: any): Promise<{
    id: number;
    ano: number;
    mes: number;
    turno: string;
    supervisor_id: number;
    supervisor_nome: string;
  }> => {
    try {
      const response = await api.post('/api/admin/escalas', data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  update: async (id: number, data: any): Promise<{
    id: number;
    ano: number;
    mes: number;
    turno: string;
    supervisor_id: number;
    supervisor_nome: string;
  }> => {
    try {
      const response = await api.put(`/api/admin/escalas/${id}`, data);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};


// Serviço de paradas
export const paradaService = {
  list: async (filters?: any): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const response = await api.get(`/api/paradas?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  get: async (id: number): Promise<any> => {
    try {
      const response = await api.get(`/api/paradas/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  delete: async (id: number): Promise<any> => {
    try {
      const response = await api.delete(`/api/paradas/${id}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  uploadParadaLog: async (file: File, condominioId?: number, datePlantao?: string, escalaPlantao?: string, supervisorId?: number): Promise<any> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (condominioId) formData.append('condominio_id', condominioId.toString());
      if (datePlantao) formData.append('data_plantao', datePlantao);
      if (escalaPlantao) formData.append('escala_plantao', escalaPlantao);
      if (supervisorId) formData.append('supervisor_id', supervisorId.toString());

      const response = await api.post('/api/paradas/upload-process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  uploadParadaFromGoogleDrive: async (
    fileId: string, 
    accessToken: string, 
    fileName: string, 
    condominioId?: number, 
    datePlantao?: string, 
    escalaPlantao?: string, 
    supervisorId?: number
  ): Promise<any> => {
    try {
      const formData = new FormData();
      formData.append('google_file_id', fileId);
      formData.append('google_access_token', accessToken);
      formData.append('google_file_name', fileName);
      if (condominioId) formData.append('condominio_id', condominioId.toString());
      if (datePlantao) formData.append('data_plantao', datePlantao);
      if (escalaPlantao) formData.append('escala_plantao', escalaPlantao);
      if (supervisorId) formData.append('supervisor_id', supervisorId.toString());

      const response = await api.post('/api/paradas/upload-process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  getDashboardStats: async (year?: number, condominioId?: number): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (year) params.append('year', year.toString());
      if (condominioId) params.append('condominio_id', condominioId.toString());
      const response = await api.get(`/api/paradas/dashboard?${params.toString()}`);
      return handleApiResponse(response);
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

export default api; 