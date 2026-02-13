import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchRondaDashboard, setFilters, clearFilters } from '../../store/slices/adminSlice';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Paper,
    Container,
    Alert,
} from '@mui/material';
import { MetricsCard } from '../../components/charts';
import { FilterPanel } from '../../components/admin';
import { LineChart, BarChart, PieChart } from '../../components/charts';

const RondaDashboardPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { rondaDashboard, loading, error, filters } = useAppSelector((state) => state.admin);

    useEffect(() => {
        dispatch(fetchRondaDashboard({ filters }));
    }, [dispatch, filters]);

    const handleFiltersChange = (newFilters: any) => {
        dispatch(setFilters(newFilters));
    };

    const handleApplyFilters = () => {
        // Os filtros são aplicados automaticamente via useEffect
    };

    const handleClearFilters = () => {
        dispatch(clearFilters());
    };

    if (loading) {
        return (
            <Container maxWidth="xl">
                <Box sx={{ mt: 4, mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        Carregando dashboard de rondas...
                    </Typography>
                </Box>
            </Container>
        );
    }

    if (error) {
        return (
            <Container maxWidth="xl">
                <Box sx={{ mt: 4, mb: 4 }}>
                    <Alert severity="error">{error}</Alert>
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="xl">
            <Box sx={{ mt: 4, mb: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Dashboard de Rondas
                </Typography>

                <FilterPanel
                    filters={filters}
                    onFiltersChange={handleFiltersChange}
                    onApplyFilters={handleApplyFilters}
                    onClearFilters={handleClearFilters}
                    showDateRange={true}
                    showCondominio={true}
                    showSupervisor={true}
                />

                {/* Cards de Métricas */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
                    <MetricsCard
                        title="Total de Rondas"
                        value={rondaDashboard?.total_rondas || 0}
                        subtitle="Este período"
                        trend={rondaDashboard?.crescimento_rondas || 0}
                    />
                    <MetricsCard
                        title="Duração Média"
                        value={`${rondaDashboard?.duracao_media || 0} min`}
                        subtitle="Por ronda"
                        trend={rondaDashboard?.crescimento_duracao || 0}
                    />
                    <MetricsCard
                        title="Rondas por Dia"
                        value={rondaDashboard?.rondas_por_dia || 0}
                        subtitle="Média diária"
                        trend={rondaDashboard?.crescimento_diario || 0}
                    />
                    <MetricsCard
                        title="Supervisores Ativos"
                        value={rondaDashboard?.supervisores_ativos || 0}
                        subtitle="Este mês"
                    />
                </Box>

                {/* Gráficos */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                    {/* Gráfico de Rondas por Condomínio */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Rondas por Condomínio
                            </Typography>
                            {rondaDashboard?.rondas_por_condominio && (
                                <BarChart
                                    data={rondaDashboard.rondas_por_condominio.map(item => ({
                                        label: item.condominio,
                                        value: item.total
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Rondas por Turno */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Rondas por Turno
                            </Typography>
                            {rondaDashboard?.rondas_por_turno && (
                                <PieChart
                                    title="Rondas por Turno"
                                    data={rondaDashboard.rondas_por_turno.map(item => ({
                                        label: item.turno,
                                        value: item.total
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Evolução Temporal */}
                    <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Evolução de Rondas (Últimos 30 dias)
                                </Typography>
                                {/* Temporariamente comentado até o backend fornecer os dados
                {rondaDashboard?.evolucao_temporal && (
                  <LineChart
                    data={rondaDashboard.evolucao_temporal.map(item => ({
                      label: item.data,
                      value: item.quantidade
                    }))}
                    height={400}
                  />
                )}
                */}
                            </CardContent>
                        </Card>
                    </Box>

                    {/* Gráfico de Duração por Supervisor */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Duração Média por Supervisor
                            </Typography>
                            {/* Temporariamente comentado até o backend fornecer os dados
                {rondaDashboard?.duracao_por_supervisor && (
                  <BarChart
                    data={rondaDashboard.duracao_por_supervisor.map(item => ({
                      label: item.supervisor,
                      value: item.duracao_media
                    }))}
                    height={300}
                  />
                )}
                */}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Status das Rondas */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Status das Rondas
                            </Typography>
                            {/* Temporariamente comentado até o backend fornecer os dados
                {rondaDashboard?.status_rondas && (
                  <PieChart
                    title="Status das Rondas"
                    data={rondaDashboard.status_rondas.map(item => ({
                      label: item.status,
                      value: item.quantidade
                    }))}
                    height={300}
                  />
                )}
                */}
                        </CardContent>
                    </Card>
                </Box>
            </Box>
        </Container>
    );
};

export default RondaDashboardPage; 