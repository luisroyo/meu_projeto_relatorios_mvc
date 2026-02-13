// Tipos de autenticação
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Tipos de usuário
export interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_supervisor: boolean;
  is_approved: boolean;
  date_registered?: string;
  last_login?: string;
}

// Tipos de dashboard
export interface DashboardStats {
  stats: {
    total_ocorrencias: number;
    total_rondas: number;
    total_condominios: number;
    rondas_em_andamento: number;
    ocorrencias_ultimo_mes: number;
    rondas_ultimo_mes: number;
  };
  user: {
    id: number;
    username: string;
    is_admin: boolean;
    is_supervisor: boolean;
  };
}

export interface RecentOcorrencia {
  id: number;
  tipo: string;
  condominio: string;
  data: string;
  descricao: string;
}

export interface RecentRonda {
  id: number;
  condominio: string;
  data_plantao: string;
  escala_plantao: string;
  status: string;
  total_rondas: number;
}

// Tipos de ocorrência
export interface Ocorrencia {
  id: number;
  tipo: string; // Nome do tipo
  condominio: string; // Nome do condomínio
  data_hora_ocorrencia: string;
  descricao: string; // relatorio_final
  status: string;
  endereco: string; // endereco_especifico
  turno?: string;
  data_criacao: string;
  registrado_por: string; // Nome do usuário que registrou
  supervisor: string; // Nome do supervisor
  registrado_por_user_id: number;
  supervisor_id?: number;
  ocorrencia_tipo_id?: number;
  condominio_id?: number;

  // Campos adicionais para detalhes completos
  relatorio_final?: string;
  endereco_especifico?: string;
  data_modificacao?: string;

  // Relacionamentos (quando disponíveis)
  condominio_obj?: Condominio;
  tipo_obj?: OcorrenciaTipo;
  registrado_por_obj?: User;
  supervisor_obj?: User;
  orgaos_publicos?: string[]; // Nomes dos órgãos
  colaboradores?: string[]; // Nomes dos colaboradores
}

export interface OcorrenciaForm {
  tipo_ocorrencia_id: number;
  condominio_id?: number;
  data_ocorrencia: string;
  hora_ocorrencia: string;
  descricao: string;
  local?: string;
  envolvidos?: string;
  acoes_tomadas?: string;
  status: string;
  relatorio_final?: string;
}

export interface OcorrenciaFilters {
  data_inicio?: string;
  data_fim?: string;
  supervisor_id?: number;
  condominio_id?: number;
  tipo_id?: number;
  status?: string;
  texto_relatorio?: string;
  page?: number;
  per_page?: number;
}

// Tipos de ronda
export interface Ronda {
  id: number;
  data_hora_inicio: string;
  data_hora_fim?: string;
  log_ronda_bruto: string;
  relatorio_processado?: string;
  condominio_id: number;
  user_id: number;
  supervisor_id?: number;
  turno_ronda?: string;
  escala_plantao?: string;
  data_plantao_ronda?: string;
  total_rondas_no_log?: number;
  primeiro_evento_log_dt?: string;
  ultimo_evento_log_dt?: string;
  duracao_total_rondas_minutos?: number;
  tipo?: string;

  // Relacionamentos
  condominio?: Condominio;
  criador?: User;
  supervisor?: User;
}

export interface RondaForm {
  condominio_id: number;
  data_plantao_ronda: string;
  turno_ronda: string;
  escala_plantao: string;
  log_ronda_bruto: string;
  supervisor_id?: number;
}

// Tipos de condomínio
export interface Condominio {
  id: number;
  nome: string;
  endereco?: string;
  bairro?: string;
  cidade?: string;
  estado?: string;
  cep?: string;
}

// Tipos auxiliares
export interface OcorrenciaTipo {
  id: number;
  nome: string;
  descricao?: string;
}

export interface OrgaoPublico {
  id: number;
  nome: string;
  telefone?: string;
  email?: string;
}

export interface Colaborador {
  id: number;
  nome?: string;
  nome_completo?: string;
  cargo?: string;
  telefone?: string;
  email?: string;
  [key: string]: any;
}

// Tipos de paginação
export interface PaginationInfo {
  page: number;
  pages: number;
  total: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  ocorrencias: T[]; // Para ocorrências
  items?: T[]; // Para outros tipos
  pagination: PaginationInfo;
  filters?: any; // Filtros aplicados
}

// Tipos de API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Tipos de analisador
export interface RelatorioRequest {
  relatorio_bruto: string;
}

export interface RelatorioResponse {
  relatorio_processado: string;
  melhorias: string[];
  tempo_processamento: number;
}

// Tipos de ronda em tempo real
export interface RondaTempoReal {
  id: number;
  condominio: string;
  hora_entrada: string;
  observacoes?: string;
  tempo_decorrido?: string;
  status: string;
}

export interface IniciarRondaRequest {
  condominio_id: number;
  hora_entrada: string;
  observacoes?: string;
}

export interface FinalizarRondaRequest {
  hora_saida: string;
  observacoes?: string;
}

// Tipos para Dashboards Administrativos
export interface DashboardMetrics {
  total_usuarios: number;
  total_condominios: number;
  total_tipos_ocorrencia: number;
  total_colaboradores: number;
  usuarios_pendentes: number;
}

export interface RondaDashboardData {
  rondas_por_condominio: Array<{
    condominio: string;
    total: number;
  }>;
  rondas_por_turno: Array<{
    turno: string;
    total: number;
  }>;
  duracao_media: number;
  total_rondas: number;
  rondas_finalizadas: number;
  rondas_em_andamento: number;
  [key: string]: any;
}

export interface OcorrenciaDashboardData {
  ocorrencias_por_tipo: Array<{
    tipo: string;
    total: number;
  }>;
  ocorrencias_por_condominio: Array<{
    condominio: string;
    total: number;
  }>;
  evolucao_temporal: Array<{
    data: string;
    total: number;
  }>;
  total_ocorrencias: number;
  ocorrencias_pendentes: number;
  ocorrencias_finalizadas: number;
}

export interface ComparativoDashboardData {
  comparativo_mensal: Array<{
    mes: string;
    rondas: number;
    ocorrencias: number;
  }>;
  correlacao: number;
}

export interface GeminiDashboardData {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  cache_hits: number;
  api_key_usage: Array<{
    api_key_name: string;
    count: number;
  }>;
  user_usage: Array<{
    username: string;
    count: number;
  }>;
  service_usage: Array<{
    service_name: string;
    count: number;
  }>;
  hourly_usage: Array<{
    hour: string;
    count: number;
  }>;
  recent_requests: Array<{
    id: number;
    username: string;
    service_name: string;
    success: boolean;
    cache_hit: boolean;
    created_at: string;
  }>;
}

export interface OnlineUser {
  id: number;
  username: string;
  email: string;
  last_activity: string;
}

export interface OnlineUsersData {
  users: OnlineUser[];
  count: number;
  timestamp: string;
}

// Tipos para Gerenciamento de Usuários
// User interface is already defined above, removing duplicate

export interface UsersPagination {
  users: User[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Tipos para Gerenciamento de Colaboradores
// Colaborador interface is already defined above, removing duplicate

export interface ColaboradoresPagination {
  colaboradores: Colaborador[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Tipos para Gerenciamento de Escalas
export interface EscalaMensal {
  id: number;
  ano: number;
  mes: number;
  turno: string;
  supervisor_id: number;
  supervisor_nome: string;
}

export interface EscalaFormData {
  ano: number;
  mes: number;
  escalas: Array<{
    turno: string;
    supervisor_id: number;
  }>;
}

// Tipos para Ferramentas Administrativas
export interface JustificativaAtestadoData {
  nome_colaborador: string;
  data_inicio: string;
  data_fim: string;
  motivo: string;
  cid: string;
  medico: string;
  crm: string;
  hospital: string;
}

export interface JustificativaTrocaPlantaoData {
  nome_colaborador: string;
  data_plantao_original: string;
  turno_original: string;
  data_plantao_troca: string;
  turno_troca: string;
  motivo: string;
  supervisor_aprovacao: string;
}

export interface EmailFormatData {
  assunto: string;
  conteudo: string;
  destinatarios: string;
  copia: string;
  tipo_relatorio: string;
}

// Tipos para Filtros
export interface DashboardFilters {
  ano?: number;
  mes?: number;
  data_inicio?: string;
  data_fim?: string;
  condominio_id?: number;
  supervisor_id?: number;
  api_key?: string;
  service?: string;
  user_id?: number;
  days?: number;
}

// Tipos para Respostas de API
// ApiResponse interface is already defined above, removing duplicate

export interface PaginationResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
} 