import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Paper,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CalendarToday as CalendarIcon,
  Schedule as ScheduleIcon,
  Badge as BadgeIcon,
  People as PeopleIcon,
  Dns as DnsIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import LoadingSpinner from '../components/LoadingSpinner';
import { paradaService } from '../services/api';
import type { Parada } from '../types';

const ParadaDetailsPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [parada, setParada] = useState<Parada | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadParadaDetails();
  }, [id]);

  const loadParadaDetails = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const response = await paradaService.get(Number(id));
      setParada(response.parada || null);
    } catch (err: any) {
      console.error('Erro ao obter detalhes da parada:', err);
      setError('Erro ao carregar detalhes da parada. Ela pode ter sido removida ou não existir.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return <LoadingSpinner message="Carregando detalhes..." size="large" />;
  }

  if (error || !parada) {
    return (
      <Box sx={{ p: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/paradas')} sx={{ mb: 3 }}>
          Voltar para Paradas
        </Button>
        <Card sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Typography variant="h5" color="error" gutterBottom>
            Erro ao Carregar Detalhes
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {error || 'Não foi possível encontrar o registro.'}
          </Typography>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/paradas')}
          sx={{ borderRadius: 2 }}
        >
          Voltar
        </Button>
        <Typography variant="h4" component="h1" fontWeight={600}>
          Detalhes da Parada #{parada.id}
        </Typography>
      </Box>

      {/* Main Grid */}
      <Grid container spacing={3}>
        {/* Info Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom color="primary">
                Informações do Plantão
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Stack spacing={2.5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <DnsIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Condomínio</Typography>
                    <Typography variant="body1" fontWeight={600}>{parada.condominio?.nome || 'N/A'}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <CalendarIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Data do Plantão</Typography>
                    <Typography variant="body1" fontWeight={600}>{formatDate(parada.data_plantao_parada)}</Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <ScheduleIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Escala / Turno</Typography>
                    <Typography variant="body1" fontWeight={600}>
                      {parada.escala_plantao || 'N/A'}{' '}
                      {parada.turno_parada && (
                        <Chip label={parada.turno_parada} size="small" color="secondary" sx={{ ml: 1, height: 20 }} />
                      )}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <BadgeIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Supervisor Responsável</Typography>
                    <Typography variant="body1" fontWeight={600}>{parada.supervisor?.username || 'Automático'}</Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <PeopleIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Importado Por</Typography>
                    <Typography variant="body1" fontWeight={600}>{parada.user || 'Sistema'}</Typography>
                  </Box>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">Data de Importação</Typography>
                  <Typography variant="body2">{formatDateTime(parada.data_criacao)}</Typography>
                </Box>
              </Stack>

              <Divider sx={{ my: 3 }} />

              <Typography variant="h6" fontWeight={600} gutterBottom color="primary">
                Métricas Consolidadas
              </Typography>
              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Paper sx={{ p: 2, flex: 1, textAlign: 'center', backgroundColor: alpha(theme.palette.primary.main, 0.03), borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">Paradas</Typography>
                  <Typography variant="h5" fontWeight={700} color="primary">{parada.total_paradas_no_log}</Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1, textAlign: 'center', backgroundColor: alpha(theme.palette.success.main, 0.03), borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">Tempo Parado</Typography>
                  <Typography variant="h5" fontWeight={700} color="success.main">{parada.duracao_minutos} min</Typography>
                </Paper>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Processed Report & Raw Logs */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3} sx={{ height: '100%' }}>
            {/* Relatório Processado */}
            <Card sx={{ borderRadius: 3, flex: 1 }}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Typography variant="h6" fontWeight={600} gutterBottom color="primary">
                  Relatório Processado de Paradas
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box
                  component="pre"
                  sx={{
                    flex: 1,
                    p: 2.5,
                    m: 0,
                    borderRadius: 2,
                    backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    color: theme.palette.text.primary,
                    border: `1px solid ${theme.palette.divider}`,
                    maxHeight: '400px'
                  }}
                >
                  {parada.relatorio_processado || 'Nenhum relatório gerado.'}
                </Box>
              </CardContent>
            </Card>

            {/* Log Bruto */}
            <Card sx={{ borderRadius: 3, flex: 1 }}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Typography variant="h6" fontWeight={600} gutterBottom color="primary">
                  Log Bruto de Mensagens
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box
                  component="pre"
                  sx={{
                    flex: 1,
                    p: 2.5,
                    m: 0,
                    borderRadius: 2,
                    backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f8f9fa',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    color: theme.palette.text.secondary,
                    border: `1px solid ${theme.palette.divider}`,
                    maxHeight: '300px'
                  }}
                >
                  {parada.log_parada_bruto || 'Nenhum log bruto disponível.'}
                </Box>
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ParadaDetailsPage;
