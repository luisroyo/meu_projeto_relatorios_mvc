import React, { useState, useEffect } from 'react';
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
  alpha
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import LoadingSpinner from '../components/LoadingSpinner';
import { rondaService, condominioService, userService } from '../services/api';
import type { Ronda } from '../types';

interface RondaListResponse {
  rondas: Ronda[];
  pagination: {
    page: number;
    pages: number;
    total: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

const RondasPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [rondas, setRondas] = useState<Ronda[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
    per_page: 10,
    has_next: false,
    has_prev: false
  });

  // Filtros baseados no backend
  const [filters, setFilters] = useState({
    condominio: '',
    supervisor: '',
    turno: '',
    data_inicio: '',
    data_fim: '',
    page: 1,
    per_page: 10
  });

  // Dados para os filtros (seriam carregados do backend)
  const [condominios, setCondominios] = useState<Array<{ id: number; nome: string }>>([]);
  const [supervisors, setSupervisors] = useState<Array<{ id: number; username: string }>>([]);
  const [turnos] = useState([
    'Noturno Par',
    'Noturno Impar',
    'Diurno Par',
    'Diurno Impar'
  ]);

  useEffect(() => {
    loadRondas();
    loadFilterData();
  }, [filters]);

  const loadFilterData = async () => {
    try {
      // Carregar dados dos filtros do backend
      const [condominiosData, usersData] = await Promise.all([
        condominioService.list(),
        userService.list()
      ]);

      // Ajustar para a estrutura correta retornada pelas APIs
      const condominios = Array.isArray(condominiosData) ? condominiosData : ((condominiosData as any)?.condominios || []);
      const users = Array.isArray(usersData) ? usersData : ((usersData as any)?.users || []);

      setCondominios(condominios);
      // Filtro apenas por supervisores reais
      const supervisores = users.filter((user: any) => user.is_supervisor === true);

      setSupervisors(supervisores);
    } catch (error) {
      console.error('Erro ao carregar dados dos filtros:', error);
    }
  };

  const loadRondas = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await rondaService.list(filters);
      setRondas(response.rondas || []);
      setPagination(response.pagination || {
        page: 1,
        pages: 1,
        total: 0,
        per_page: 10,
        has_next: false,
        has_prev: false
      });
    } catch (error) {
      console.error('Erro ao carregar rondas:', error);
      setError('Erro ao carregar rondas. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field: string, value: string | number) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      page: 1 // Reset para primeira página ao filtrar
    }));
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const clearFilters = () => {
    setFilters({
      condominio: '',
      supervisor: '',
      turno: '',
      data_inicio: '',
      data_fim: '',
      page: 1,
      per_page: 10
    });
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: ptBR });
    } catch {
      return 'N/A';
    }
  };

  if (loading) {
    return <LoadingSpinner message="Carregando rondas..." size="large" />;
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{
            fontWeight: 600,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            📋 Histórico de Rondas
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Visualize todas as rondas registradas no sistema
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/rondas/nova')}
          sx={{
            borderRadius: 2,
            px: 3,
            py: 1.5,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
            '&:hover': {
              background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`
            }
          }}
        >
          Registrar Nova Ronda
        </Button>
      </Box>

      {/* Filtros */}
      <Card sx={{ mb: 3, borderRadius: 3, boxShadow: theme.shadows[2] }}>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FilterIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Filtros
              </Typography>
            </Box>
          }
          sx={{
            backgroundColor: alpha(theme.palette.primary.main, 0.05),
            borderBottom: `1px solid ${theme.palette.divider}`
          }}
        />
        <CardContent>
          <Grid container spacing={3} alignItems="end">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Condomínio</InputLabel>
                <Select
                  value={filters.condominio}
                  onChange={(e) => handleFilterChange('condominio', e.target.value)}
                  label="Condomínio"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {condominios.map((condominio) => (
                    <MenuItem key={condominio.id} value={condominio.nome}>
                      {condominio.nome}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Supervisor</InputLabel>
                <Select
                  value={filters.supervisor}
                  onChange={(e) => handleFilterChange('supervisor', e.target.value)}
                  label="Supervisor"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {supervisors.map((supervisor) => (
                    <MenuItem key={supervisor.id} value={supervisor.id}>
                      {supervisor.username}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Turno</InputLabel>
                <Select
                  value={filters.turno}
                  onChange={(e) => handleFilterChange('turno', e.target.value)}
                  label="Turno"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {turnos.map((turno) => (
                    <MenuItem key={turno} value={turno}>
                      {turno}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="Data Início"
                type="date"
                value={filters.data_inicio}
                onChange={(e) => handleFilterChange('data_inicio', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="Data Fim"
                type="date"
                value={filters.data_fim}
                onChange={(e) => handleFilterChange('data_fim', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={loadRondas}
                  fullWidth
                  sx={{ borderRadius: 2 }}
                >
                  Filtrar
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={clearFilters}
                  sx={{ borderRadius: 2 }}
                >
                  Limpar
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabela de Rondas */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {rondas.length > 0 ? (
        <Card sx={{ borderRadius: 3, overflow: 'hidden', boxShadow: theme.shadows[2] }}>
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: alpha(theme.palette.primary.main, 0.05) }}>
                  <TableCell sx={{ fontWeight: 600 }}>#ID</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Condomínio</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Data Plantão</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Turno</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Supervisor</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600 }}>Rondas no Log</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rondas.map((ronda) => (
                  <TableRow key={ronda.id} hover>
                    <TableCell>{ronda.id}</TableCell>
                    <TableCell>{ronda.condominio?.nome || 'N/A'}</TableCell>
                    <TableCell>{formatDate(ronda.data_plantao || '')}</TableCell>
                    <TableCell>
                      <Chip
                        label={ronda.turno || 'N/A'}
                        size="small"
                        color="secondary"
                        sx={{ borderRadius: 2 }}
                      />
                    </TableCell>
                    <TableCell>{ronda.supervisor?.username || 'Automático'}</TableCell>
                    <TableCell align="center">{ronda.total_rondas_no_log || 0}</TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Tooltip title="Ver Detalhes">
                          <IconButton
                            color="info"
                            onClick={() => navigate(`/rondas/${ronda.id}`)}
                            sx={{
                              backgroundColor: alpha(theme.palette.info.main, 0.1),
                              '&:hover': { backgroundColor: alpha(theme.palette.info.main, 0.2) }
                            }}
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Editar Ronda">
                          <IconButton
                            color="warning"
                            onClick={() => navigate(`/rondas/${ronda.id}/editar`)}
                            sx={{
                              backgroundColor: alpha(theme.palette.warning.main, 0.1),
                              '&:hover': { backgroundColor: alpha(theme.palette.warning.main, 0.2) }
                            }}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Excluir Ronda">
                          <IconButton
                            color="error"
                            onClick={() => {
                              if (window.confirm('Tem certeza que deseja excluir esta ronda?')) {
                                // Implementar exclusão
                              }
                            }}
                            sx={{
                              backgroundColor: alpha(theme.palette.error.main, 0.1),
                              '&:hover': { backgroundColor: alpha(theme.palette.error.main, 0.2) }
                            }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
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
              />
            </Box>
          )}
        </Card>
      ) : (
        <Card sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Typography variant="h5" color="text.secondary" gutterBottom>
            Nenhuma ronda encontrada
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Tente ajustar os filtros ou limpar a pesquisa
          </Typography>
          <Button variant="outlined" onClick={clearFilters}>
            Limpar Filtros
          </Button>
        </Card>
      )}
    </Box>
  );
};

export default RondasPage; 