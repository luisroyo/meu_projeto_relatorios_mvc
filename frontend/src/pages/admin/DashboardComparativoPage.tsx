import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchComparativoDashboard, setFilters, clearFilters } from '../../store/slices/adminSlice';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Paper,
    Container,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Stack,
    Divider,
    CardHeader,
} from '@mui/material';
import {
    Shield,
    StopCircle,
    WarningAmber,
    TrendingUp,
    BarChart as BarChartIcon,
} from '@mui/icons-material';
import { MetricsCard } from '../../components/charts';
import { FilterPanel } from '../../components/admin';
import { BarChart, LineChart } from '../../components/charts';
import { BarChart as MuiBarChart } from '@mui/x-charts/BarChart';

const DashboardComparativoPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { comparativoDashboard, loading, error, filters } = useAppSelector((state) => state.admin);

    // Estado local para armazenar o modo de comparação do filtro
    const [comparisonMode, setComparisonMode] = useState<string>('all');

    useEffect(() => {
        dispatch(fetchComparativoDashboard({ filters }));
    }, [dispatch, filters]);

    const handleFiltersChange = (newFilters: any) => {
        dispatch(setFilters(newFilters));
    };

    const handleApplyFilters = () => {
        // Os filtros são aplicados automaticamente via useEffect ao alterar a store
    };

    const handleClearFilters = () => {
        dispatch(clearFilters());
    };

    if (loading) {
        return (
            <Container maxWidth="xl">
                <Box sx={{ mt: 4, mb: 4, textAlign: 'center', py: 8 }}>
                    <Typography variant="h5" color="text.secondary">
                        Carregando análise comparativa...
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

    // Adaptando dados retornados da API
    const data = comparativoDashboard?.success === false ? null : comparativoDashboard?.data || comparativoDashboard;

    if (!data) {
        return (
            <Container maxWidth="xl">
                <Box sx={{ mt: 4, mb: 4 }}>
                    <Alert severity="info">Nenhum dado disponível para o período selecionado.</Alert>
                </Box>
            </Container>
        );
    }

    const {
        selected_year = new Date().getFullYear(),
        month_labels = [],
        rondas_data = [],
        ocorrencias_data = [],
        paradas_data = [],
        metrics = {},
        breakdown = {},
        filter_options = {}
    } = data;

    // Dados para o gráfico combinado principal
    const combinedSeries = [
        { data: rondas_data, label: 'Rondas', color: '#2563eb' },
        { data: paradas_data, label: 'Paradas', color: '#10b981' },
        { data: ocorrencias_data, label: 'Ocorrências', color: '#dc3545' }
    ];

    // Formatar meses do histórico de forma legível
    const monthlySummaryList = month_labels.map((label: string, index: number) => {
        const rondas = rondas_data[index] || 0;
        const ocorrencias = ocorrencias_data[index] || 0;
        const paradas = paradas_data[index] || 0;
        return {
            mes: label,
            rondas,
            paradas,
            ocorrencias,
            proporcaoOcorrencias: rondas > 0 ? ((ocorrencias / rondas) * 100).toFixed(1) + '%' : '-',
            proporcaoParadas: rondas > 0 ? ((paradas / rondas) * 100).toFixed(1) + '%' : '-'
        };
    });

    return (
        <Container maxWidth="xl">
            <Box sx={{ mt: 4, mb: 4 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" mb={3}>
                    <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
                        Análise Comparativa Operacional
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary" sx={{ bgcolor: 'action.selected', px: 2, py: 0.5, borderRadius: 1 }}>
                        Ano de Referência: {selected_year}
                    </Typography>
                </Box>

                {/* Filtros */}
                <FilterPanel
                    filters={filters}
                    onFiltersChange={handleFiltersChange}
                    onApplyFilters={handleApplyFilters}
                    onClearFilters={handleClearFilters}
                    showCondominio={true}
                    showSupervisor={true}
                    condominios={filter_options.condominios || []}
                    supervisores={filter_options.supervisors || []}
                />

                {/* KPI Cards Row */}
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} sm={6} md={4} lg={2.4}>
                        <MetricsCard
                            title="Total de Rondas"
                            value={metrics.total_rondas || 0}
                            subtitle={`Média: ${metrics.media_rondas_mensal || 0}/mês`}
                            icon={<Shield sx={{ fontSize: 32 }} />}
                            color="primary"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4} lg={2.4}>
                        <MetricsCard
                            title="Total de Paradas"
                            value={metrics.total_paradas || 0}
                            subtitle={`Média: ${metrics.media_paradas_mensal || 0}/mês`}
                            icon={<StopCircle sx={{ fontSize: 32 }} />}
                            color="success"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4} lg={2.4}>
                        <MetricsCard
                            title="Total de Ocorrências"
                            value={metrics.total_ocorrencias || 0}
                            subtitle={`Média: ${metrics.media_ocorrencias_mensal || 0}/mês`}
                            icon={<WarningAmber sx={{ fontSize: 32 }} />}
                            color="warning"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4} lg={2.4}>
                        <MetricsCard
                            title="Proporção Ocor./Rondas"
                            value={`${metrics.proporcao_ocorrencias_por_ronda || 0}%`}
                            subtitle="Ocorrências p/ 100 rondas"
                            icon={<TrendingUp sx={{ fontSize: 32 }} />}
                            color="info"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4} lg={2.4}>
                        <MetricsCard
                            title="Tendência Geral"
                            value={
                                metrics.tendencia_rondas === 'Crescimento' && metrics.tendencia_ocorrencias === 'Crescimento'
                                    ? 'Crescimento'
                                    : metrics.tendencia_rondas === 'Queda' && metrics.tendencia_ocorrencias === 'Queda'
                                    ? 'Queda'
                                    : 'Mista'
                            }
                            subtitle="Últimos vs 3 primeiros meses"
                            icon={<TrendingUp sx={{ fontSize: 32 }} />}
                            color="secondary"
                        />
                    </Grid>
                </Grid>

                {/* Gráfico Combinado Principal */}
                <Card sx={{ mb: 4 }}>
                    <CardHeader
                        avatar={<BarChartIcon color="primary" />}
                        title="Comparativo Mensal de Rondas, Paradas e Ocorrências"
                        titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
                    />
                    <CardContent>
                        <Box sx={{ width: '100%', height: 400, overflowX: 'auto' }}>
                            <MuiBarChart
                                height={380}
                                series={combinedSeries}
                                xAxis={[{ data: month_labels, scaleType: 'band' }]}
                            />
                        </Box>
                    </CardContent>
                </Card>

                {/* Gráficos Individuais Lado a Lado */}
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} md={4}>
                        <BarChart
                            title="Evolução Mensal de Rondas"
                            data={month_labels.map((l: string, i: number) => ({ label: l, value: rondas_data[i] || 0 }))}
                            color="#2563eb"
                            height={280}
                        />
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <BarChart
                            title="Evolução Mensal de Paradas"
                            data={month_labels.map((l: string, i: number) => ({ label: l, value: paradas_data[i] || 0 }))}
                            color="#10b981"
                            height={280}
                        />
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <BarChart
                            title="Evolução Mensal de Ocorrências"
                            data={month_labels.map((l: string, i: number) => ({ label: l, value: ocorrencias_data[i] || 0 }))}
                            color="#dc3545"
                            height={280}
                        />
                    </Grid>
                </Grid>

                {/* Tendências e Resumo Mensal */}
                <Grid container spacing={3} mb={4}>
                    {/* Insights de Tendências */}
                    <Grid item xs={12} md={6}>
                        <Card sx={{ height: '100%' }}>
                            <CardHeader title="Análise de Tendências & Insights" titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }} />
                            <CardContent>
                                <Grid container spacing={2} mb={3}>
                                    <Grid item xs={4}>
                                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                                            <Typography variant="subtitle2" color="text.secondary">Rondas</Typography>
                                            <Typography variant="h6" fontWeight="bold" color="primary.main">{metrics.tendencia_rondas}</Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                                            <Typography variant="subtitle2" color="text.secondary">Paradas</Typography>
                                            <Typography variant="h6" fontWeight="bold" color="success.main">{metrics.tendencia_paradas}</Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                                            <Typography variant="subtitle2" color="text.secondary">Ocorrências</Typography>
                                            <Typography variant="h6" fontWeight="bold" color="warning.main">{metrics.tendencia_ocorrencias}</Typography>
                                        </Paper>
                                    </Grid>
                                </Grid>
                                <Divider sx={{ my: 2 }} />
                                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                                    Diretrizes e Insights:
                                </Typography>
                                <Box component="ul" sx={{ pl: 2, m: 0 }}>
                                    <Typography component="li" variant="body2" mb={1} color="text.secondary">
                                        {metrics.proporcao_ocorrencias_por_ronda > 50
                                            ? '🚨 Alta incidência de ocorrências em relação ao volume de rondas realizadas. Reforce as rotas críticas.'
                                            : '✅ Baixa incidência de ocorrências por ronda, indicando bom nível preventivo.'}
                                    </Typography>
                                    {metrics.tendencia_rondas === 'Crescimento' && (
                                        <Typography component="li" variant="body2" mb={1} color="text.secondary">
                                            📈 Rondas apresentaram crescimento consistente nos últimos meses do período analisado.
                                        </Typography>
                                    )}
                                    {metrics.tendencia_paradas === 'Crescimento' && (
                                        <Typography component="li" variant="body2" mb={1} color="text.secondary">
                                            🛑 O volume de paradas operacionais cresceu nos últimos meses. Monitore a eficiência do tempo estacionado.
                                        </Typography>
                                    )}
                                    {metrics.tendencia_ocorrencias === 'Queda' && (
                                        <Typography component="li" variant="body2" mb={1} color="text.secondary">
                                            📉 Redução bem-sucedida do total de ocorrências reportadas, sugerindo maior estabilidade operacional.
                                        </Typography>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Tabela de Resumo Mensal */}
                    <Grid item xs={12} md={6}>
                        <Card sx={{ height: '100%' }}>
                            <CardHeader title="Resumo Mensal Consolidado" titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }} />
                            <CardContent sx={{ p: 0 }}>
                                <TableContainer component={Box} sx={{ maxHeight: 300 }}>
                                    <Table stickyHeader size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Mês</TableCell>
                                                <TableCell align="right">Rondas</TableCell>
                                                <TableCell align="right">Paradas</TableCell>
                                                <TableCell align="right">Ocor.</TableCell>
                                                <TableCell align="right">Prop. Ocor.</TableCell>
                                                <TableCell align="right">Prop. Paradas</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {monthlySummaryList.map((row) => (
                                                <TableRow key={row.mes} hover>
                                                    <TableCell component="th" scope="row" fontWeight="medium">{row.mes}</TableCell>
                                                    <TableCell align="right">{row.rondas}</TableCell>
                                                    <TableCell align="right">{row.paradas}</TableCell>
                                                    <TableCell align="right">{row.ocorrencias}</TableCell>
                                                    <TableCell align="right">{row.proporcaoOcorrencias}</TableCell>
                                                    <TableCell align="right">{row.proporcaoParadas}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Breakdown Detalhado: Condomínios e Supervisores */}
                <Grid container spacing={3}>
                    {/* Top 10 Condomínios */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardHeader title="Top 10 Condomínios (Distribuição Detalhada)" titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }} />
                            <CardContent>
                                <Grid container spacing={2}>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="primary" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <Shield fontSize="small" /> Rondas
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.rondas_por_condominio || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="success.main" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <StopCircle fontSize="small" /> Paradas
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.paradas_por_condominio || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="warning.main" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <WarningAmber fontSize="small" /> Ocorrências
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.ocorrencias_por_condominio || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Top 10 Supervisores */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardHeader title="Top 10 Supervisores (Volume de Atividades)" titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }} />
                            <CardContent>
                                <Grid container spacing={2}>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="primary" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <Shield fontSize="small" /> Rondas
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.rondas_por_supervisor || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="success.main" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <StopCircle fontSize="small" /> Paradas
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.paradas_por_supervisor || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography variant="subtitle2" color="warning.main" fontWeight="bold" mb={1} display="flex" alignItems="center" gap={0.5}>
                                            <WarningAmber fontSize="small" /> Ocorrências
                                        </Typography>
                                        <TableContainer>
                                            <Table size="small">
                                                <TableBody>
                                                    {(breakdown.ocorrencias_por_supervisor || []).map((item: any, idx: number) => (
                                                        <TableRow key={idx}>
                                                            <TableCell sx={{ fontSize: '0.8rem', p: 0.5 }}>{item.name}</TableCell>
                                                            <TableCell align="right" sx={{ fontWeight: 'bold', p: 0.5 }}>{item.value}</TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </TableContainer>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
};

export default DashboardComparativoPage;
