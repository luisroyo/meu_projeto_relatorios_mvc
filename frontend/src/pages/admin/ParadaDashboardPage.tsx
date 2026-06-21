import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Container,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Button
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Timeline as TimelineIcon,
  Schedule as ScheduleIcon,
  LocationCity as CondoIcon
} from '@mui/icons-material';
import { MetricsCard, BarChart, LineChart, PieChart } from '../../components/charts';
import { paradaService, condominioService } from '../../services/api';
import type { ParadaDashboardData } from '../../types';
import LoadingSpinner from '../../components/LoadingSpinner';

const ParadaDashboardPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<ParadaDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtros
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [condominioId, setCondominioId] = useState<string>('');
  
  // Listas para filtros
  const [condominios, setCondominios] = useState<Array<{ id: number; nome: string }>>([]);

  useEffect(() => {
    loadCondominios();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [year, condominioId]);

  const loadCondominios = async () => {
    try {
      const response = await condominioService.list();
      const condos = Array.isArray(response) ? response : (response?.condominios || []);
      setCondominios(condos);
    } catch (err) {
      console.error('Erro ao carregar condomínios no dashboard:', err);
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await paradaService.getDashboardStats(
        year,
        condominioId ? Number(condominioId) : undefined
      );
      
      if (response.success && response.data) {
        setDashboardData(response.data);
      } else {
        setError(response.message || 'Erro ao carregar estatísticas do dashboard.');
      }
    } catch (err: any) {
      console.error('Erro ao buscar dados do dashboard de paradas:', err);
      setError('Erro de conexão ao servidor. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setYear(new Date().getFullYear());
    setCondominioId('');
  };

  if (loading && !dashboardData) {
    return <LoadingSpinner message="Carregando estatísticas do dashboard..." size="large" />;
  }

  // Anos disponíveis para filtro
  const availableYears = [
    new Date().getFullYear() - 2,
    new Date().getFullYear() - 1,
    new Date().getFullYear(),
    new Date().getFullYear() + 1
  ];

  // Preparar dados para gráficos
  const trendCountData = dashboardData?.historico.meses.map((mes, idx) => ({
    x: mes,
    y: dashboardData.historico.count[idx] || 0
  })) || [];

  const trendDurationData = dashboardData?.historico.meses.map((mes, idx) => ({
    label: mes,
    value: dashboardData.historico.duracao[idx] || 0
  })) || [];

  const condoBreakdownData = dashboardData?.breakdown.condominios.map(item => ({
    label: item.name,
    value: item.value
  })) || [];

  const supervisorBreakdownData = dashboardData?.breakdown.supervisores.map(item => ({
    label: item.name,
    value: item.value
  })) || [];

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={600} gutterBottom>
          Dashboard de Paradas 🛑
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Estatísticas e análise detalhada dos pontos fixos de segurança
        </Typography>
      </Box>

      {/* Filtros */}
      <Card sx={{ mb: 4, borderRadius: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Ano</InputLabel>
                <Select
                  value={year}
                  onChange={(e) => setYear(Number(e.target.value))}
                  label="Ano"
                >
                  {availableYears.map(y => (
                    <MenuItem key={y} value={y}>{y}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Condomínio</InputLabel>
                <Select
                  value={condominioId}
                  onChange={(e) => setCondominioId(e.target.value)}
                  label="Condomínio"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {condominios.map((c) => (
                    <MenuItem key={c.id} value={c.id}>{c.nome}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={3}>
              <Stack direction="row" spacing={1}>
                <Button 
                  variant="outlined" 
                  onClick={handleClearFilters}
                  fullWidth
                  size="medium"
                  sx={{ borderRadius: 2 }}
                >
                  Limpar Filtros
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 4, borderRadius: 2 }}>{error}</Alert>
      )}

      {dashboardData && (
        <Box>
          {/* KPI Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={4}>
              <MetricsCard
                title="Total de Paradas no Ano"
                value={dashboardData.stats.total_paradas}
                subtitle={`Ano de ${year}`}
                color="primary"
                icon={<BarChartIcon />}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <MetricsCard
                title="Tempo Total Parado"
                value={`${dashboardData.stats.duracao_total} min`}
                subtitle="Duração em minutos"
                color="success"
                icon={<ScheduleIcon />}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <MetricsCard
                title="Duração Média por Parada"
                value={`${dashboardData.stats.duracao_media} min`}
                subtitle="Média por ocorrência de ponto fixo"
                color="info"
                icon={<TimelineIcon />}
              />
            </Grid>
          </Grid>

          {/* Gráficos de Tendência */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <LineChart
                data={trendCountData}
                title="Tendência Mensal: Quantidade de Paradas"
                xAxisLabel="Mês"
                yAxisLabel="Paradas"
                color="#8884d8"
                height={350}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <BarChart
                data={trendDurationData}
                title="Tendência Mensal: Duração Total Estacionado (minutos)"
                xAxisLabel="Mês"
                yAxisLabel="Minutos"
                color="#82ca9d"
                height={350}
              />
            </Grid>
          </Grid>

          {/* Gráficos de Distribuição */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <PieChart
                data={condoBreakdownData}
                title="Distribuição de Paradas por Condomínio"
                height={350}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <PieChart
                data={supervisorBreakdownData}
                title="Distribuição de Paradas por Supervisor"
                height={350}
              />
            </Grid>
          </Grid>
        </Box>
      )}
    </Container>
  );
};

export default ParadaDashboardPage;
