import React, { useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Alert,
    CircularProgress,
    Paper
} from '@mui/material';
import {
    People,
    Business,
    Security,
    Assignment,

    Warning
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchMetrics } from '../../store/slices/adminSlice';
import MetricsCard from '../../components/charts/MetricsCard';
import LoadingSpinner from '../../components/LoadingSpinner';

const MetricsDashboardPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { metrics, loading, error } = useAppSelector((state) => state.admin);

    useEffect(() => {
        dispatch(fetchMetrics());
    }, [dispatch]);

    if (loading) {
        return <LoadingSpinner />;
    }

    if (error) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            </Container>
        );
    }

    if (!metrics) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                <Alert severity="info">
                    Nenhum dado disponível
                </Alert>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box mb={4}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Dashboard de Métricas Gerais
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Visão geral do sistema com estatísticas principais
                </Typography>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3 }}>
                {/* Total de Usuários */}
                <MetricsCard
                    title="Total de Usuários"
                    value={metrics.total_usuarios}
                    subtitle="Usuários registrados no sistema"
                    icon={<People />}
                    color="primary"
                />

                {/* Usuários Pendentes */}
                <MetricsCard
                    title="Usuários Pendentes"
                    value={metrics.usuarios_pendentes}
                    subtitle="Aguardando aprovação"
                    icon={<Warning />}
                    color="warning"
                />

                {/* Total de Condomínios */}
                <MetricsCard
                    title="Condomínios"
                    value={metrics.total_condominios}
                    subtitle="Condomínios cadastrados"
                    icon={<Business />}
                    color="info"
                />

                {/* Total de Tipos de Ocorrência */}
                <MetricsCard
                    title="Tipos de Ocorrência"
                    value={metrics.total_tipos_ocorrencia}
                    subtitle="Categorias de ocorrências"
                    icon={<Security />}
                    color="secondary"
                />

                {/* Total de Colaboradores */}
                <MetricsCard
                    title="Colaboradores"
                    value={metrics.total_colaboradores}
                    subtitle="Funcionários cadastrados"
                    icon={<Assignment />}
                    color="success"
                />
            </Box>

            {/* Resumo Executivo */}
            <Paper sx={{ p: 3, mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                    Resumo Executivo
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" color="primary" gutterBottom>
                            Sistema Ativo
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            O sistema possui {metrics.total_usuarios} usuários registrados,
                            sendo {metrics.usuarios_pendentes} aguardando aprovação.
                            Há {metrics.total_condominios} condomínios cadastrados e
                            {metrics.total_colaboradores} colaboradores no sistema.
                        </Typography>
                    </Box>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" color="primary" gutterBottom>
                            Configuração
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            O sistema está configurado com {metrics.total_tipos_ocorrencia}
                            tipos diferentes de ocorrências para categorização adequada
                            dos incidentes reportados.
                        </Typography>
                    </Box>
                </Box>
            </Paper>

            {/* Estatísticas de Aprovação */}
            <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Estatísticas de Aprovação
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                    <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CircularProgress
                            variant="determinate"
                            value={((metrics.total_usuarios - metrics.usuarios_pendentes) / metrics.total_usuarios) * 100}
                            size={60}
                            color="success"
                        />
                        <Box>
                            <Typography variant="h6">
                                {((metrics.total_usuarios - metrics.usuarios_pendentes) / metrics.total_usuarios * 100).toFixed(1)}%
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Taxa de aprovação
                            </Typography>
                        </Box>
                    </Box>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Usuários aprovados: {metrics.total_usuarios - metrics.usuarios_pendentes}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Usuários pendentes: {metrics.usuarios_pendentes}
                        </Typography>
                    </Box>
                </Box>
            </Paper>
        </Container>
    );
};

export default MetricsDashboardPage; 