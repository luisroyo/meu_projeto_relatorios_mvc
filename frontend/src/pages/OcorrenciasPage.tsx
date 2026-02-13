import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Pagination,
  Stack,
  useTheme,
  alpha,
  Divider,
  InputAdornment,
  Collapse,
  Fab
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
  ExpandLess as ExpandLessIcon,
  Report as ReportIcon,
  Refresh as RefreshIcon,

} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/LoadingSpinner';
import { ocorrenciaService, userService, condominioService, checkAuthStatus } from '../services/api';
import type { Ocorrencia, User, Condominio, OcorrenciaTipo } from '../types';

const OcorrenciasPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
    per_page: 10,
    has_next: false,
    has_prev: false
  });

  // Filtros aplicados (que causam recarregamento)
  const [filters, setFilters] = useState({
    data_inicio: '',
    data_fim: '',
    supervisor_id: '',
    condominio_id: '',
    tipo_id: '',
    status: '',
    texto_relatorio: '',
    page: 1,
    per_page: 10
  });

  // Filtros temporários (para digitação sem recarregar)
  const [tempFilters, setTempFilters] = useState({
    data_inicio: '',
    data_fim: '',
    supervisor_id: '',
    condominio_id: '',
    tipo_id: '',
    status: '',
    texto_relatorio: '',
  });

  // Dados para os filtros
  const [supervisors, setSupervisors] = useState<User[]>([]);
  const [condominios, setCondominios] = useState<Condominio[]>([]);
  const [tiposOcorrencia, setTiposOcorrencia] = useState<OcorrenciaTipo[]>([]);
  const [statusList] = useState(['Registrada', 'Em andamento', 'Concluída']);



  useEffect(() => {
    loadFilterData();
    // Verificar status da autenticação
    checkAuthStatus();
  }, []);

  useEffect(() => {
    loadOcorrencias();
  }, [filters]);

  // Sincronizar filtros temporários com filtros aplicados na inicialização
  useEffect(() => {
    setTempFilters({
      data_inicio: filters.data_inicio,
      data_fim: filters.data_fim,
      supervisor_id: filters.supervisor_id,
      condominio_id: filters.condominio_id,
      tipo_id: filters.tipo_id,
      status: filters.status,
      texto_relatorio: filters.texto_relatorio,
    });
  }, []);

  const loadFilterData = async () => {
    try {
      const [usersData, condominiosData, tiposData] = await Promise.all([
        userService.list(),
        condominioService.list(),
        ocorrenciaService.getTipos()
      ]);

      // Ajustar para a estrutura correta retornada pelas APIs
      const users = Array.isArray(usersData) ? usersData : ((usersData as any)?.users || []);
      const condominios = Array.isArray(condominiosData) ? condominiosData : ((condominiosData as any)?.condominios || []);
      const tipos = Array.isArray(tiposData) ? tiposData : ((tiposData as any)?.tipos || []);

      // Filtro apenas por supervisores reais
      const supervisores = users.filter((user: any) => user.is_supervisor === true);
      setSupervisors(supervisores);
      setCondominios(condominios);
      setTiposOcorrencia(tipos);
    } catch (error) {
      console.error('Erro ao carregar dados dos filtros:', error);
    }
  };

  const loadOcorrencias = async () => {
    try {
      setLoading(true);
      const response = await ocorrenciaService.list(filters);
      setOcorrencias(response.ocorrencias || []);
      setPagination(response.pagination || {
        page: 1,
        pages: 1,
        per_page: 10,
        total: 0,
        has_next: false,
        has_prev: false
      });
    } catch (error) {
      console.error('Erro ao carregar ocorrências:', error);
      setError('Erro ao carregar ocorrências');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field: string, value: string | number) => {
    let processedValue = value;

    // Aplicar máscara de data para campos de data
    if (field === 'data_inicio' || field === 'data_fim') {
      const stringValue = String(value);

      // Remover tudo que não é número
      const numbers = stringValue.replace(/\D/g, '');

      // Aplicar máscara dd/mm/aaaa
      if (numbers.length <= 2) {
        processedValue = numbers;
      } else if (numbers.length <= 4) {
        processedValue = `${numbers.slice(0, 2)}/${numbers.slice(2)}`;
      } else if (numbers.length <= 8) {
        processedValue = `${numbers.slice(0, 2)}/${numbers.slice(2, 4)}/${numbers.slice(4, 8)}`;
      } else {
        processedValue = `${numbers.slice(0, 2)}/${numbers.slice(2, 4)}/${numbers.slice(4, 8)}`;
      }
    }

    setTempFilters(prev => ({
      ...prev,
      [field]: processedValue
    }));
  };

  const applyFilters = () => {
    setFilters(tempFilters);
    setPagination(prev => ({ ...prev, page: 1 })); // Resetar para primeira página ao filtrar
  };

  const formatDateForAPI = (dateString: string) => {
    if (!dateString) return '';

    try {
      // Primeiro, verificar se está no formato dd/mm/aaaa
      const ddmmRegex = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
      const ddmmMatch = dateString.match(ddmmRegex);

      if (ddmmMatch) {
        const [, day, month, year] = ddmmMatch;
        const dayNum = parseInt(day);
        const monthNum = parseInt(month);
        const yearNum = parseInt(year);

        // Validar se os valores são válidos
        if (yearNum < 1900 || yearNum > 2100) {
          console.warn('Ano inválido:', yearNum);
          return '';
        }

        if (monthNum < 1 || monthNum > 12) {
          console.warn('Mês inválido:', monthNum);
          return '';
        }

        if (dayNum < 1 || dayNum > 31) {
          console.warn('Dia inválido:', dayNum);
          return '';
        }

        // A API espera DD/MM/YYYY, então manter o formato original
        const formattedDate = `${String(dayNum).padStart(2, '0')}/${String(monthNum).padStart(2, '0')}/${year}`;
        console.log('Data mantida dd/mm/aaaa:', dateString, '->', formattedDate);

        return formattedDate;
      }

      // Verificar se está no formato YYYY-MM-DD (campo de data nativo)
      const yyyyRegex = /^(\d{4})-(\d{2})-(\d{2})$/;
      const yyyyMatch = dateString.match(yyyyRegex);

      if (yyyyMatch) {
        const [, year, month, day] = yyyyMatch;

        // Validar se os valores são válidos
        const yearNum = parseInt(year);
        const monthNum = parseInt(month);
        const dayNum = parseInt(day);

        if (yearNum < 1900 || yearNum > 2100) {
          console.warn('Ano inválido:', yearNum);
          return '';
        }

        if (monthNum < 1 || monthNum > 12) {
          console.warn('Mês inválido:', monthNum);
          return '';
        }

        if (dayNum < 1 || dayNum > 31) {
          console.warn('Dia inválido:', dayNum);
          return '';
        }

        // Converter YYYY-MM-DD para DD/MM/YYYY (formato que a API espera)
        const formattedDate = `${String(dayNum).padStart(2, '0')}/${String(monthNum).padStart(2, '0')}/${year}`;
        console.log('Data convertida YYYY-MM-DD -> dd/mm/aaaa:', dateString, '->', formattedDate);

        return formattedDate;
      }

      console.warn('Formato de data inválido:', dateString);
      return '';
    } catch (error) {
      console.error('Erro ao formatar data:', error);
      return '';
    }
  };



  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setPagination(prev => ({ ...prev, page }));
  };

  const clearFilters = () => {
    setTempFilters({
      status: '',
      condominio_id: '',
      supervisor_id: '',
      tipo_id: '',
      data_inicio: '',
      data_fim: '',
      texto_relatorio: ''
    });
    setFilters({
      status: '',
      condominio_id: '',
      supervisor_id: '',
      tipo_id: '',
      data_inicio: '',
      data_fim: '',
      texto_relatorio: ''
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'concluída':
        return 'success';
      case 'em andamento':
        return 'warning';
      case 'registrada':
        return 'info';
      default:
        return 'default';
    }
  };

  const handleView = (id: number) => {
    navigate(`/ocorrencias/${id}`);
  };

  const handleEdit = (id: number) => {
    navigate(`/ocorrencias/${id}/editar`);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Tem certeza que deseja excluir esta ocorrência?')) {
      try {
        await ocorrenciaService.delete(id);
        toast.success('Ocorrência excluída com sucesso!');
        loadOcorrencias();
      } catch (error) {
        toast.error('Erro ao excluir ocorrência');
      }
    }
  };

  if (loading) {
    return <LoadingSpinner message="Carregando ocorrências..." />;
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Moderno */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: 3,
          p: 4,
          mb: 4,
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.1"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            opacity: 0.3,
          }
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
            📋 Gestão de Ocorrências
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.9 }}>
            Gerencie e acompanhe todas as ocorrências do sistema
          </Typography>
        </Box>
      </Box>

      {/* Card Principal */}
      <Card
        sx={{
          borderRadius: 3,
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden',
          border: '1px solid rgba(0, 0, 0, 0.05)',
        }}
      >
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <ReportIcon sx={{ color: 'primary.main', fontSize: 28 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Lista de Ocorrências
              </Typography>
              <Chip
                label={`${pagination.total} total`}
                size="small"
                color="primary"
                variant="outlined"
              />
              {Object.values(filters).some(value => value && value !== '' && value !== 1 && value !== 10) && (
                <Chip
                  label="Filtros ativos"
                  size="small"
                  color="warning"
                  variant="filled"
                  sx={{ ml: 1 }}
                />
              )}
            </Box>
          }
          action={
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
              >
                {showFilters ? 'Ocultar Filtros' : 'Mostrar Filtros'}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => navigate('/ocorrencias/nova')}
                sx={{
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                    boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                  }
                }}
              >
                Nova Ocorrência
              </Button>
            </Stack>
          }
          sx={{
            backgroundColor: alpha(theme.palette.primary.main, 0.02),
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        />

        <CardContent sx={{ p: 0 }}>
          {/* Filtros */}
          <Collapse in={showFilters}>
            <Box sx={{ p: 3, backgroundColor: alpha(theme.palette.grey[50], 0.5) }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <TextField
                    fullWidth
                    label="Data Início (dd/mm/aaaa)"
                    placeholder="dd/mm/aaaa"
                    value={tempFilters.data_inicio}
                    onChange={(e) => handleFilterChange('data_inicio', e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          📅
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                      }
                    }}
                    helperText="Formato: dd/mm/aaaa"
                  />
                </Box>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <TextField
                    fullWidth
                    label="Data Fim (dd/mm/aaaa)"
                    placeholder="dd/mm/aaaa"
                    value={tempFilters.data_fim}
                    onChange={(e) => handleFilterChange('data_fim', e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          📅
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                      }
                    }}
                    helperText="Formato: dd/mm/aaaa"
                  />
                </Box>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Supervisor</InputLabel>
                    <Select
                      value={tempFilters.supervisor_id}
                      label="Supervisor"
                      onChange={(e) => handleFilterChange('supervisor_id', e.target.value)}
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {supervisors.map((supervisor) => (
                        <MenuItem key={supervisor.id} value={supervisor.id}>
                          {supervisor.username}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Condomínio</InputLabel>
                    <Select
                      value={tempFilters.condominio_id}
                      label="Condomínio"
                      onChange={(e) => handleFilterChange('condominio_id', e.target.value)}
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {condominios.map((condominio) => (
                        <MenuItem key={condominio.id} value={condominio.id}>
                          {condominio.nome}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Tipo</InputLabel>
                    <Select
                      value={tempFilters.tipo_id}
                      label="Tipo"
                      onChange={(e) => handleFilterChange('tipo_id', e.target.value)}
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {tiposOcorrencia.map((tipo) => (
                        <MenuItem key={tipo.id} value={tipo.id}>
                          {tipo.nome}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={tempFilters.status}
                      label="Status"
                      onChange={(e) => handleFilterChange('status', e.target.value)}
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {statusList.map((status) => (
                        <MenuItem key={status} value={status}>
                          {status}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box sx={{ flex: '1 1 300px', minWidth: 300 }}>
                  <TextField
                    fullWidth
                    label="Buscar no relatório"
                    value={tempFilters.texto_relatorio}
                    onChange={(e) => handleFilterChange('texto_relatorio', e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                      }
                    }}
                  />
                </Box>
                <Box sx={{ flex: '1 1 300px', minWidth: 300 }}>
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      startIcon={<SearchIcon />}
                      onClick={applyFilters}
                      sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                        }
                      }}
                    >
                      Filtrar
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<ClearIcon />}
                      onClick={clearFilters}
                      sx={{ borderRadius: 2, textTransform: 'none' }}
                    >
                      Limpar Filtros
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<RefreshIcon />}
                      onClick={loadOcorrencias}
                      sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #218838 0%, #1e7e34 100%)',
                        }
                      }}
                    >
                      Atualizar
                    </Button>
                  </Stack>
                </Box>
              </Box>
            </Box>
          </Collapse>

          {error && (
            <Alert severity="error" sx={{ m: 3, borderRadius: 2 }}>
              {error}
            </Alert>
          )}

          {/* Tabela */}
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: alpha(theme.palette.primary.main, 0.05) }}>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>ID</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Tipo</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Condomínio</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Data/Hora</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Supervisor</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ocorrencias.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        Nenhuma ocorrência encontrada
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  ocorrencias.map((ocorrencia) => (
                    <TableRow
                      key={ocorrencia.id}
                      sx={{
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.primary.main, 0.02),
                        },
                        transition: 'background-color 0.2s ease',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 500 }}>#{ocorrencia.id}</TableCell>
                      <TableCell>{ocorrencia.tipo}</TableCell>
                      <TableCell>{ocorrencia.condominio}</TableCell>
                      <TableCell>{formatDate(ocorrencia.data_hora_ocorrencia)}</TableCell>
                      <TableCell>
                        <Chip
                          label={ocorrencia.status}
                          color={getStatusColor(ocorrencia.status) as any}
                          size="small"
                          sx={{ fontWeight: 500 }}
                        />
                      </TableCell>
                      <TableCell>{ocorrencia.supervisor}</TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Tooltip title="Visualizar">
                            <IconButton
                              size="small"
                              onClick={() => handleView(ocorrencia.id)}
                              sx={{
                                color: 'primary.main',
                                '&:hover': {
                                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                                }
                              }}
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Editar">
                            <IconButton
                              size="small"
                              onClick={() => handleEdit(ocorrencia.id)}
                              sx={{
                                color: 'warning.main',
                                '&:hover': {
                                  backgroundColor: alpha(theme.palette.warning.main, 0.1),
                                }
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Excluir">
                            <IconButton
                              size="small"
                              onClick={() => handleDelete(ocorrencia.id)}
                              sx={{
                                color: 'error.main',
                                '&:hover': {
                                  backgroundColor: alpha(theme.palette.error.main, 0.1),
                                }
                              }}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Paginação */}
          {pagination.pages > 1 && (
            <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={pagination.pages}
                page={pagination.page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
                sx={{
                  '& .MuiPaginationItem-root': {
                    borderRadius: 2,
                    fontWeight: 500,
                  }
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* FAB para Nova Ocorrência */}
      <Fab
        color="primary"
        aria-label="add"
        onClick={() => navigate('/ocorrencias/nova')}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
            boxShadow: '0 12px 35px rgba(102, 126, 234, 0.4)',
          }
        }}
      >
        <AddIcon />
      </Fab>


    </Box>
  );
};

export default OcorrenciasPage; 