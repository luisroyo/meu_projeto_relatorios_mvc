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
  alpha,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import LoadingSpinner from '../components/LoadingSpinner';
import { paradaService, condominioService, userService } from '../services/api';
import type { Parada } from '../types';

const ParadasPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [paradas, setParadas] = useState<Parada[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    total_paradas: 0,
    duracao_total: 0,
    duracao_media: 0,
    supervisor_mais_ativo: 'N/A'
  });
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
    per_page: 10,
    has_next: false,
    has_prev: false
  });

  // Filtros
  const [filters, setFilters] = useState({
    condominio: '',
    supervisor: '',
    turno: '',
    data_inicio: '',
    data_fim: '',
    page: 1,
    per_page: 10
  });

  // Filtros temporários para digitação (evita chamadas redundantes de API e problemas de digitação)
  const [tempFilters, setTempFilters] = useState({
    condominio: '',
    supervisor: '',
    data_inicio: '',
    data_fim: '',
  });

  // Dados para filtros
  const [condominios, setCondominios] = useState<Array<{ id: number; nome: string }>>([]);
  const [supervisors, setSupervisors] = useState<Array<{ id: number; username: string }>>([]);
  const [turnos, setTurnos] = useState<string[]>([]);

  // Estados para Upload
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  useEffect(() => {
    loadFilterData();
  }, []);

  useEffect(() => {
    loadParadas();
  }, [filters]);

  useEffect(() => {
    // Carregar bibliotecas do Google Drive Picker
    const gapiScript = document.createElement('script');
    gapiScript.src = 'https://apis.google.com/js/api.js';
    gapiScript.async = true;
    gapiScript.defer = true;
    gapiScript.onload = () => {
      (window as any).gapi.load('picker', { 'callback': () => { (window as any).pickerApiLoaded = true; } });
    };
    document.body.appendChild(gapiScript);

    const gisScript = document.createElement('script');
    gisScript.src = 'https://accounts.google.com/gsi/client';
    gisScript.async = true;
    gisScript.defer = true;
    document.body.appendChild(gisScript);

    return () => {
      document.body.removeChild(gapiScript);
      document.body.removeChild(gisScript);
    };
  }, []);

  const loadFilterData = async () => {
    try {
      const [condominiosData, usersData] = await Promise.all([
        condominioService.list(),
        userService.list()
      ]);

      const condos = Array.isArray(condominiosData) ? condominiosData : ((condominiosData as any)?.condominios || []);
      const users = Array.isArray(usersData) ? usersData : ((usersData as any)?.users || []);

      setCondominios(condos);
      setSupervisors(users.filter((user: any) => user.is_supervisor === true || user.is_admin === true));
    } catch (error) {
      console.error('Erro ao carregar dados dos filtros:', error);
    }
  };

  const loadParadas = async () => {
    try {
      setLoading(true);
      setError(null);

      const serviceFilters = {
        page: filters.page,
        per_page: filters.per_page,
        condominio_id: filters.condominio ? Number(filters.condominio) : undefined,
        supervisor_id: filters.supervisor ? Number(filters.supervisor) : undefined,
        turno: filters.turno || undefined,
        data_inicio: filters.data_inicio || undefined,
        data_fim: filters.data_fim || undefined
      };

      const response = await paradaService.list(serviceFilters);
      setParadas(response.paradas || []);
      setStats(response.stats || {
        total_paradas: 0,
        duracao_total: 0,
        duracao_media: 0,
        supervisor_mais_ativo: 'N/A'
      });
      setPagination(response.pagination || {
        page: 1,
        pages: 1,
        total: 0,
        per_page: 10,
        has_next: false,
        has_prev: false
      });
    } catch (err: any) {
      console.error('Erro ao carregar paradas:', err);
      setError('Erro ao carregar paradas. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field: string, value: string | number) => {
    setTempFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const applyFilters = () => {
    setFilters(prev => ({
      ...prev,
      ...tempFilters,
      page: 1
    }));
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const clearFilters = () => {
    const cleared = {
      condominio: '',
      supervisor: '',
      data_inicio: '',
      data_fim: '',
    };
    setTempFilters(cleared);
    setFilters(prev => ({
      ...prev,
      ...cleared,
      page: 1
    }));
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setUploadFile(file);
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile) return;

    setUploadLoading(true);
    try {
      const result = await paradaService.uploadParadaLog(uploadFile);

      if (result.success) {
        setUploadOpen(false);
        setUploadFile(null);
        loadParadas();
        alert(result.message || 'Arquivo processado com sucesso!');
      }
    } catch (err: any) {
      console.error('Erro no upload de paradas:', err);
      alert('Erro ao processar arquivo: ' + (err.message || 'Erro desconhecido'));
    } finally {
      setUploadLoading(false);
    }
  };

  const handleGoogleDriveClick = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const apiKey = import.meta.env.VITE_GOOGLE_API_KEY;

    if (!clientId || !apiKey) {
      alert("Credenciais do Google Drive não configuradas no ambiente.");
      return;
    }

    if (!(window as any).google) {
      alert("Biblioteca do Google API não carregada.");
      return;
    }

    const tokenClient = (window as any).google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: 'https://www.googleapis.com/auth/drive.readonly',
      callback: async (response: any) => {
        if (response.error !== undefined) {
          console.error("Erro na autenticação:", response);
          return;
        }
        const token = response.access_token;
        
        const createPicker = () => {
          const docsView = new (window as any).google.picker.DocsView()
            .setIncludeFolders(true)
            .setMimeTypes("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");

          const picker = new (window as any).google.picker.PickerBuilder()
            .addView(docsView)
            .setOAuthToken(token)
            .setDeveloperKey(apiKey)
            .setCallback(async (data: any) => {
              if (data[(window as any).google.picker.Response.ACTION] === (window as any).google.picker.Action.PICKED) {
                const doc = data[(window as any).google.picker.Response.DOCUMENTS][0];
                const fileId = doc[(window as any).google.picker.Document.ID];
                const fileName = doc[(window as any).google.picker.Document.NAME];
                
                await handleGoogleDriveImport(fileId, token, fileName);
              }
            })
            .setTitle("Selecione o arquivo de Paradas")
            .build();
          picker.setVisible(true);
        };

        if (!(window as any).pickerApiLoaded && (window as any).gapi) {
          (window as any).gapi.load('picker', {
            'callback': () => {
              (window as any).pickerApiLoaded = true;
              createPicker();
            }
          });
        } else {
          createPicker();
        }
      },
    });

    tokenClient.requestAccessToken({ prompt: 'consent' });
  };

  const handleGoogleDriveImport = async (fileId: string, token: string, fileName: string) => {
    setUploadLoading(true);
    try {
      const result = await paradaService.uploadParadaFromGoogleDrive(fileId, token, fileName);

      if (result.success) {
        setUploadOpen(false);
        setUploadFile(null);
        loadParadas();
        alert(result.message || 'Arquivo do Google Drive importado com sucesso!');
      }
    } catch (err: any) {
      console.error('Erro no upload via Google Drive:', err);
      alert('Erro ao processar do Google Drive: ' + (err.message || 'Erro desconhecido'));
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Tem certeza que deseja excluir este registro de parada?')) return;
    try {
      const result = await paradaService.delete(id);
      if (result.success) {
        loadParadas();
        alert('Registro de parada excluído com sucesso.');
      }
    } catch (err: any) {
      alert('Erro ao excluir registro: ' + (err.message || 'Erro desconhecido'));
    }
  };

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
            🛑 Histórico de Paradas
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Gerencie e analise os registros de paradas e pontos fixos de segurança
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            startIcon={<CloudUploadIcon />}
            onClick={() => setUploadOpen(true)}
            color="secondary"
            sx={{ borderRadius: 2 }}
          >
            Importar Relatório
          </Button>
        </Stack>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3, borderLeft: `5px solid ${theme.palette.primary.main}` }}>
            <CardContent>
              <Typography color="text.secondary" variant="body2" fontWeight={600}>Total de Paradas</Typography>
              <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>{stats.total_paradas}</Typography>
              <Typography variant="caption" color="text.secondary">Contabilizadas no log</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3, borderLeft: `5px solid ${theme.palette.success.main}` }}>
            <CardContent>
              <Typography color="text.secondary" variant="body2" fontWeight={600}>Duração Total</Typography>
              <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>{stats.duracao_total} min</Typography>
              <Typography variant="caption" color="text.secondary">Tempo total estacionado</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3, borderLeft: `5px solid ${theme.palette.info.main}` }}>
            <CardContent>
              <Typography color="text.secondary" variant="body2" fontWeight={600}>Média por Parada</Typography>
              <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>{stats.duracao_media} min</Typography>
              <Typography variant="caption" color="text.secondary">Duração média de parada</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3, borderLeft: `5px solid ${theme.palette.warning.main}` }}>
            <CardContent>
              <Typography color="text.secondary" variant="body2" fontWeight={600}>Supervisor em Destaque</Typography>
              <Typography variant="h5" fontWeight={700} sx={{ my: 1.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {stats.supervisor_mais_ativo}
              </Typography>
              <Typography variant="caption" color="text.secondary">Com mais paradas registradas</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
                  value={tempFilters.condominio}
                  onChange={(e) => handleFilterChange('condominio', e.target.value)}
                  label="Condomínio"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {condominios.map((c) => (
                    <MenuItem key={c.id} value={c.id}>{c.nome}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Supervisor</InputLabel>
                <Select
                  value={tempFilters.supervisor}
                  onChange={(e) => handleFilterChange('supervisor', e.target.value)}
                  label="Supervisor"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {supervisors.map((s) => (
                    <MenuItem key={s.id} value={s.id}>{s.username}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="Data Início"
                type="date"
                value={tempFilters.data_inicio}
                onChange={(e) => handleFilterChange('data_inicio', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="Data Fim"
                type="date"
                value={tempFilters.data_fim}
                onChange={(e) => handleFilterChange('data_fim', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                  onClick={applyFilters}
                  disabled={loading}
                  fullWidth
                  sx={{ borderRadius: 2 }}
                >
                  Filtrar
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={clearFilters}
                  disabled={loading}
                  sx={{ borderRadius: 2 }}
                >
                  Limpar
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabela de Paradas */}
      {loading && <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}

      {paradas.length > 0 ? (
        <Card sx={{ borderRadius: 3, overflow: 'hidden', boxShadow: theme.shadows[2] }}>
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: alpha(theme.palette.primary.main, 0.05) }}>
                  <TableCell sx={{ fontWeight: 600 }}>#ID</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Condomínio</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Data do Plantão</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Escala</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Turno</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Supervisor</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600 }}>Paradas</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600 }}>Duração Total</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paradas.map((p) => (
                  <TableRow key={p.id} hover>
                    <TableCell>{p.id}</TableCell>
                    <TableCell>{p.condominio?.nome || 'N/A'}</TableCell>
                    <TableCell>{formatDate(p.data_plantao_parada)}</TableCell>
                    <TableCell>{p.escala_plantao || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip
                        label={p.turno_parada || 'N/A'}
                        size="small"
                        color="secondary"
                        variant="outlined"
                        sx={{ borderRadius: 2 }}
                      />
                    </TableCell>
                    <TableCell>{p.supervisor?.username || 'Automático'}</TableCell>
                    <TableCell align="center">{p.total_paradas_no_log || 0}</TableCell>
                    <TableCell align="center">{p.duracao_minutos || 0} min</TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Tooltip title="Ver Detalhes">
                          <IconButton
                            color="info"
                            onClick={() => navigate(`/paradas/${p.id}`)}
                            sx={{
                              backgroundColor: alpha(theme.palette.info.main, 0.1),
                              '&:hover': { backgroundColor: alpha(theme.palette.info.main, 0.2) }
                            }}
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Excluir Parada">
                          <IconButton
                            color="error"
                            onClick={() => handleDelete(p.id)}
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
            Nenhum registro de parada encontrado
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Tente carregar um novo relatório ou ajustar os filtros
          </Typography>
          <Button variant="outlined" onClick={clearFilters}>
            Limpar Filtros
          </Button>
        </Card>
      )}

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Importar Relatório de Paradas (Excel)</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <Typography variant="body2" color="text.secondary">
              Selecione o arquivo Excel (.xlsx) de controle de paradas para processamento em lote.
            </Typography>

            <Button
              variant="outlined"
              component="label"
              startIcon={<CloudUploadIcon />}
              fullWidth
              sx={{ py: 2.5, borderStyle: 'dashed' }}
            >
              {uploadFile ? uploadFile.name : 'Selecionar Arquivo (.xlsx)'}
              <input
                type="file"
                hidden
                accept=".xlsx"
                onChange={handleFileChange}
              />
            </Button>

            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', my: 0.5 }}>
              ou
            </Typography>

            <Button
              variant="outlined"
              onClick={handleGoogleDriveClick}
              color="info"
              fullWidth
              sx={{ py: 2, borderStyle: 'solid' }}
            >
              Selecionar do Google Drive
            </Button>


          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={() => setUploadOpen(false)}>Cancelar</Button>
          <Button
            onClick={handleUploadSubmit}
            variant="contained"
            disabled={!uploadFile || uploadLoading}
            startIcon={uploadLoading && <CircularProgress size={20} color="inherit" />}
          >
            {uploadLoading ? 'Processando...' : 'Enviar e Processar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ParadasPage;
