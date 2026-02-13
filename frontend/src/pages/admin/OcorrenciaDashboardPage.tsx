import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchOcorrenciaDashboard, setFilters } from '../../store/slices/adminSlice';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Container,
    Alert,
} from '@mui/material';
import { MetricsCard } from '../../components/charts';
import { FilterPanel } from '../../components/admin';
import { LineChart, BarChart, PieChart } from '../../components/charts';

const OcorrenciaDashboardPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { ocorrenciaDashboard, loading, error, filters } = useAppSelector((state) => state.admin);

    useEffect(() => {
        dispatch(fetchOcorrenciaDashboard(filters));
    }, [dispatch, filters]);

    const handleFilterChange = (newFilters: any) => {
        dispatch(setFilters(newFilters));
    };

    if (loading) {
        return (
            <Container maxWidth="xl">
                <Box sx={{ mt: 4, mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        Carregando dashboard de ocorrências...
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
                    Dashboard de Ocorrências
                </Typography>

                <FilterPanel onFilterChange={handleFilterChange} />

                {/* Cards de Métricas */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
                    <MetricsCard
                        title="Total de Ocorrências"
                        value={ocorrenciaDashboard?.total_ocorrencias || 0}
                        subtitle="Este período"
                        trend={ocorrenciaDashboard?.crescimento_ocorrencias || 0}
                    />
                    <MetricsCard
                        title="Ocorrências Pendentes"
                        value={ocorrenciaDashboard?.ocorrencias_pendentes || 0}
                        subtitle="Aguardando resolução"
                        color="warning"
                    />
                    <MetricsCard
                        title="Ocorrências por Dia"
                        value={ocorrenciaDashboard?.ocorrencias_por_dia || 0}
                        subtitle="Média diária"
                        trend={ocorrenciaDashboard?.crescimento_diario || 0}
                    />
                    <MetricsCard
                        title="Tempo Médio Resolução"
                        value={`${ocorrenciaDashboard?.tempo_medio_resolucao || 0}h`}
                        subtitle="Tempo médio"
                        trend={ocorrenciaDashboard?.crescimento_tempo_resolucao || 0}
                    />
                </Box>

                {/* Gráficos */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                    {/* Gráfico de Ocorrências por Tipo */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Ocorrências por Tipo
                            </Typography>
                            {ocorrenciaDashboard?.ocorrencias_por_tipo && (
                                <BarChart
                                    data={ocorrenciaDashboard.ocorrencias_por_tipo.map(item => ({
                                        label: item.tipo,
                                        value: item.quantidade
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Ocorrências por Condomínio */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Ocorrências por Condomínio
                            </Typography>
                            {ocorrenciaDashboard?.ocorrencias_por_condominio && (
                                <PieChart
                                    title="Ocorrências por Condomínio"
                                    data={ocorrenciaDashboard.ocorrencias_por_condominio.map(item => ({
                                        label: item.condominio,
                                        value: item.quantidade
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
                                    Evolução de Ocorrências (Últimos 30 dias)
                                </Typography>
                                {/* Temporariamente comentado até o backend fornecer os dados
                {ocorrenciaDashboard?.evolucao_temporal && (
                  <LineChart
                    data={ocorrenciaDashboard.evolucao_temporal.map(item => ({
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

                    {/* Gráfico de Status das Ocorrências */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Status das Ocorrências
                            </Typography>
                            {ocorrenciaDashboard?.status_ocorrencias && (
                                <PieChart
                                    title="Status das Ocorrências"
                                    data={ocorrenciaDashboard.status_ocorrencias.map(item => ({
                                        label: item.status,
                                        value: item.quantidade
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Ocorrências por Supervisor */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Ocorrências por Supervisor
                            </Typography>
                            {ocorrenciaDashboard?.ocorrencias_por_supervisor && (
                                <BarChart
                                    data={ocorrenciaDashboard.ocorrencias_por_supervisor.map(item => ({
                                        label: item.supervisor,
                                        value: item.quantidade
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Prioridade das Ocorrências */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Ocorrências por Prioridade
                            </Typography>
                            {ocorrenciaDashboard?.ocorrencias_por_prioridade && (
                                <BarChart
                                    data={ocorrenciaDashboard.ocorrencias_por_prioridade.map(item => ({
                                        label: item.prioridade,
                                        value: item.quantidade
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>

                    {/* Gráfico de Tempo de Resolução */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Tempo de Resolução por Tipo
                            </Typography>
                            {ocorrenciaDashboard?.tempo_resolucao_por_tipo && (
                                <BarChart
                                    data={ocorrenciaDashboard.tempo_resolucao_por_tipo.map(item => ({
                                        label: item.tipo,
                                        value: item.tempo_medio
                                    }))}
                                    height={300}
                                />
                            )}
                        </CardContent>
                    </Card>
                </Box>
            </Box>
        </Container>
    );
};

export default OcorrenciaDashboardPage; 